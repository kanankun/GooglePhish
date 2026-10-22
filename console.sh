#!/usr/bin/env bash
#
# console.sh - open the private data console on your own machine without
# publishing any port on the server. Run this FROM YOUR LAPTOP.
#
#   ./console.sh root@your-server
#
# It finds the c2 container's internal IP on the server and tunnels
# localhost:8001 straight to it over SSH. Nothing is exposed on the
# server beyond 80/443. Close it with Ctrl-C.

set -euo pipefail

SERVER="${1:?usage: ./console.sh <user>@<server>}"
LOCAL_PORT="${2:-8001}"

echo "Looking up the console container on ${SERVER}..."
IP="$(ssh "$SERVER" "docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' week1-c2")"

[ -n "$IP" ] || { echo "Could not find the week1-c2 container. Is the stack up?" >&2; exit 1; }

echo "Console will be at  http://localhost:${LOCAL_PORT}/gate"
echo "(Ctrl-C to close the tunnel.)"
exec ssh -N -L "${LOCAL_PORT}:${IP}:8000" "$SERVER"
