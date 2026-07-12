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

## Keeping the workspace in sync (bind mount + UID/GID matching)

The whole repository is bind-mounted into the container at `/workspace`
(see the `volumes:` entry in `docker-compose.yml`), not copied into the
image. That means:

- Any file created or edited on the host — including repos cloned into
  `ros2_ws/src` — is immediately visible inside the container, and vice
  versa. There is no separate "sync" step.
- The container's `ros` user is built with your host user's UID/GID
  (auto-detected by `scripts/docker_build.sh`), so files created *inside*
  the container (colcon's `build/`, `install/`, `log/`, or repos cloned
  in-container) come out owned by you on the host — not a foreign UID
  that would need `sudo` to edit or delete.
- If files ever do show up with the wrong owner on the host (e.g. after
  pulling the image on a different machine, or if the image was built
  before this UID/GID matching was added), rerun
  `bash scripts/docker_build.sh` to rebuild with the correct UID/GID.

## First-time setup

On the host:

```bash
bash scripts/docker_build.sh
bash scripts/clone_repos.sh
bash scripts/docker_shell.sh
```

Inside the container:

```bash
source /opt/ros/jazzy/setup.bash
bash scripts/check_environment.sh
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
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --continue-on-error
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

By default, `docker-compose.yml` already gives the container broad
sensor/device access:

- `/dev:/dev` — the whole host `/dev` tree is bind-mounted in, so
  cameras, serial adapters, and other sensors attached to the host are
  visible inside the container without extra configuration.
- `/dev/dri:/dev/dri` and `/dev/snd:/dev/snd` — GPU render nodes (for
  hardware-accelerated video/camera pipelines and RViz) and audio
  devices, passed through explicitly.

**This is broad access** — it is only appropriate on the lab machine that
is actually connected to the robot. Treat it with the same care as real
hardware: don't connect or command real robot hardware until the
instructor confirms it's safe (see
[docs/setup.md](setup.md#safety-warning)).

For a USB device such as Gello or a motor controller:

1. Check the device on the host (it should already be visible inside the
   container too, via `/dev:/dev`):
   ```bash
   ls /dev/ttyUSB*
   ls /dev/ttyACM*
   ```
2. If you want to scope access down to just that device instead of the
   full `/dev:/dev` mount, add it to the `devices:` list in
   `docker-compose.yml` and remove the `/dev:/dev` volume line:
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

### OpenManipulator arm (U2D2 USB-serial adapter)

The arm's U2D2 USB-serial adapter needs a udev rule so it shows up with
consistent permissions. ROBOTIS provides this in the cloned
`open_manipulator` repo — after running `scripts/clone_repos.sh`, follow
its own instructions to install the rule (typically
`open_manipulator_bringup/open-manipulator-cdc.rules` plus the
`om_create_udev_rules.py` helper script). This is not automated by this
repository — check the arm's own README for the current steps before
connecting it.

### iCart mini (URG lidar + joystick)

`icart_mini_driver` (real hardware) depends on a URG lidar (`urg_node`)
and joystick teleop (`joy`, `teleop_twist_joy`) in addition to the
YP-Spur motor-controller bridge (`ypspur_ros2`). Like the OpenManipulator
arm, these are real-hardware components: don't launch `icart_mini_driver`
until the instructor confirms it's safe (see
[docs/setup.md](setup.md#safety-warning)). `icart_mini_setup` (cloned
alongside the driver) has scripts to generate the udev rules and
parameter files these depend on — see its README under
`ros2_ws/src/icart-ros2/icart_mini_setup`.

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
