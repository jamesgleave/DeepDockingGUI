#!/bin/bash
#SBATCH --cpus-per-task=24
#SBATCH --partition=normal
#SBATCH --ntasks=1
#SBATCH --mem=0               # memory per node
#SBATCH --job-name=phase_f
#SBATCH --output=slurm-%x.%j.out
#SBATCH --error=slurm-%x.%j.err

# Read input
project_path=$1
n_cpus=$2
iteration=$3
scripts=$4
mol_to_dock=$5

echo Project Path: $project_path
echo Project Name: $(basename "$project_path")
echo Num. CPU: $n_cpus
echo Iteration: $iteration
echo Script Path: $scripts
echo Final Mol. To Dock: $mol_to_dock

# Set constant
smile_directory=`sed -n '5p' $project_path/logs.txt`

# This should activate the conda environment
source ~/.bashrc
source activation_script.sh

# cd into the final iteration and run the search
cd $project_path/iteration_$iteration
echo Running >| final_phase.info # created in phase_a
echo Smile Dir: $smile_directory
python -u $scripts/final_extraction.py -smile_dir $smile_directory -morgan_dir $project_path/iteration_$iteration/morgan_1024_predictions/ -processors $n_cpus -mols_to_dock $mol_to_dock

# If the above final extraction failed, we try another slower version
if grep -Fxq "Failed" final_phase.info
then
  echo Running |> final_phase.info
  python -u $scripts/GUI/overloaded_final_extraction.py -smile_dir $smile_directory -morgan_dir $project_path/iteration_$iteration/morgan_1024_predictions/ -processors $n_cpus -mols_to_dock $mol_to_dock
fi

# Clean up the slurm files
echo cleaning slurm files
cd $scripts
python3 $scripts/slurm_file_manager.py --phase 0 --iteration $iteration --project_path $project_path
echo Done

