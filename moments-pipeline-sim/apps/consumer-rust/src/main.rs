mod dedupe;
mod moment;
mod mysql_repo;
mod scoring;

use anyhow::{Context, Result};
use dotenvy::dotenv;
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

#[tokio::main]
async fn main() -> Result<()> {
    dotenv().ok();

    let mysql_url = build_mysql_url();
    let repo = MysqlRepo::new(&mysql_url)?;
    let mut dedupe = DedupeCache::new();

    // TODO: Replace this vector with a real Pulsar consumer loop.
    let sample_payloads = vec![
        r#"{"event_id":"demo-evt-1","event_time":"2026-04-01T20:15:13Z","league":"NBA","game_id":"game_123","team_id":"team_7","player_id":"player_42","moment_type":"lead_change","importance_score":0.71,"metadata":{"period":4,"clock":"01:22","home_score":101,"away_score":100}}"#,
        r#"{"event_id":"demo-evt-2","event_time":"2026-04-01T20:16:10Z","league":"NBA","game_id":"game_123","team_id":"team_7","player_id":"player_99","moment_type":"timeout","importance_score":0.32,"metadata":{"period":4,"clock":"00:44","home_score":103,"away_score":102}}"#
    ];

    for payload in sample_payloads {
        let event = parse_event(payload)?;
        if dedupe.is_duplicate(&event.event_id) {
            println!("duplicate event skipped: {}", event.event_id);
            continue;
        }

        repo.insert_raw_moment(&event)?;
        let score = score_moment(&event);
        let accepted = should_trigger(score);
        let reason = if accepted { "score_above_threshold" } else { "score_below_threshold" };
        repo.insert_scored(&event.event_id, score, accepted, reason)?;
        repo.insert_trigger(&event.event_id, "campaign_demo_1", accepted, reason)?;

        println!(
            "processed event_id={}, score={:.3}, accepted={}",
            event.event_id, score, accepted
        );
    }

    Ok(())
}
