# Moments Pipeline Simulator

Starter project that mirrors an adtech "moments package" pipeline using:

- TypeScript API + producer
- Apache Pulsar for ingestion
- Rust consumer for scoring and trigger decisions
- MySQL for storage and analytics

## Project Structure

- `apps/api-ts`: API for ingesting and querying moments
- `apps/producer-ts`: script that publishes simulated game moments
- `apps/consumer-rust`: consumer that validates, deduplicates, scores, and persists moments
- `libs/event-schema`: shared moment event contract
- `sql`: schema and indexes
- `dashboards/queries`: starter analytics queries
- `docs`: architecture and backlog

## Quick Start

### One-command local start (recommended)

From `moments-pipeline-sim/`:

```bash
./scripts/dev-up.sh
```

What this script does:
- starts Pulsar + MySQL via Docker Compose
- initializes MySQL schema
- installs Node dependencies (API + producer)
- installs a local `protoc` binary (if missing)
- creates/reuses tmux sessions for:
  - `moments-api`
  - `moments-consumer`
  - `moments-producer`

Useful follow-ups:

```bash
tmux -f /exec-daemon/tmux.portal.conf ls
tmux -f /exec-daemon/tmux.portal.conf attach-session -t moments-api
tmux -f /exec-daemon/tmux.portal.conf attach-session -t moments-consumer
tmux -f /exec-daemon/tmux.portal.conf attach-session -t moments-producer
```

Stop everything:

```bash
./scripts/dev-down.sh
```

Verify:

```bash
curl "http://127.0.0.1:3000/healthz"
curl "http://127.0.0.1:3000/moments/recent?limit=10"
curl "http://127.0.0.1:3000/campaigns/campaign_demo_1/triggers?from=2026-01-01T00:00:00.000Z&to=2030-01-01T00:00:00.000Z"
```

---

1. Copy environment defaults:

   ```bash
   cp .env.example .env
   ```

2. Start local services:

   ```bash
   docker compose up -d
   ```

3. Initialize database schema:

   ```bash
   docker compose exec mysql mysql -uroot -proot moments < /workspace/moments-pipeline-sim/sql/001_init.sql
   docker compose exec mysql mysql -uroot -proot moments < /workspace/moments-pipeline-sim/sql/002_indexes.sql
   ```

4. Install Node dependencies:

   ```bash
   cd apps/api-ts && npm install
   cd ../producer-ts && npm install
   cd ../../
   ```

5. Start the API in one shell:

   ```bash
   cd apps/api-ts
   npm run dev
   ```

6. In another shell, install and export `protoc` once (required by Pulsar Rust crate):

   ```bash
   PROTOC_BIN="$(./scripts/setup-protoc.sh)"
   export PROTOC="$PROTOC_BIN"
   export OPENSSL_STATIC=1
   ```

7. In that same shell, run the Rust consumer:

   ```bash
   cd apps/consumer-rust
   cargo run
   ```

8. Publish simulated events in another shell:

   ```bash
   cd apps/producer-ts
   npm start
   ```

9. Verify pipeline output from API:

   ```bash
   curl "http://127.0.0.1:3000/moments/recent?limit=10"
   curl "http://127.0.0.1:3000/campaigns/campaign_demo_1/triggers?from=2026-01-01T00:00:00.000Z&to=2030-01-01T00:00:00.000Z"
   ```

## What works end-to-end now

- API accepts `POST /moments/ingest` and publishes to Pulsar `TOPIC_MOMENTS_RAW`.
- Rust consumer subscribes to `TOPIC_MOMENTS_RAW` and:
  - validates/deserializes payloads
  - deduplicates by `event_id` (in-memory cache)
  - computes score + trigger decision
  - writes to MySQL (`moments_raw`, `moments_scored`, `ad_triggers`)
  - records failures in `consumer_errors`
  - publishes error payloads to `TOPIC_MOMENTS_DLQ`
  - publishes scored payloads to `TOPIC_MOMENTS_SCORED`

## Notes

- This is a starter scaffold intended for interview/internship prep.
- Replace stub scoring and campaign logic with production-style rule/ML pipelines as you iterate.
