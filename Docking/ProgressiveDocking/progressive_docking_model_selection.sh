#!/bin/bash
#SBATCH --cpus-per-task=24
#SBATCH --ntasks=1
#SBATCH --mem=0               # memory per node
#SBATCH --job-name=phase_4
#SBATCH --partition=normal

file_path=`sed -n '1p' $3/$4/logs.txt`
protein=`sed -n '2p' $3/$4/logs.txt`

morgan_directory=`sed -n '4p' $3/$4/logs.txt`
smile_directory=`sed -n '5p' $3/$4/logs.txt`
sdf_directory=`sed -n '6p' $3/$4/logs.txt`
nhp=`sed -n '8p' $3/$4/logs.txt`    # number of hyperparameters
sof=`sed -n '7p' $3/$4/logs.txt`    # The docking software used

# The number of molecules to train on:
num_molec=`sed -n '9p' $3/$4/logs.txt`

local_path=/groups/cherkasvgrp/share/progressive_docking/development/pd_python_pose
env_path=/groups/cherkasvgrp/share/progressive_docking/development/pd_python_pose

echo "writing jobs"
python jobid_writer.py -protein $protein -file_path $file_path -n_it $1 -jid $SLURM_JOB_NAME -jn $SLURM_JOB_NAME.sh

source /home/jgleave/.conda/envs/keras_tuning/bin/activate

t_pos=$2    # total number of processers available
echo "Extracting labels"
python Extract_labels.py -if False -n_it $1 -protein $protein -file_path $file_path -t_pos $t_pos -sof $sof

if [ $? != 0 ]; then
  echo "Extract_labels failed... terminating"
  exit
fi


echo "Creating simple jobs"
python progressive_docking_model_selection_sjm.py -n_it $1 -mdd $morgan_directory -time 00-04:00 -file_path $file_path/$protein -nhp $nhp -titr $6 -n_mol $num_molec  -model_dir $7  #TODO: add -t_n_mol here

cd $file_path/$protein/iteration_$1/simple_job

echo "Running simple jobs"
# Executes all the files that were created in the simple_jobs directory
for f in *;do sbatch $f;done

#echo "running phase_changer"
#python $local_path/phase_changer.py -pf phase_4.sh -itr $file_path/$protein/iteration_$1
#echo "Done..."