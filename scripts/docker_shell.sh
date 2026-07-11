#!/usr/bin/env bash
# Start an interactive shell in a disposable container.
#
# `docker compose run --rm` creates a *new* container each time and removes
# it on exit. This is intentional and safe: the repository is mounted from
# the host (see docker-compose.yml), so nothing you edit inside
# /workspace is lost when the container is removed. Only state that lives
# outside /workspace (e.g. packages installed manually inside the
# container) will not persist between runs.
#
# Run from the repository root: bash scripts/docker_shell.sh
set -e

cd "$(dirname "$0")/.."

docker compose run --rm robot-basketball bash
