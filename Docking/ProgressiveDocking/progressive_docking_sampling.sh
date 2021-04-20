#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=24
#SBATCH --gres=gpu:1
#SBATCH --mem=0               # memory per node
#SBATCH --job-name=sampling

env_path=/groups/cherkasvgrp/share/progressive_docking/pd_python
source $env_path/tensorflow_gpu/bin/activate

#python progressive_docking_sampling.py --file_n $1
python progressive_docking_sampling_test.py --file_n $1
