#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --nodes=1
#SBATCH --mem=0               # memory per node
#SBATCH --job-name=download_zinc

env_path=/groups/cherkasvgrp/share/progressive_docking/development/pd_python_pose
source $env_path/tensorflow_gpu/bin/activate

python download_zinc15.py -up $1 -fp $2 -fn $3  -tp $4
