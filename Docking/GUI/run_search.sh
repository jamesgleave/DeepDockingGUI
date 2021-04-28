#!/bin/bash
#SBATCH -n 1
#SBATCH --job-name=smile_searching
#SBATCH --cpus-per-task=25
#SBATCH --output=slurm-%x.%j.out
#SBATCH --error=slurm-%x.%j.err

# Read input
project_path=$1
n_cpus=$2
iteration=$3
n=$4

echo Args:
echo Iteration: $iteration
echo Total CPUs: $n_cpus
echo Project Path: $project_path
echo Project Name: $(basename "$project_path")
echo Num Mols: $n

# Set constant
smile_directory=`sed -n '5p' $project_path/logs.txt`

cd ..
# This should activate the conda environment
source ~/.bashrc
source activation_script.sh

cd GUI
python fast_top_hit_search.py -sdb $smile_directory -pdb $project_path/iteration_$iteration/morgan_1024_predictions -tp $n_cpus -n $n
