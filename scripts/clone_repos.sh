#!/usr/bin/env bash
# Clone external robot repositories into ros2_ws/src.
#
# The URLs below are placeholders. Confirm the official upstream URLs with
# the instructor (see docs/repository_sources.md) and fill them in before
# running this script for real.
#
# Run from the repository root: bash scripts/clone_repos.sh
set -e

cd "$(dirname "$0")/.."

SRC_DIR="ros2_ws/src"
mkdir -p "$SRC_DIR"

# TODO: replace with the confirmed upstream repository URLs.
ICART_MINI_REPO_URL="TODO"
OPENXARM_REPO_URL="TODO"
GELLO_REPO_URL="TODO"

clone_one() {
    local name="$1"
    local url="$2"
    local target="$SRC_DIR/$name"

    if [[ "$url" == *TODO* ]]; then
        echo "SKIP: $name — repository URL not set yet."
        echo "      Edit scripts/clone_repos.sh and set the URL for $name."
        echo "      See docs/repository_sources.md for details."
        return
    fi

    if [ -d "$target" ]; then
        echo "SKIP: $name — $target already exists."
        return
    fi

    echo "Cloning $name into $target ..."
    git clone "$url" "$target"
}

clone_one "icart_mini" "$ICART_MINI_REPO_URL"
clone_one "openxarm_ros2" "$OPENXARM_REPO_URL"
clone_one "gello" "$GELLO_REPO_URL"

echo ""
echo "Done. Any 'SKIP' above means a repository URL still needs to be added."
echo "See docs/repository_sources.md for what to confirm with the instructor."
