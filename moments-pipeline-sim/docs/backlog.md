# Starter Backlog

## Phase 1: Foundation

- [ ] Boot local stack with Pulsar and MySQL.
- [ ] Wire API ingest endpoint to publish raw events.
- [ ] Implement Rust consumer happy-path flow.

## Phase 2: Reliability

- [ ] Idempotency check (`event_id`) in MySQL.
- [ ] Retry and dead-letter handling for invalid payloads.
- [ ] Lag and error metrics from consumer loop.

## Phase 3: Product Signal

- [ ] Add campaign rule table and trigger threshold logic.
- [ ] Support per-league/per-moment-type weighting.
- [ ] Add SQL dashboards for trigger and dedupe analysis.

## Phase 4: Experimentation

- [ ] A/B test baseline trigger threshold vs adaptive threshold.
- [ ] Add reporting endpoint for "triggered vs not triggered."
