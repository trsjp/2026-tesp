#!/usr/bin/env bash
# Build the Docker image for the TESP Robot Basketball workspace.
# Run from the repository root: bash scripts/docker_build.sh
set -e

cd "$(dirname "$0")/.."

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker is not installed or not on PATH."
    echo "Install Docker: https://docs.docker.com/engine/install/"
    exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
    echo "ERROR: 'docker compose' is not available."
    echo "Install the Docker Compose plugin: https://docs.docker.com/compose/install/"
    exit 1
fi

# Build the container's "ros" user with the current host user's UID/GID so
# files created inside the container (colcon build output, cloned repos)
# stay owned by you on the host instead of a foreign UID. See
# docs/docker_workflow.md for details.
export USER_UID
export USER_GID
USER_UID="$(id -u)"
USER_GID="$(id -g)"
echo "Building for host UID:GID = ${USER_UID}:${USER_GID}"

echo "Building Docker image (service: robot-basketball)..."
docker compose build

echo "Done. Next: bash scripts/clone_repos.sh, then bash scripts/docker_shell.sh"
