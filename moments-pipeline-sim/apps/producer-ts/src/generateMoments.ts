import "dotenv/config";
import Pulsar from "pulsar-client";
import { randomUUID } from "node:crypto";

const topic = process.env.TOPIC_MOMENTS_RAW ?? "persistent://public/default/moments.raw";

const client = new Pulsar.Client({
  serviceUrl: process.env.PULSAR_URL ?? "pulsar://127.0.0.1:6650"
});

const producer = await client.createProducer({ topic });

const momentTypes = ["goal", "lead_change", "timeout", "clutch_play", "milestone"] as const;
const leagues = ["NBA", "NFL", "NCAA"];

function randomFrom<T>(arr: readonly T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]!;
}

for (let i = 0; i < 20; i += 1) {
  const event = {
    event_id: randomUUID(),
    event_time: new Date().toISOString(),
    ingest_time: new Date().toISOString(),
    league: randomFrom(leagues),
    game_id: `game_${100 + (i % 5)}`,
    team_id: `team_${1 + (i % 10)}`,
    player_id: `player_${10 + (i % 30)}`,
    moment_type: randomFrom(momentTypes),
    importance_score: Number(Math.random().toFixed(4)),
    metadata: {
      period: 1 + (i % 4),
      clock: "01:22",
      home_score: 85 + i,
      away_score: 83 + i
    }
  };

  await producer.send({
    data: Buffer.from(JSON.stringify(event)),
    partitionKey: `${event.game_id}:${event.moment_type}`
  });
  // Keep logs simple so this can run as a one-off local simulator.
  console.log(`published ${event.event_id} (${event.moment_type})`);
}

await producer.close();
await client.close();
