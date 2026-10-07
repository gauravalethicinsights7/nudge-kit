#!/usr/bin/env bash
# One-time provisioning for a fresh Oracle Cloud Always Free VM (Ubuntu 22.04+,
# Ampere A1 / arm64). Run it on the VM, not on your laptop:
#
#   ssh ubuntu@<vm-public-ip>
#   git clone <your-repo-url> nudge-kit && cd nudge-kit
#   bash deploy/setup-oracle.sh
#
# Installs Docker, adds swap, and starts the stack. Re-running it is safe.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> Installing Docker Engine + compose plugin"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER"
  echo "    Added $USER to the docker group — log out and back in for it to apply."
fi

# PyMC's first-use C compilation and the uv dependency resolve are the two
# memory spikes here. The Ampere A1 shape has plenty of RAM, but swap keeps a
# smaller shape (or a parallel docker build) from being OOM-killed mid-build.
echo "==> Ensuring 4G swap exists"
if [ ! -f /swapfile ]; then
  sudo fallocate -l 4G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

# Oracle's Ubuntu images ship iptables rules that drop almost everything
# inbound. We deliberately do NOT open a port: cloudflared makes an *outbound*
# connection, so the API is reachable through Cloudflare without the VM ever
# accepting inbound traffic. Nothing to configure here — noted so the closed
# firewall doesn't look like a mistake later.
echo "==> Firewall left closed (cloudflared dials out; no inbound port needed)"

if [ ! -f deploy/.env ]; then
  cp deploy/.env.example deploy/.env
  echo
  echo "!!  deploy/.env was just created from the example."
  echo "!!  Fill it in (tunnel token, API keys, passwords), then re-run this script:"
  echo "!!      nano deploy/.env && bash deploy/setup-oracle.sh"
  exit 1
fi

echo "==> Building and starting the stack (first build takes 10-20 min on arm64)"
sudo docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env up -d --build

echo
echo "==> Done. Useful commands:"
echo "    sudo docker compose -f deploy/docker-compose.prod.yml logs -f api"
echo "    sudo docker compose -f deploy/docker-compose.prod.yml ps"
echo "    sudo docker compose -f deploy/docker-compose.prod.yml up -d --build   # redeploy"
