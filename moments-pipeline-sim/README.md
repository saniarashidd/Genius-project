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

4. Start the TypeScript API and producer, then run the Rust consumer.

## Notes

- This is a starter scaffold intended for interview/internship prep.
- Replace stub logic with real campaign rules, scoring, and metrics as you iterate.
