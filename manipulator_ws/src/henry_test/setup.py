from setuptools import find_packages, setup

package_name = 'henry_test'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', ['config/moveit_cpp.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ros',
    maintainer_email='ros@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            "moveit_py_teleop_ik_guarded = henry_test.moveit_py_joystick_teleop_ik_guarded:main",
            "ball_grabber_node = henry_test.ball_grabber_node:main",
            "ball_position_publisher_example = henry_test.ball_position_publisher_example:main"
        ],
    },
)
