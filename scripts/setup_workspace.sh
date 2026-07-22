#!/usr/bin/env bash
# Install dependencies and build the ROS 2 workspace.
#
# Run from the repository root: bash scripts/setup_workspace.sh
set -e

cd "$(dirname "$0")/.."

if [ -z "$ROS_DISTRO" ]; then
    echo "ERROR: ROS 2 is not sourced (ROS_DISTRO is empty)."
    echo "Run this first:"
    echo "  source /opt/ros/jazzy/setup.bash"
    exit 1
fi

cd ros2_ws

echo "Updating rosdep database..."
rosdep update

echo "Installing dependencies with rosdep..."
rosdep install --from-paths src --ignore-src -r -y || echo "WARNING: some rosdep packages could not be installed (some may not be available in this distro version)"

echo "Building workspace with colcon..."
colcon build --symlink-install --continue-on-error || echo "WARNING: one or more packages failed to build — check the colcon summary above for which ones."

echo ""
echo "Build finished. Source the workspace with:"
echo "  source ros2_ws/install/setup.bash"
