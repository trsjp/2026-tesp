# Docker Workflow

## Why use Docker?

- Everyone gets the same ROS 2 environment, regardless of their laptop's OS.
- Students do not need to install ROS 2 directly on their laptop.
- It reduces dependency problems ("it works on my machine").
- It is good for learning, building, and testing.

## What Docker does not automatically solve

- Real robot hardware may need USB permissions.
- Networked robots may need host networking.
- RViz GUI may need X11 configuration.
- Some hardware drivers may require native installation or privileged
  container access.

See [Hardware access](#hardware-access) and
[ROS 2 networking](#ros-2-networking) below.

## First-time setup

```bash
bash scripts/docker_build.sh
bash scripts/docker_shell.sh
```

Inside the container:

```bash
source /opt/ros/jazzy/setup.bash
bash scripts/check_environment.sh
bash scripts/clone_repos.sh
bash scripts/setup_workspace.sh
```

## Daily workflow

Every new terminal:

```bash
bash scripts/docker_shell.sh
```

Inside the container:

```bash
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
ros2 topic list
```

## Building the workspace

Inside the container:

```bash
cd /workspace/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

## Running RViz

On a Linux host:

```bash
xhost +local:docker
bash scripts/docker_shell.sh
rviz2
```

**Warning:** this may not work directly on macOS or Windows without extra
X server setup (e.g. XQuartz or VcXsrv).

## Hardware access

For USB devices such as Gello or motor controllers:

1. Check the device on the host:
   ```bash
   ls /dev/ttyUSB*
   ls /dev/ttyACM*
   ```
2. Add the device to `docker-compose.yml`:
   ```yaml
   devices:
     - /dev/ttyUSB0:/dev/ttyUSB0
   ```
3. Possibly add the container user to the `dialout` group (also
   commented out in `docker-compose.yml`):
   ```yaml
   group_add:
     - dialout
   ```
4. Only use `privileged: true` if the above is not enough, and only for
   real robot hardware sessions.

## ROS 2 networking

- ROS 2 uses DDS for discovery between nodes.
- Containers may not communicate with robots unless networking is
  configured correctly.
- Host networking (already configured in `docker-compose.yml`) is usually
  easier for lab robots than Docker's default bridge network.
- All machines that need to communicate must use the same
  `ROS_DOMAIN_ID`.
- Different student groups should use different `ROS_DOMAIN_ID` values to
  avoid interfering with each other.

## Stopping Docker

```bash
exit
docker compose down
```

## Common Docker problems

- **`docker: command not found`**
  Docker is not installed. See
  [docs/troubleshooting.md](troubleshooting.md).

- **Permission denied using Docker**
  Your user may not be in the `docker` group, or you may need `sudo`.

- **`docker compose` not found**
  The Docker Compose plugin is not installed, or you are using the old
  `docker-compose` (with a hyphen) binary instead of `docker compose`.

- **RViz cannot open display**
  Usually an X11/`DISPLAY` issue. Run `xhost +local:docker` on the host
  first (Linux only).

- **ROS 2 topics not visible**
  Check `ROS_DOMAIN_ID` matches on all machines, and that host networking
  is being used.

- **USB device not visible inside container**
  The device must be explicitly added under `devices:` in
  `docker-compose.yml` — it is not shared automatically.

For more detail, see [docs/troubleshooting.md](troubleshooting.md).
