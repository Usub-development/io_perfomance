#!/usr/bin/env bash
set -euo pipefail
echo "bin,threads,conn,port,rps,p50,p90,p99,p999" > results/summary.csv
for f in results/*.txt; do
  bin=$(basename "$f" | cut -d_ -f1-2 | sed 's/_$//')
  threads=$(grep -oE '_t[0-9]+'    <<<"$f" | tr -dc 0-9)
  conn=$(   grep -oE '_c[0-9]+'    <<<"$f" | tr -dc 0-9)
  port=$(   grep -oE '_p[0-9]+'    <<<"$f" | tr -dc 0-9)
  rps=$(grep -E '^Requests/sec:' "$f" | awk '{print $2}')
  p50=$(grep -A3 '^  Latency Distribution' "$f" | sed -n '2p' | awk '{print $2}')
  p90=$(grep -A3 '^  Latency Distribution' "$f" | sed -n '4p' | awk '{print $2}')
  p99=$(grep -A3 '^  Latency Distribution' "$f" | sed -n '5p' | awk '{print $2}')
  p999=$(grep -A4 '^  Latency Distribution' "$f" | sed -n '6p' | awk '{print $2}')
  echo "$bin,$threads,$conn,$port,$rps,$p50,$p90,$p99,$p999" >> results/summary.csv
done
echo "Wrote results/summary.csv"