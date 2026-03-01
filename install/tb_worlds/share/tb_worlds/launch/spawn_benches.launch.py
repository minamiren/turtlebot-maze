import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Paths to models
    models_path = os.path.join(
        get_package_share_directory('tb_worlds'), 'models')
    
    # Model names and poses (touching walls)
    spawn_data = [
        {
            'name': 'bench_with_animals',
            'pose': [0.5, -2.7, 0.0, 0, 0, 1.57],  # near south wall
        },
        {
            'name': 'bench_with_fruits',
            'pose': [-2.7, 0.5, 0.0, 0, 0, 0],      # near west wall
        },
        {
            'name': 'bench_with_misc',
            'pose': [2.7, 0.5, 0.0, 0, 0, 3.14],    # near east wall
        },
    ]

    spawn_nodes = []
    for item in spawn_data:
        spawn_nodes.append(
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
                    "file": os.path.join(models_path, item['name'], 'model.sdf'),
                    "name": item['name'],
                    "x": str(item['pose'][0]),
                    "y": str(item['pose'][1]),
                    "z": str(item['pose'][2]),
                    "Y": str(item['pose'][5]),
                }.items(),
            )
        )

    return LaunchDescription(spawn_nodes)
