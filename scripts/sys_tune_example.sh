#!/usr/bin/env bash
set -euo pipefail
sudo sysctl -w net.core.somaxconn=65535
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=262144
sudo sysctl -w net.core.netdev_max_backlog=250000
sudo sysctl -w net.ipv4.tcp_fin_timeout=10
sudo sysctl -w net.ipv4.tcp_tw_reuse=1
ulimit -n 1048576