#!/bin/bash
#SBATCH --cpus-per-task=24
#SBATCH --partition=normal
#SBATCH --ntasks=1
#SBATCH --mem=0               # memory per node
#SBATCH --job-name=phase_1
#SBATCH --output=slurm-%x.%j.out
#SBATCH --error=slurm-%x.%j.err

# ARGS Passed:
iteration=$1
t_cpu=$2
project_path=$3
project_name=$4
mol_to_dock=$5  # Replace with sample size (training set)
local_path=$6

echo Args:
echo Iteration: $iteration
echo Total CPUs: $t_cpu
echo Project Path: $project_path
echo Project Name: $project_name
echo Mols To Dock: $mol_to_dock
echo Scripts: $local_path

# This should activate the conda environment
source ~/.bashrc
source $local_path/activation_script.sh

# Set constants
file_path=`sed -n '1p' $project_path/$project_name/logs.txt`
protein=`sed -n '2p' $project_path/$project_name/logs.txt`
n_mol=`sed -n '9p' $project_path/$project_name/logs.txt`
morgan_directory=`sed -n '4p' $project_path/$project_name/logs.txt`
smile_directory=`sed -n '5p' $project_path/$project_name/logs.txt`
sdf_directory=`sed -n '6p' $project_path/$project_name/logs.txt`

# Set the to be docked
pr_it=$(($1-1))
if [ $1 == 1 ]
then 
	to_d=$((n_mol+n_mol+mol_to_dock))
else
	to_d=$mol_to_dock
fi
echo To Dock: $to_d

# set the total CPUs
if [ $t_cpu == 64 ];then t_cpu=48;fi
echo Total CPU: $t_cpu

python jobid_writer.py -file_path $file_path/$protein -n_it $1 -jid $SLURM_JOB_NAME -jn $SLURM_JOB_NAME.sh
if [ $1 == 1 ];then pred_directory=$morgan_directory;else pred_directory=$file_path/$protein/iteration_$pr_it/morgan_1024_predictions;fi

python molecular_file_count_updated.py -pt $protein -it $1 -cdd $pred_directory -t_pos $t_cpu -t_samp $to_d
python sampling.py -pt $protein -fp $file_path -it $1 -dd $pred_directory -t_pos $t_cpu -tr_sz $mol_to_dock -vl_sz $n_mol
python sanity_check.py -pt $protein -fp $file_path -it $1
python Extracting_morgan.py -pt $protein -fp $file_path -it $1 -md $morgan_directory -t_pos $t_cpu
python Extracting_smiles.py -pt $protein -fp $file_path -it $1 -fn 0 -smd $smile_directory -sd $sdf_directory -t_pos $t_cpu -if False

python phase_changer.py -pf phase_1.sh -itr $file_path/$protein/iteration_$1
echo python phase_changer.py -pf phase_1.sh -itr $file_path/$protein/iteration_$1


# Clean up the slurm files
echo cleaning slurm files
python slurm_file_manager.py --phase 1 --iteration $iteration --project_path $project_path/$project_name

# This extracts the zinc ids by randomly sampling and creates the datasets
# - If a smile file is found on line l in file f then the morgan fingerprint will be on the same line in the same file in the equivalent file.

# how to run phase_1.sh:
# sbatch phase_1.sh iteration t_cpu project_path project_name mol_to_dock
#   - Note: that mol_to_dock should match what is in the logs file or it could not haha
