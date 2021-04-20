#!/bin/bash
#SBATCH --cpus-per-task=24
#SBATCH --partition=normal
#SBATCH --job-name=prepare
#SBATCH --output=slurm-phase_2-%x.%j.out
#SBATCH --error=slurm-phase_2-%x.%j.err

script_path=$1

# This should activate the conda environment
source ~/.bashrc
source $script_path/activation_script.sh

start=`date +%s`

name=$(pwd| rev | cut -d'/' -f 1 | rev)
fld=$name'_'pdbqt

# This line is a problem...
$openeye tautomers -in $name'.'smi -out $name'_'h.smi -maxtoreturn 1 -warts false
wait $!

$openeye oeomega classic -in $name'_'h.smi -out $name'.'sdf  -strictstereo false -maxconfs 1 -mpi_np 20 -log $name'.'log -prefix $name
wait $!

rm -r $fld
mkdir $fld
cp $name'.'sdf $fld'/'
cd $fld
python $script_path'/'split_sdf.py $name'.'sdf
rm $name'.'sdf
obabel -isdf *sdf -opdbqt -m
wait $!
rm *sdf

end=`date +%s`
echo $((end-start))
echo finished