#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

API_SESSION="moments-sim-api"
CONSUMER_SESSION="moments-sim-consumer"
PRODUCER_SESSION="moments-sim-producer"

usage() {
  cat <<'USAGE'
Usage: ./scripts/dev-down.sh [--keep-docker]

Stops local Moments Pipeline simulator processes:
- kills tmux sessions started by dev-up.sh
- brings Docker Compose services down (unless --keep-docker)

Flags:
  --keep-docker    Keep Pulsar/MySQL containers running.
  -h, --help       Show this help.
USAGE
}

KEEP_DOCKER=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep-docker)
      KEEP_DOCKER=1
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

kill_session_if_exists() {
  local session="$1"
  if tmux has-session -t "=${session}" 2>/dev/null; then
    tmux kill-session -t "$session"
    echo "Stopped tmux session: $session"
  fi
}

kill_session_if_exists "$API_SESSION"
kill_session_if_exists "$CONSUMER_SESSION"
kill_session_if_exists "$PRODUCER_SESSION"

if [[ "$KEEP_DOCKER" -eq 0 ]]; then
  if command -v docker >/dev/null 2>&1; then
    echo "Stopping Docker services..."
    docker compose -f "$ROOT_DIR/docker-compose.yml" down
  else
    echo "docker command not found; skipped docker compose down"
  fi
fi

echo "Done."
