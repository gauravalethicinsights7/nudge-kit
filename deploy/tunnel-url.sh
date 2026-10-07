#!/usr/bin/env bash
# Prints the current quick-tunnel public URL.
#
# Quick tunnels get a fresh random hostname every time the cloudflared
# container restarts, so this reads it back out of the connector's own logs
# rather than storing it anywhere.
#
#   bash deploy/tunnel-url.sh
set -euo pipefail

COMPOSE="docker compose -f $(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/deploy/docker-compose.prod.yml"

url=$($COMPOSE logs cloudflared 2>/dev/null \
  | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' \
  | tail -1 || true)

if [ -z "$url" ]; then
  echo "No quick-tunnel URL found yet." >&2
  echo "The connector may still be starting, or you're on a named tunnel." >&2
  echo "Check with: $COMPOSE logs cloudflared" >&2
  exit 1
fi

echo "$url"
