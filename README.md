# TESP Robot Basketball Workspace

This repository organizes the ROS 2 workspace for a mobile manipulation
basketball challenge using the iCart mini mobile base, OpenXArm/OpenRoboticX
arm, Gello controller, ROS 2, Nav2, and MoveIt.

## Repository purpose

- Keep setup instructions in one place.
- Clone external robot repositories into `ros2_ws/src`.
- Build the ROS 2 workspace.
- Provide a Docker environment for students.
- Later hold integration packages, launch files, and demo scripts.

## Getting started

Pick one of the two setup paths below. See [docs/setup.md](docs/setup.md)
for the full guide.

### Option A: Docker setup (recommended for students)

Use this when students do not already have a stable ROS 2 Jazzy installation.

On the host (only `git` is needed for the clone step, not ROS):

```bash
bash scripts/docker_build.sh
bash scripts/clone_repos.sh
bash scripts/docker_shell.sh
```

Inside the container:

```bash
bash scripts/check_environment.sh
bash scripts/setup_workspace.sh
source ros2_ws/install/setup.bash
```

### Option B: Native Ubuntu setup

Use this only if the machine already has Ubuntu 24.04 and ROS 2 Jazzy
installed.

```bash
source /opt/ros/jazzy/setup.bash
bash scripts/check_environment.sh
bash scripts/clone_repos.sh
bash scripts/setup_workspace.sh
source ros2_ws/install/setup.bash
```

## Docker vs. native

- Docker is recommended for learning, building, and simulation/development.
- Native setup may be required for direct hardware control depending on
  USB, network, real-time, or driver requirements.
- Students must not run real robot hardware until the instructor confirms
  safety.

## Documentation

- [docs/setup.md](docs/setup.md) — full setup guide (Docker + native)
- [docs/docker_workflow.md](docs/docker_workflow.md) — daily Docker workflow
- [docs/repository_sources.md](docs/repository_sources.md) — upstream repo
  URLs to be confirmed with the instructor
- [docs/ros2_quickstart.md](docs/ros2_quickstart.md) — ROS 2 concepts and
  commands for this robot
- [docs/troubleshooting.md](docs/troubleshooting.md) — common problems and
  fixes

## Repository layout

```
.
├── README.md
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── docs/                 # setup and workflow documentation
├── scripts/              # helper scripts for Docker and workspace setup
├── ros2_ws/               # ROS 2 workspace (src/ populated by clone_repos.sh)
└── .gitignore
```

## Safety

Do not connect or command real robot hardware until:

- The emergency stop is known and tested.
- The robot is lifted or the area around it is clear.
- The instructor gives explicit permission.
- One person is assigned as a safety observer.
