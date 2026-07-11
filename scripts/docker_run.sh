#!/usr/bin/env bash
# Start a long-running container for the workspace.
#
# Unlike docker_shell.sh (which creates a disposable container per run),
# this keeps a single container running so it can be attached from
# multiple terminals, e.g. with:
#   docker compose exec robot-basketball bash
#
# Run from the repository root: bash scripts/docker_run.sh
set -e

cd "$(dirname "$0")/.."

docker compose up
