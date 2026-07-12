#!/usr/bin/env bash
# Clone external robot repositories into ros2_ws/src.
#
# Run this on the HOST, before starting the container (before
# docker_shell.sh / docker_run.sh / `docker compose up`). It only needs
# git, not ROS, and the repository is bind-mounted into the container
# (see docker-compose.yml), so anything cloned here on the host is
# immediately visible inside the container once it starts.
#
# Run from the repository root: bash scripts/clone_repos.sh
set -e

cd "$(dirname "$0")/.."

SRC_DIR="ros2_ws/src"
mkdir -p "$SRC_DIR"

# --- iCart mini (mobile base) ------------------------------------------
# Intentionally left as TODO: the upstream repo (open-rdc/icart) has no
# ROS 2 branch at all — every branch is ROS1/catkin (confirmed by
# checking all branches). There is an unofficial, unmaintained community
# ROS2 port (haruyama8940/icart_mini_driver_ros2, last updated 2023,
# untested on Jazzy, missing description/gazebo packages) — see
# docs/repository_sources.md if the instructor wants to evaluate it.
ICART_MINI_REPO_URL="TODO"

# --- Gello (lead-arm teleoperation controller) --------------------------
# Standalone Python project (installed with `uv`/pip), not a colcon/ROS
# package at the top level — `setup_workspace.sh`'s colcon build will
# simply skip this folder (no package.xml at its root). Its Python
# environment (Python 3.11 via `uv`) must be set up separately, following
# gello_software's own README. See docs/repository_sources.md.
GELLO_REPO_URL="https://github.com/wuphilipp/gello_software.git"

# --- ROBOTIS OpenManipulator (arm) + required companion packages -------
# Official ROS 2 Jazzy support lives on the `jazzy` branch (confirmed via
# ROBOTIS's own docker/Dockerfile on that branch). ROBOTIS's own Docker
# workflow clones these 3 companion packages alongside the main repo and
# builds everything from source via rosdep + colcon (see
# scripts/setup_workspace.sh) rather than relying on prebuilt apt
# packages — this script mirrors that exactly.
OPEN_MANIPULATOR_REPO_URL="https://github.com/ROBOTIS-GIT/open_manipulator.git"
DYNAMIXEL_HARDWARE_INTERFACE_REPO_URL="https://github.com/ROBOTIS-GIT/dynamixel_hardware_interface.git"
DYNAMIXEL_INTERFACES_REPO_URL="https://github.com/ROBOTIS-GIT/dynamixel_interfaces.git"
DYNAMIXEL_SDK_REPO_URL="https://github.com/ROBOTIS-GIT/DynamixelSDK.git"

clone_one() {
    local name="$1"
    local url="$2"
    local branch="${3:-}"
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

    if [ -n "$branch" ]; then
        echo "Cloning $name (branch: $branch) into $target ..."
        git clone -b "$branch" "$url" "$target"
    else
        echo "Cloning $name into $target ..."
        git clone "$url" "$target"
    fi
}

clone_one "icart_mini" "$ICART_MINI_REPO_URL"
clone_one "gello" "$GELLO_REPO_URL"
clone_one "open_manipulator" "$OPEN_MANIPULATOR_REPO_URL" "jazzy"
clone_one "dynamixel_hardware_interface" "$DYNAMIXEL_HARDWARE_INTERFACE_REPO_URL" "jazzy"
clone_one "dynamixel_interfaces" "$DYNAMIXEL_INTERFACES_REPO_URL" "jazzy"
clone_one "DynamixelSDK" "$DYNAMIXEL_SDK_REPO_URL" "jazzy"

echo ""
echo "Done. Any 'SKIP' above means a repository URL still needs to be added."
echo "See docs/repository_sources.md for what to confirm with the instructor."
