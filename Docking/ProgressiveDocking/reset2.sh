echo Resetting Phase 2 on $(basename $1)...

# Remove the slurm files associated with the project
python3 reset.py --project_name "$2" --username "$3" --scripts "$4"

# Move into the project
cd $1
rm -r chunks_smi