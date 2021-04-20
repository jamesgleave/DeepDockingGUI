cd /groups/cherkasvgrp/share/progressive_docking/development/pd_python_pose_v2/DD_dev_slurm/
dest=../../pd_python_pose/

git pull

# Phase 4 updates:
cp -i phase_4.sh $dest
cp -i Extract_labels.py $dest
cp -i simple_job_models.py $dest
cp -i jobid_writer.py $dest
#cp -i progressive_docking.py $dest

# Phase 5 updates:
cp -i phase_5.sh $dest
cp -i hyperparameter_result_evaluation.py $dest
cp -i simple_job_predictions.py $dest
