echo Resetting Phase 4 on $(basename $1)...

# Remove the slurm files associated with the project
python3 reset.py --project_name "$2" --username "$3" --scripts "$4"

# Move into the project
cd $1

rm -r all_models hyperparameter* model_no.txt morgan_1024_predictions simple_job*
rm -r best_model*
rm testing* validation* training*
