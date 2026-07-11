# Setup Guide

## Recommended path for students: Docker

1. Install Docker (and the Docker Compose plugin).
2. Build the image:
   ```bash
   bash scripts/docker_build.sh
   ```
3. Enter the container:
   ```bash
   bash scripts/docker_shell.sh
   ```
4. Check the environment:
   ```bash
   bash scripts/check_environment.sh
   ```
5. Add repository URLs:
   edit `scripts/clone_repos.sh` (see
   [docs/repository_sources.md](repository_sources.md)).
6. Clone external repos:
   ```bash
   bash scripts/clone_repos.sh
   ```
7. Build the workspace:
   ```bash
   bash scripts/setup_workspace.sh
   ```
8. Source the workspace:
   ```bash
   source ros2_ws/install/setup.bash
   ```

See [docs/docker_workflow.md](docker_workflow.md) for day-to-day usage,
GUI tools, hardware access, and troubleshooting.

## Native setup

1. Use Ubuntu 24.04.
2. Install ROS 2 Jazzy (follow the official ROS 2 documentation).
3. Source ROS:
   ```bash
   source /opt/ros/jazzy/setup.bash
   ```
4. Run the same scripts as the Docker path:
   ```bash
   bash scripts/check_environment.sh
   bash scripts/clone_repos.sh
   bash scripts/setup_workspace.sh
   source ros2_ws/install/setup.bash
   ```

## Safety warning

Do not connect or command real robot hardware until:

- The emergency stop is known and tested.
- The robot is lifted, or the area around it is clear.
- The instructor gives explicit permission.
- One person is assigned as a safety observer.
