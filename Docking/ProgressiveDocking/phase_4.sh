#!/bin/bash
#SBATCH --cpus-per-task=3
#SBATCH --ntasks=1
#SBATCH --mem=0               # memory per node
#SBATCH --job-name=phase_4
#SBATCH --output=slurm-%x.%j.out
#SBATCH --error=slurm-%x.%j.err

###************************************************************************
### Planned Changes:
###  > Reducing the number of passed parameters
###   |- How we currently run phase 4: "sbatch phase_4.sh current_itr n_cpu project_path project_name final_itr? total_itr"
###   |- How we want to run phase 4: "sbatch phase_4.sh current_itr n_cpu project_path/project_name final_itr? total_itr path_to_deep_docking_source"
###  > Get rid of smile_directory and sdf_directory for they are unused
###************************************************************************

echo Partition: $SLURM_JOB_PARTITION
echo "Passed Parameters:"
echo "Current Iteration: $1"
echo "Number of CPUs: $2"
echo "Project Path: $3"
echo Project Name: $(basename "$3")
echo "Final Iteration: $4"
echo "Total Iterations: $5"
echo "Path To Deep Docking Source Scripts: $6"
echo "Percent First Mol: $7"
echo "Percent Last Mol: $8"

# Reading the log file
file_path=`sed -n '1p' $3/logs.txt`
project_name=`sed -n '2p' $3/logs.txt`
morgan_directory=`sed -n '4p' $3/logs.txt`
num_hyperparameters=`sed -n '8p' $3/logs.txt`    # number of hyperparameters
docking_software=`sed -n '7p' $3/logs.txt`    # The docking software used

# The number of molecules to train on:
num_molec=`sed -n '9p' $3/logs.txt`

local_path=$6  # Should be the path to the deep docking source scripts
save_path=$3

# getting slurm args for gpu req scripts (with cpus-per-task and gpu_partition)
slurm_args_g=$(sed -n '4p' ${local_path}/slurm_args/${project_name}_slurm_args.txt)

# This should activate the conda environment
source ~/.bashrc
source $local_path/activation_script.sh

echo "writing jobs"
python jobid_writer.py -file_path $file_path/$project_name -n_it $1 -jid $SLURM_JOB_NAME -jn $SLURM_JOB_NAME.sh --save_path $save_path

t_pos=$2    # total number of processors available
echo "Extracting labels"
python Extract_labels.py -if False -n_it $1 -protein $project_name -file_path $file_path -t_pos $t_pos -sof $docking_software

if [ $? != 0 ]; then
  echo "Extract_labels failed... terminating"
  exit
fi

echo "Creating simple jobs"
python simple_job_models.py -n_it $1 -time 00-04:00 -file_path $file_path/$project_name -nhp $num_hyperparameters -titr $5 -n_mol $num_molec --save_path $save_path --percent_first_mols $7 --percent_last_mols $8

# Executes all the files that were created in the simple_jobs directory
echo "Running simple jobs"
cd $save_path/iteration_$1/simple_job

# For some reason, running this with the conda environment activated causes an error.
# We must deactivate it before running!
source ~/.bashrc
source $local_path/deactivation_script.sh
for f in *;do sbatch $slurm_args_g $f;done

echo "running phase_changer"
source ~/.bashrc
source $local_path/activation_script.sh
python $local_path/phase_changer.py -pf phase_4.sh -itr $file_path/$project_name/iteration_$1

# Clean up the slurm files
echo cleaning slurm files
cd $local_path
python slurm_file_manager.py --phase 4 --iteration $1 --project_path $3

echo "Done..."
