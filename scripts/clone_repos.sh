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
# CRG-Tohoku/icart-ros2 (branch worktree-ros2-jazzy-migration) is an
# instructor-authored ROS 2 Jazzy migration of open-rdc/icart. It is a
# single repo containing 6 colcon packages (icart_mini,
# icart_mini_description, icart_mini_control, icart_mini_driver,
# icart_mini_gazebo, icart_mini_setup) plus the ypspur_ros2 git
# submodule — colcon discovers all 6 packages recursively once cloned.
# See docs/repository_sources.md for the full breakdown and the Docker
# build-time system deps (yp-spur, Gazebo) this repo requires.
ICART_ROS2_REPO_URL="https://github.com/CRG-Tohoku/icart-ros2.git"

# --- Gello (lead-arm teleoperation controller) --------------------------
# Standalone Python project (installed with `uv`/pip), not a colcon/ROS
# package — despite having no package.xml, colcon's generic Python
# package identification still picks up its bare setup.py and tries to
# build it, which fails under --symlink-install (see COLCON_IGNORE
# marker below and docs/repository_sources.md for why). Its Python
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
ROBOTIS_INTERFACES_REPO_URL="https://github.com/ROBOTIS-GIT/robotis_interfaces.git"

clone_one() {
    local name="$1"
    local url="$2"
    local branch="${3:-}"
    local submodules="${4:-}"
    local colcon_ignore="${5:-}"
    local target="$SRC_DIR/$name"

    if [[ "$url" == *TODO* ]]; then
        echo "SKIP: $name — repository URL not set yet."
        echo "      Edit scripts/clone_repos.sh and set the URL for $name."
        echo "      See docs/repository_sources.md for details."
        return
    fi

    if [ -d "$target" ]; then
        echo "SKIP: $name — $target already exists."
    else
        local clone_args=()
        [ -n "$branch" ] && clone_args+=(-b "$branch")
        [ "$submodules" = "--recurse-submodules" ] && clone_args+=(--recurse-submodules)

        echo "Cloning $name${branch:+ (branch: $branch)} into $target ..."
        git clone "${clone_args[@]}" "$url" "$target"
    fi

    if [ "$colcon_ignore" = "--colcon-ignore" ]; then
        # Tells colcon to never treat this directory as a package to
        # build (colcon's standard mechanism — see docs/repository_sources.md
        # for why this is needed even though there's no package.xml here).
        touch "$target/COLCON_IGNORE"
    fi
}

clone_one "icart-ros2" "$ICART_ROS2_REPO_URL" "worktree-ros2-jazzy-migration" "--recurse-submodules"
clone_one "gello" "$GELLO_REPO_URL" "" "" "--colcon-ignore"
clone_one "open_manipulator" "$OPEN_MANIPULATOR_REPO_URL" "jazzy"
clone_one "dynamixel_hardware_interface" "$DYNAMIXEL_HARDWARE_INTERFACE_REPO_URL" "jazzy"
clone_one "dynamixel_interfaces" "$DYNAMIXEL_INTERFACES_REPO_URL" "jazzy"
clone_one "DynamixelSDK" "$DYNAMIXEL_SDK_REPO_URL" "jazzy"
clone_one "robotis_interfaces" "$ROBOTIS_INTERFACES_REPO_URL" "jazzy"

echo ""
echo "Done. Any 'SKIP' above means a repository URL still needs to be added."
echo "See docs/repository_sources.md for what to confirm with the instructor."
