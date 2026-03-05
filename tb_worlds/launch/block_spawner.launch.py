import os
import math
import yaml
import random
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    lds = []  # Launch Descriptions
    pkg_dir = get_package_share_directory("tb_worlds")

    # Parse locations YAML file
    yaml_config_path = os.path.join(pkg_dir, "maps", "sim_house_locations.yaml")
    with open(yaml_config_path, "r") as f:
        locations = yaml.load(f, Loader=yaml.FullLoader)

    # Offset between Gazebo world and map frame (can we fix this somehow else?)
    block_spawn_offset = [-0.6, -0.6]

    # Distance from navigation waypoint to spawn object
    offset_from_robot = 0.6

    # Spawn blocks in random locations
    model_names = ["red_block", "green_block", "blue_block"]
    sampled_locs = random.sample(list(locations.keys()), len(model_names))
    for mdl_name, loc in zip(model_names, sampled_locs):
        x, y, theta = locations[loc]
        x += block_spawn_offset[0] + offset_from_robot * math.cos(theta)
        y += block_spawn_offset[1] + offset_from_robot * math.sin(theta)

        mdl_sdf = os.path.join(pkg_dir, "models", mdl_name, "model.sdf")
        lds.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        get_package_share_directory("ros_gz_sim"),
                        "launch",
                        "gz_spawn_model.launch.py",
                    )
                ),
                launch_arguments={
                    "world": "",
                    "file": mdl_sdf,
                    "name": mdl_name,
                    "x": str(x),
                    "y": str(y),
                    "z": "0.06",
                    "Y": str(theta),
                }.items(),
            )
        )

    # Add benches at fixed wall locations
    benches = [
        {
            'name': 'bench_with_vehicles',
            'pose': [-0.15, -1.3, -0.12, 0, 0, 1.57],  # South wall, centered
        },
        {
            'name': 'bench_with_furniture',
            'pose': [2.6, 0.0, -0.12, 0, 0, -0.7853],    # East wall, centered
        },
        {
            'name': 'bench_with_food',
            'pose': [0.1, 1.5, -0.12, 0, 0, -1.57],   # North wall, centered
        }
        # {
        #     'name': 'bench_with_vehicles',
        #     'pose': [0.0, 2.6, 0.00, 0, 0, -1.57],   # North wall, centered
        # },
    ]
    for bench in benches:
        mdl_sdf = os.path.join(pkg_dir, "models", bench['name'], "model.sdf")
        lds.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        get_package_share_directory("ros_gz_sim"),
                        "launch",
                        "gz_spawn_model.launch.py",
                    )
                ),
                launch_arguments={
                    "world": "",
                    "file": mdl_sdf,
                    "name": bench['name'],
                    "x": str(bench['pose'][0]),
                    "y": str(bench['pose'][1]),
                    "z": str(bench['pose'][2]),
                    "Y": str(bench['pose'][5]),
                }.items(),
            )
        )
    return LaunchDescription(lds)
