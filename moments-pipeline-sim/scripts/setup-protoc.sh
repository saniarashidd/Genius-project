#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BIN_DIR="$ROOT_DIR/.bin"
PROTOC_DIR="$BIN_DIR/protoc"
PROTOC_BIN="$PROTOC_DIR/bin/protoc"
PROTOC_VERSION="${PROTOC_VERSION:-27.5}"

if [ -x "$PROTOC_BIN" ]; then
  echo "$PROTOC_BIN"
  exit 0
fi

mkdir -p "$BIN_DIR"
ZIP_PATH="$BIN_DIR/protoc-${PROTOC_VERSION}.zip"
URL="https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOC_VERSION}/protoc-${PROTOC_VERSION}-linux-x86_64.zip"

echo "Downloading protoc ${PROTOC_VERSION}..."
curl -fsSL "$URL" -o "$ZIP_PATH"
export ZIP_PATH PROTOC_DIR
python3 - <<'PY'
import os
import zipfile

zip_path = os.environ["ZIP_PATH"]
target = os.environ["PROTOC_DIR"]
os.makedirs(target, exist_ok=True)
with zipfile.ZipFile(zip_path) as zf:
    zf.extractall(target)
PY
chmod +x "$PROTOC_BIN"

echo "$PROTOC_BIN"
