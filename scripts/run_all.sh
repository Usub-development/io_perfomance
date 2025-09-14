#!/usr/bin/env bash
set -euo pipefail

HOST=${HOST:-127.0.0.1}
BASE_PORT=${PORT:-45900}
THREADS_LIST="${THREADS_LIST:-1 2 4 8}"
CONN=${CONN:-1000}
DUR=${DUR:-30s}
WARMUP=${WARMUP:-0s}
REUSE=${REUSE:-0}

DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RUN_ONE="$DIR/run_one.sh"

BINS=( "./build/echo_uvent" "./build/echo_asio" "./build/echo_libuv" )

i=0
for BIN in "${BINS[@]}"; do
  [[ -x "$BIN" ]] || { echo "skip $BIN"; continue; }
  for T in $THREADS_LIST; do
    PORT=$((BASE_PORT + i))
    THREADS=$T CONN=$CONN DUR=$DUR WARMUP=$WARMUP REUSE=$REUSE HOST=$HOST PORT=$PORT \
      "$RUN_ONE" "$BIN"
    i=$((i+1))
    sleep 1
  done
done