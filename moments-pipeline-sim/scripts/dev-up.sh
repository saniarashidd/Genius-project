#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

API_SESSION="moments-sim-api"
CONSUMER_SESSION="moments-sim-consumer"
PRODUCER_SESSION="moments-sim-producer"

usage() {
  cat <<'USAGE'
Usage: ./scripts/dev-up.sh [--skip-producer] [--no-install]

Boots the local Moments Pipeline simulator:
1) starts Pulsar + MySQL via docker compose
2) initializes MySQL schema
3) installs JS dependencies (unless --no-install)
4) starts API, Rust consumer, and producer in tmux sessions

Flags:
  --skip-producer   Start only API + Rust consumer.
  --no-install      Skip npm install steps.
  -h, --help        Show this help.
USAGE
}

SKIP_PRODUCER=0
SKIP_INSTALL=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-producer)
      SKIP_PRODUCER=1
      ;;
    --no-install)
      SKIP_INSTALL=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_cmd docker
require_cmd tmux
require_cmd npm
require_cmd cargo
require_cmd curl
require_cmd python3

cd "$ROOT_DIR"

if [[ ! -f "$ROOT_DIR/.env" ]]; then
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
fi

echo "Starting docker services..."
docker compose up -d

echo "Initializing MySQL schema..."
docker compose exec -T mysql mysql -uroot -proot moments < "$ROOT_DIR/sql/001_init.sql"
docker compose exec -T mysql mysql -uroot -proot moments < "$ROOT_DIR/sql/002_indexes.sql"

if [[ "$SKIP_INSTALL" -eq 0 ]]; then
  echo "Installing Node dependencies..."
  (cd "$ROOT_DIR/apps/api-ts" && npm install)
  (cd "$ROOT_DIR/apps/producer-ts" && npm install)
fi

PROTOC_BIN="$("$ROOT_DIR/scripts/setup-protoc.sh")"

start_or_restart_session() {
  local session="$1"
  local cmd="$2"
  if tmux has-session -t "=${session}" 2>/dev/null; then
    tmux respawn-pane -k -t "${session}:0.0" "$cmd"
  else
    tmux new-session -d -s "$session" -c "$ROOT_DIR" "$cmd"
  fi
}

API_CMD="cd \"$ROOT_DIR/apps/api-ts\" && npm run dev"
CONSUMER_CMD="cd \"$ROOT_DIR/apps/consumer-rust\" && PROTOC=\"$PROTOC_BIN\" OPENSSL_STATIC=1 cargo run"
PRODUCER_CMD="cd \"$ROOT_DIR/apps/producer-ts\" && npm start"

echo "Starting API and Rust consumer in tmux..."
start_or_restart_session "$API_SESSION" "$API_CMD"
start_or_restart_session "$CONSUMER_SESSION" "$CONSUMER_CMD"

if [[ "$SKIP_PRODUCER" -eq 0 ]]; then
  echo "Starting producer in tmux..."
  start_or_restart_session "$PRODUCER_SESSION" "$PRODUCER_CMD"
fi

echo
echo "Started sessions:"
tmux ls | rg "^moments-sim-" || true
echo
echo "Attach examples:"
echo "  tmux attach -t $API_SESSION"
echo "  tmux attach -t $CONSUMER_SESSION"
if [[ "$SKIP_PRODUCER" -eq 0 ]]; then
  echo "  tmux attach -t $PRODUCER_SESSION"
fi
echo
echo "Quick health check:"
echo "  curl http://127.0.0.1:3000/healthz"
