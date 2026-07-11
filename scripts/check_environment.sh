#!/usr/bin/env bash
# Print a summary of the current environment: what is installed, what is
# configured, and what might still be missing. This script intentionally
# does not exit on the first missing tool — it reports everything it can
# so students get a full picture in one run.
set -e

cd "$(dirname "$0")/.."

missing=()
recommend=()

check_cmd() {
    local name="$1"
    if command -v "$name" >/dev/null 2>&1; then
        echo "  $name: found"
    else
        echo "  $name: NOT found"
        missing+=("$name")
    fi
}

echo "=== TESP Robot Basketball — environment check ==="
echo ""

echo "General"
echo "  current directory: $(pwd)"
if [ -f /etc/os-release ]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    echo "  Ubuntu version: ${PRETTY_NAME:-unknown}"
else
    echo "  Ubuntu version: unknown (no /etc/os-release)"
fi
echo "  user: $(whoami)"
echo ""

echo "ROS 2"
echo "  ROS_DISTRO: ${ROS_DISTRO:-<not set>}"
echo "  ROS_DOMAIN_ID: ${ROS_DOMAIN_ID:-<not set>}"
echo "  RMW_IMPLEMENTATION: ${RMW_IMPLEMENTATION:-<not set>}"
if [ -z "$ROS_DISTRO" ]; then
    recommend+=("source /opt/ros/jazzy/setup.bash")
fi
echo ""

echo "Tools"
check_cmd ros2
check_cmd colcon
check_cmd git
check_cmd rosdep
check_cmd docker

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    echo "  docker compose: found"
else
    echo "  docker compose: NOT found"
    missing+=("docker compose")
fi
echo ""

echo "Workspace"
if [ -d "ros2_ws/src" ]; then
    echo "  ros2_ws/src: found"
else
    echo "  ros2_ws/src: NOT found"
    missing+=("ros2_ws/src")
fi
echo ""

echo "=== Summary ==="
if [ ${#missing[@]} -eq 0 ]; then
    echo "OK: all checked tools/paths were found."
else
    echo "Missing:"
    for m in "${missing[@]}"; do
        echo "  - $m"
    done
fi

if [ ${#recommend[@]} -gt 0 ]; then
    echo ""
    echo "Recommended next steps:"
    for r in "${recommend[@]}"; do
        echo "  - $r"
    done
fi
