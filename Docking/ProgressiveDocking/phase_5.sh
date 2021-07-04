#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --mem=0               # memory per node
#SBATCH --job-name=phase_5
#SBATCH --output=slurm-%x.%j.out
#SBATCH --error=slurm-%x.%j.err

### This will be replacing the old phase 5 script
### (make sure to decrease all other parameters after 3 when doing so)

###************************************************************************
### Planned Changes:
###  > Reducing the number of passed parameters to 1
###   |- How we currently run phase 5: "sbatch phase_5.sh iteration path_to_project project_name"
###   |- How we want to run phase 5: "sbatch phase_5.sh iteration path_to_project/project_name progressive_docking_path"
###  > Get rid of smile_directory and sdf_directory for they are unused
###************************************************************************

### Scan through the logs.txt file
file_path=`sed -n '1p' $2/logs.txt`
protein=`sed -n '2p' $2/logs.txt`    # name of project folder
morgan_directory=`sed -n '4p' $2/logs.txt`
num_molec=`sed -n '9p' $2/logs.txt`

progressive_docking_path=$3
save_path=$2
project_name=$(basename "$2")

echo Partition: $SLURM_JOB_PARTITION
echo "Passed Parameters:"
echo "Current Iteration: $1"
echo "Project Path: $2"
echo Project Name: $project_name
echo "Scripts: $3"
echo "Number of CPUs: $4"

# This should activate the conda environment
source ~/.bashrc
source $progressive_docking_path/activation_script.sh

# getting slurm args for gpu req scripts (with cpus-per-task and gpu_partition)
slurm_args_g=$(sed -n '4p' ${progressive_docking_path}/slurm_args/${project_name}_slurm_args.txt)


python jobid_writer.py -file_path $file_path/$protein -n_it $1 -jid $SLURM_JOB_NAME -jn $SLURM_JOB_NAME.sh --save_path $save_path

echo "Starting Evaluation"
python -u hyperparameter_result_evaluation.py -n_it $1 --data_path $file_path/$protein -n_mol $num_molec --save_path $save_path
echo "Creating simple_job_predictions"
python simple_job_predictions.py -protein $protein -file_path $file_path -n_it $1 -mdd $morgan_directory --save_path $save_path

# For some reason, running this with the conda environment activated causes an error.
# We must deactivate it before running!
source ~/.bashrc
source $progressive_docking_path/deactivation_script.sh
cd $save_path/iteration_$1/simple_job_predictions/
echo "running simple_jobs"
for f in *;do sbatch $slurm_args_g $f; done

echo "waiting for event phase change"
source ~/.bashrc
source $progressive_docking_path/activation_script.sh
python $progressive_docking_path/phase_changer.py -pf phase_5.sh -itr $file_path/$protein/iteration_$1

# Now we grab the top hits
source ~/.bashrc
source $progressive_docking_path/deactivation_script.sh

echo Phase 5 is finished. Now searching for top predicted molecules.
cd $progressive_docking_path/GUI
sbatch run_search.sh $2 $4 $1 1000 #TODO: slurm args for this?

# Clean up the slurm files
echo Cleaning slurm files
cd $progressive_docking_path
python slurm_file_manager.py --phase 5 --iteration $1 --project_path $2 --script_path $3

echo All finished.