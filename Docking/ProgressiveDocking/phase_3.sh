#!/bin/bash
#SBATCH --cpus-per-task=1
#SBATCH --partition=normal
#SBATCH --ntasks=1
#SBATCH --mem=0 # memory per node
#SBATCH --job-name=phase_3
#SBATCH --output=slurm-%x.%j.out
#SBATCH --error=slurm-%x.%j.err

# ARGS
PATH_FLD=$1
num_energy_evaluations=$2
num_runs=$3
path_to_auto_dock_gpu=$4
project_path=$5
iteration=$6
scripts=$7


echo Args:
echo FLD Path: $PATH_FLD
echo Energy Evaluations: $num_energy_evaluations
echo Num Runs: $num_runs
echo Path To Autodock: $path_to_auto_dock_gpu
echo Project Path: $project_path
echo Project Name: $(basename "$project_path")
echo Iteration: $iteration
echo Scripts: $scripts

# This should activate the conda environment
source ~/.bashrc
source $local_path/activation_script.sh

#path_to_auto_dock_gpu=/groups/cherkasvgrp/autodock/scottlegrand/AutoDock-GPU.relicensing/bin
python jobid_writer.py -file_path $project_path -n_it $iteration -jid $SLURM_JOB_NAME -jn $SLURM_JOB_NAME.sh --save_path $project_path

# Run phase 3
cd $project_path/iteration_$iteration
echo Running Phase 3
mkdir res
for i in $(ls -d chunks_smi/*); do fld=$(echo $i | rev | cut -d'/' -f 1 | rev); mkdir res/$fld; cd res/$fld; sbatch $scripts/autodock_gpu_ad.sh 64 sw $PATH_FLD ../../$i'/'$fld'_'pdbqt list.txt $num_energy_evaluations $num_runs $path_to_auto_dock_gpu $scripts; cd ../../;done

cd $scripts
python phase_changer.py -pf phase_3.sh -itr $project_path/iteration_$iteration

# Clean up the slurm files
echo cleaning slurm files
python slurm_file_manager.py --phase 3 --iteration $iteration --project_path $project_path
echo Done

#sbatch phase_3.sh /groups/cherkasvgrp/share/progressive_docking/development/AD_GPU/autodock_grid/x77_grid.maps.fld 5000000 10 /groups/cherkasvgrp/autodock/scottlegrand/AutoDock-GPU.relicensing/bin /groups/cherkasvgrp/share/progressive_docking/development/pd_python_pose_v2/test_DD_installation/DeepDockingProjects/full_run_test_james 1 /groups/cherkasvgrp/share/progressive_docking/development/pd_python_pose_v2/test_DD_installation/DeepDocking