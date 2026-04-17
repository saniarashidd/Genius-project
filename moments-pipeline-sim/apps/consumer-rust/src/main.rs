mod dedupe;
mod moment;
mod mysql_repo;
mod scoring;

use anyhow::{Context, Result};
use dotenvy::dotenv;
use futures::TryStreamExt;
use pulsar::{
    producer::Message as PulsarMessage, Consumer, DeserializeMessage, Error as PulsarError,
    Payload, Producer, Pulsar, SerializeMessage, SubType, TokioExecutor,
};
use serde::{Deserialize, Serialize};
use std::env;

use crate::dedupe::DedupeCache;
use crate::moment::MomentEvent;
use crate::mysql_repo::MysqlRepo;
use crate::scoring::{score_moment, should_trigger};

fn build_mysql_url() -> String {
    let user = env::var("MYSQL_USER").unwrap_or_else(|_| "root".to_string());
    let pass = env::var("MYSQL_PASSWORD").unwrap_or_else(|_| "root".to_string());
    let host = env::var("MYSQL_HOST").unwrap_or_else(|_| "127.0.0.1".to_string());
    let port = env::var("MYSQL_PORT").unwrap_or_else(|_| "3306".to_string());
    let db = env::var("MYSQL_DATABASE").unwrap_or_else(|_| "moments".to_string());
    format!("mysql://{}:{}@{}:{}/{}", user, pass, host, port, db)
}

fn parse_event(payload: &str) -> Result<MomentEvent> {
    let event: MomentEvent =
        serde_json::from_str(payload).context("failed to deserialize moment event payload")?;
    Ok(event)
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct RawJson {
    data: String,
}

impl DeserializeMessage for RawJson {
    type Output = Result<RawJson, PulsarError>;

    fn deserialize_message(payload: &Payload) -> Self::Output {
        let data = String::from_utf8(payload.data.clone())
            .map_err(|err| PulsarError::Custom(err.to_string()))?;
        Ok(RawJson { data })
    }
}

impl SerializeMessage for RawJson {
    fn serialize_message(input: Self) -> Result<PulsarMessage, PulsarError> {
        Ok(PulsarMessage {
            payload: input.data.into_bytes(),
            ..Default::default()
        })
    }
}

fn env_var_or_default(key: &str, default: &str) -> String {
    env::var(key).unwrap_or_else(|_| default.to_string())
}

async fn build_pulsar_client() -> Result<Pulsar<TokioExecutor>> {
    let url = env_var_or_default("PULSAR_URL", "pulsar://127.0.0.1:6650");
    let client: Pulsar<_> = Pulsar::builder(url, TokioExecutor)
        .build()
        .await
        .context("failed to connect to pulsar")?;
    Ok(client)
}

async fn build_raw_consumer(
    client: &Pulsar<TokioExecutor>,
) -> Result<Consumer<RawJson, TokioExecutor>> {
    let topic = env_var_or_default("TOPIC_MOMENTS_RAW", "persistent://public/default/moments.raw");
    let subscription = env_var_or_default("PULSAR_SUBSCRIPTION", "moment-scorer-subscription");
    let consumer_name = env_var_or_default("PULSAR_CONSUMER_NAME", "moment-scorer-v1");

    let consumer = client
        .consumer()
        .with_topic(topic)
        .with_subscription_type(SubType::KeyShared)
        .with_subscription(subscription)
        .with_consumer_name(consumer_name)
        .build()
        .await
        .context("failed to create raw moments consumer")?;
    Ok(consumer)
}

async fn build_producer(
    client: &Pulsar<TokioExecutor>,
    env_key: &str,
    default_topic: &str,
    name: &str,
) -> Result<Producer<TokioExecutor>> {
    let topic = env_var_or_default(env_key, default_topic);
    let producer = client
        .producer()
        .with_topic(topic)
        .with_name(name)
        .build()
        .await
        .with_context(|| format!("failed to create producer {}", name))?;
    Ok(producer)
}

async fn publish_json(
    producer: &mut Producer<TokioExecutor>,
    value: &serde_json::Value,
) -> Result<()> {
    let data = serde_json::to_string(value).context("failed to serialize payload for publish")?;
    producer
        .send(RawJson { data })
        .await
        .context("failed to enqueue publish message")?
        .await
        .map_err(|e| anyhow::anyhow!("failed to publish message: {}", e))?;
    Ok(())
}

fn extract_event_id(payload: &str) -> Option<String> {
    let parsed: serde_json::Value = serde_json::from_str(payload).ok()?;
    parsed.get("event_id")?.as_str().map(|s| s.to_string())
}

fn normalize_payload_value(payload: &str) -> serde_json::Value {
    serde_json::from_str::<serde_json::Value>(payload)
        .unwrap_or_else(|_| serde_json::json!({ "raw": payload }))
}

async fn process_event(
    repo: &MysqlRepo,
    scored_producer: &mut Producer<TokioExecutor>,
    event: &MomentEvent,
) -> Result<()> {
    repo.insert_raw_moment(event)?;

    let score = score_moment(event);
    let accepted = should_trigger(score);
    let reason = if accepted {
        "score_above_threshold"
    } else {
        "score_below_threshold"
    };

    repo.insert_scored(&event.event_id, score, accepted, reason)?;
    repo.insert_trigger(&event.event_id, "campaign_demo_1", accepted, reason)?;

    let scored_payload = serde_json::json!({
        "event_id": event.event_id,
        "game_id": event.game_id,
        "moment_type": event.moment_type,
        "score": score,
        "accepted": accepted,
        "reason": reason,
        "processed_at": chrono::Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Millis, true)
    });
    publish_json(scored_producer, &scored_payload).await?;

    Ok(())
}

#[tokio::main]
async fn main() -> Result<()> {
    dotenv().ok();

    let mysql_url = build_mysql_url();
    let repo = MysqlRepo::new(&mysql_url).context("failed to initialize mysql repo")?;
    let mut dedupe = DedupeCache::new();

    let pulsar = build_pulsar_client().await?;
    let mut consumer = build_raw_consumer(&pulsar).await?;
    let mut scored_producer = build_producer(
        &pulsar,
        "TOPIC_MOMENTS_SCORED",
        "persistent://public/default/moments.scored",
        "moment-scorer-scored-producer",
    )
    .await?;
    let mut dlq_producer = build_producer(
        &pulsar,
        "TOPIC_MOMENTS_DLQ",
        "persistent://public/default/moments.dlq",
        "moment-scorer-dlq-producer",
    )
    .await?;

    println!("moment consumer started and waiting for messages...");

    while let Some(msg) = consumer.try_next().await.context("consumer stream failed")? {
        let payload = match msg.deserialize() {
            Ok(raw) => raw.data,
            Err(err) => {
                let details = format!("failed to decode message payload: {}", err);
                if let Err(db_err) =
                    repo.insert_consumer_error(None, "deserialization_error", None, &details)
                {
                    eprintln!("failed to persist consumer error: {}", db_err);
                }
                consumer.ack(&msg).await.context("ack after decode failure failed")?;
                continue;
            }
        };

        let event_id_for_error = extract_event_id(&payload);
        let payload_value = normalize_payload_value(&payload);
        let payload_json = serde_json::to_string(&payload_value)
            .context("failed to serialize payload json for error recording")?;

        let event = match parse_event(&payload) {
            Ok(event) => event,
            Err(err) => {
                let details = format!("invalid moment payload: {}", err);
                if let Err(db_err) = repo.insert_consumer_error(
                    event_id_for_error.as_deref(),
                    "validation_error",
                    Some(&payload_json),
                    &details,
                ) {
                    eprintln!("failed to persist validation error: {}", db_err);
                }
                let dlq_payload = serde_json::json!({
                    "event_id": event_id_for_error,
                    "error_type": "validation_error",
                    "details": details,
                    "raw_payload": payload_value
                });
                match publish_json(&mut dlq_producer, &dlq_payload).await {
                    Ok(()) => {
                        consumer
                            .ack(&msg)
                            .await
                            .context("ack after validation failure failed")?;
                    }
                    Err(publish_err) => {
                        eprintln!("failed to publish validation error to DLQ: {}", publish_err);
                        consumer
                            .nack(&msg)
                            .await
                            .context("nack after validation DLQ failure failed")?;
                    }
                }
                continue;
            }
        };

        if dedupe.has_seen(&event.event_id) {
            println!("duplicate event skipped: {}", event.event_id);
            consumer
                .ack(&msg)
                .await
                .context("ack after duplicate skip failed")?;
            continue;
        }

        match process_event(&repo, &mut scored_producer, &event).await {
            Ok(()) => {
                dedupe.mark_seen(&event.event_id);
                consumer.ack(&msg).await.context("ack after processing failed")?;
                println!(
                    "processed event_id={}, moment_type={}, league={}",
                    event.event_id, event.moment_type, event.league
                );
            }
            Err(err) => {
                let details = format!("processing_error: {}", err);
                if let Err(db_err) = repo.insert_consumer_error(
                    Some(&event.event_id),
                    "processing_error",
                    Some(&payload_json),
                    &details,
                ) {
                    eprintln!("failed to persist processing error: {}", db_err);
                }

                consumer
                    .nack(&msg)
                    .await
                    .context("nack after processing failure failed")?;
            }
        }
    }

    Ok(())
}
