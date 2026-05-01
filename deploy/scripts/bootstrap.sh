#!/usr/bin/env bash
set -euo pipefail

echo "[AUTOQA] Preparing host for deployment"
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker

echo "[AUTOQA] Ensure NVIDIA Container Toolkit is installed for GPU workloads"
echo "[AUTOQA] Run: docker compose --env-file .env up -d --build"
