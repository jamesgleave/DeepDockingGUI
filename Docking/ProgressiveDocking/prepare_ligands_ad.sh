#!/bin/bash
#SBATCH --job-name=prepare
#SBATCH --time=04:00:00
#SBATCH --output=slurm-phase_2-%x.%j.out
#SBATCH --error=slurm-phase_2-%x.%j.err

script_path=$1

# This should activate the conda environment
source ~/.bashrc
source $script_path/activation_script.sh

start=`date +%s`

name=$(pwd| rev | cut -d'/' -f 1 | rev)
fld=$name'_'pdbqt

# Uncomment the next three lines if you have openeye and want to do tautomer generation on the fly (instead of preparing the library beforehand); add also #SBATCH --cpus-per-task=20 at the top as openeye uses MPI 
# $openeye tautomers -in $name'.'smi -out $name'_'h.smi -maxtoreturn 1 -warts false
# wait $!
# mv $name'_'h.smi $name'.'smi       

# obabel takes a lot longer than openeye, but both of the following lines work for 3d conformer generation
# $openeye oeomega classic -in $name'.'smi -out $name'.'sdf  -strictstereo false -maxconfs 1 -mpi_np 20 -log $name'.'log -prefix $name
obabel -ismi $name'.'smi -O $name'.'sdf --gen3d --fast
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
