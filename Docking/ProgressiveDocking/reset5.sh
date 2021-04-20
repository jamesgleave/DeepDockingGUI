echo Resetting Phase 5 on $(basename $1)...

# Remove the slurm files associated with the project
python3 reset.py --project_name "$2" --username "$3" --scripts "$4"

cd $1
rm -r simple_job_predictions/ morgan_1024_predictions/
echo Done