#!/bin/bash
#SBATCH --cpus-per-task=1
#SBATCH --partition=normal
#SBATCH --mem=0               # memory per node
#SBATCH --job-name=phase_2
#SBATCH --output=slurm-%x.%j.out
#SBATCH --error=slurm-%x.%j.err

# Args
extension=$1  # .smi
chunk_n_lines=$2  # 1000
script_path=$3  # path to scripts
project_path=$4  # path to project
iteration=$5

echo Args:
echo Extension: $extension
echo Chunk Size: $chunk_n_lines
echo Project Path: $project_path
echo Project Name: $(basename "$project_path")
echo Iteration: $iteration

# This should activate the conda environment
source ~/.bashrc
source $script_path/activation_script.sh

python $script_path/jobid_writer.py -file_path $project_path -n_it $iteration -jid $SLURM_JOB_NAME -jn $SLURM_JOB_NAME.sh

# For some reason, running this with the conda environment activated causes an error.
# We must deactivate it before running!
source ~/.bashrc
source $local_path/deactivation_script.sh

# Move into the project
cd $project_path/iteration_$iteration

# Start running the chunking
echo Starting Phase 2
echo Chunking Train, Test, and Valid Sets...
sbatch $script_path/split_chunks.sh smile/train_smiles_final_updated.smi $extension train $chunk_n_lines $script_path
sbatch $script_path/split_chunks.sh smile/test_smiles_final_updated.smi $extension test $chunk_n_lines $script_path
sbatch $script_path/split_chunks.sh smile/valid_smiles_final_updated.smi $extension valid $chunk_n_lines $script_path

# This should activate the conda environment
source ~/.bashrc
source $script_path/activation_script.sh

# wait for completion
echo Finished Chunking
wait
python $script_path/phase_changer.py -pf phase_2.sh -itr $project_path/iteration_$iteration
echo Phase 2 Finished

# Clean up the slurm files
echo cleaning slurm files
cd $script_path
python slurm_file_manager.py --phase 2 --iteration $iteration --project_path $project_path


# sbatch phase_2.sh .smi 1000 /groups/cherkasvgrp/share/progressive_docking/development/pd_python_pose_v2/test_DD_installation/DeepDocking /groups/cherkasvgrp/share/progressive_docking/development/pd_python_pose_v2/test_DD_installation/DeepDockingProjects/full_run_test_james 1
