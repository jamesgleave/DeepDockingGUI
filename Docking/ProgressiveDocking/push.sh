cd /groups/cherkasvgrp/share/progressive_docking/development/pd_python_pose/
dest=../pd_python_pose_v2/DD_dev_slurm/

files=('phase_4.sh' 'Extract_labels.py' 'simple_job_models.py' 'jobid_writer.py' 'phase_5.sh' 'hyperparameter_result_evaluation.py' 'simple_job_predictions.py')

for f in "${files[@]}"; do
	cp -i $f $dest
done 

# Adding commiting then pushing the modified files
cd $dest

for f in "${files[@]}"; do
	git add $f
done

git commit -m "Updates from remote"
git push
