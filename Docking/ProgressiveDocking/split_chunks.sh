#!/bin/bash
#SBATCH --cpus-per-task=24
#SBATCH --partition=normal
#SBATCH --ntasks=1
#SBATCH --job-name=split_chunks
#SBATCH --output=slurm-phase_2-%x.%j.out
#SBATCH --error=slurm-phase_2-%x.%j.err

input=$1
extension=$2
output=$3
chunk_n_lines=$4
script_path=$5

echo "Working..."

mkdir -p chunks_smi

split -a 4 -d -l $chunk_n_lines --additional-suffix=${extension} ${input} chunks_smi/${output}_set_part

cd chunks_smi

for x in ./$output*${extension}; do
  mkdir "${x%.*}" && mv "$x" "${x%.*}"
done

# Start preparing ligands
cd ..
return=$PWD
echo Preparing Ligands
for i in $(ls -d chunks_smi/$output*); do cd $i; sbatch $script_path/prepare_ligands_ad.sh $script_path; cd $return; done

echo "Done!"