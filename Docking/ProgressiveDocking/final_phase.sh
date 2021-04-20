#!/bin/bash
#SBATCH --cpus-per-task=24
#SBATCH --partition=normal
#SBATCH --ntasks=5
#SBATCH --mem=0               # memory per node
#SBATCH --job-name=phase_f
#SBATCH --output=slurm-%x.%j.out
#SBATCH --error=slurm-%x.%j.err

# Gather the arguments
t_cpu=$2
local_path=$5

# Read the logs file
file_path=`sed -n '1p' $3/$4/logs.txt`
protein=`sed -n '2p' $3/$4/logs.txt`
smile_directory=`sed -n '5p' $3/$4/logs.txt`
sdf_directory=`sed -n '6p' $3/$4/logs.txt`

# Make a new directory for after the runs
mkdir $file_path/$protein/after_iteration
python jobid_writer.py -file_path $file_path/$protein -n_it $1 -jid $SLURM_JOB_NAME -jn $SLURM_JOB_NAME.sh

# This should activate the conda environment
source ~/.bashrc
source $local_path/activation_script.sh

# Run the final step. This will get the top n molecules and dock them.
python final_step.py -pt $protein -fp $file_path -it $1 -t_pos $t_cpu

# Move into the to dock directory
cd $file_path/$protein/after_iteration/to_dock

# Run all extract smiles on all the text files
ct=0
for f in *.txt
do
	((++ct))
	tmp="$(cut -d'_' -f3 <<<"$f")"
	tmp="$(cut -d'.' -f1 <<<"$tmp")"
	(srun -n 1 -N 1 --jobid=$SLURM_JOBID --job-name=$SLURM_JOB_NAME python $local_path/Extracting_smiles.py -pt $protein -fp $file_path -it $1 -fn $tmp -smd $smile_directory -sd $sdf_directory -t_pos $t_cpu -if True)&
	if (($ct % 1 ==0));then wait;fi
done
wait

# Create a new directory for smiles
mkdir smile_ph

# Finally, we dock the molecules
cd smile
for f in *.smi
do
   ($openeye tautomers -in $f -out ../smile_ph/$f -maxtoreturn 1)&
done
wait

