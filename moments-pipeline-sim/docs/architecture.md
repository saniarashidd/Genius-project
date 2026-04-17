# Architecture

## Goal

Simulate a live sports "moments" pipeline that converts in-game events into ad trigger decisions.

## Data Flow

1. Producer/API emits `moment_event` to `moments.raw`.
2. Rust consumer reads from `moments.raw`.
3. Consumer validates + deduplicates + scores event importance.
4. Consumer stores records in MySQL and optional trigger decision.
5. Consumer publishes accepted results to `moments.scored`.
6. Invalid events are sent to `moments.dlq`.

## Services

- **api-ts**: HTTP ingest + query endpoints.
- **producer-ts**: local simulator for in-game events.
- **consumer-rust**: reliability and decisioning core.
- **MySQL**: source of truth for moments and triggers.
- **Pulsar**: event transport and replay backbone.

## Non-Functional Targets (Starter)

- End-to-end processing p95 under 3 seconds.
- Idempotent ingest using `event_id`.
- Clear error capture for malformed and out-of-window events.
