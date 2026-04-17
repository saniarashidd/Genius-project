# Moment Event Contract

```json
{
  "event_id": "uuid",
  "event_time": "2026-04-01T20:15:13Z",
  "ingest_time": "2026-04-01T20:15:14Z",
  "league": "NBA",
  "game_id": "game_123",
  "team_id": "team_7",
  "player_id": "player_42",
  "moment_type": "lead_change",
  "importance_score": 0.91,
  "metadata": {
    "clock": "01:22",
    "period": 4,
    "home_score": 101,
    "away_score": 100
  }
}
```

## Required Fields

- `event_id`, `event_time`, `league`, `game_id`, `moment_type`

## Allowed `moment_type` Values

- `goal`
- `lead_change`
- `timeout`
- `clutch_play`
- `milestone`

## Compatibility Rule

Any breaking schema change must update:

1. `libs/event-schema/moment-event.schema.json`
2. `libs/event-schema/moment-event.zod.ts`
3. Rust struct in `apps/consumer-rust/src/moment.rs`
