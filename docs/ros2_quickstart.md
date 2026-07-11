# ROS 2 Quickstart

A short reference for students new to ROS 2. This does not cover robot
control for this project yet — it is background for reading and debugging
the system once integration packages exist.

## Core concepts

- **Node** — a process that does one job (e.g. drive the base, read a
  sensor, run a planner).
- **Topic** — a named stream of messages that nodes publish to and
  subscribe from (e.g. `/cmd_vel`, `/odom`).
- **Message** — the typed data structure sent over a topic.
- **Service** — a request/response call between nodes (unlike topics,
  which are one-way streams).
- **Action** — a long-running request with feedback and the ability to
  cancel (e.g. "navigate to this pose").
- **Parameter** — a named, typed configuration value a node can be
  configured with at runtime.
- **Launch file** — a Python (or XML/YAML) file that starts one or more
  nodes together with configuration.
- **TF (transforms)** — the system that tracks coordinate frames over
  time (e.g. where the arm is relative to the base).

## Common commands

```bash
ros2 node list
ros2 topic list
ros2 topic echo /joint_states
ros2 topic echo /odom
ros2 topic hz /scan
ros2 service list
ros2 action list
ros2 param list
ros2 launch <package> <launch_file.py>
ros2 run <package> <executable>
```

## How this maps to the robot

- `/cmd_vel` — controls the mobile base's velocity.
- `/odom` — the base's estimated motion (position/velocity over time).
- `/joint_states` — the arm's current joint positions.
- `/tf` — coordinate frames relating the base, arm, and world.
- `/scan` — laser/range sensor data, used by Nav2 for navigation.
- **Nav2** — plans and executes motion of the mobile base.
- **MoveIt** — plans motion for the arm.
- **Gello** — provides manual/lead-arm input for teleoperation.
