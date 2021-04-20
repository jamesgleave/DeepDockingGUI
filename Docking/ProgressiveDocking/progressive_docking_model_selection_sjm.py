import argparse
import builtins as __builtin__
import glob
import os
import time

import numpy as np
import pandas as pd


# For debugging purposes only:
def print(*args, **kwargs):
    __builtin__.print('\t simple_jobs: ', end="")
    return __builtin__.print(*args, **kwargs)


START_TIME = time.time()
parser = argparse.ArgumentParser()
parser.add_argument('-n_it', '--iteration_no', required=True)
parser.add_argument('-mdd', '--morgan_directory', required=True)
parser.add_argument('-time', '--time', required=True)
parser.add_argument('-file_path', '--file_path', required=True)
parser.add_argument('-nhp', '--number_of_hyp', required=True)
parser.add_argument('-titr', '--total_iterations', required=True)
parser.add_argument('-model_dir', required=True)

parser.add_argument('-isl', '--is_last', required=False, action='store_true')

# allowing for variable number of molecules to train and vaildate from
parser.add_argument('-n_mol', '--number_mol', required=False, default=1_000_000)

parser.add_argument('-pfm', '--percent_first_mols', required=False, default=-1)  # these two inputs must be percentages
parser.add_argument('-plm', '--percent_last_mols', required=False, default=-1)

# Flag for switching between functions that determine how many mols to be left at the end of iteration
#   if not provided it defaults to a linear dec
funct_flags = parser.add_mutually_exclusive_group(required=False)
funct_flags.add_argument('-expdec', '--exponential_dec', required=False, default=-1)  # must pass in the base number
funct_flags.add_argument('-polydec', '--polynomial_dec', required=False,
                         default=-1)  # You must also pass in to what power for this flag

io_args, extra_args = parser.parse_known_args()
n_it = int(io_args.iteration_no)
mdd = io_args.morgan_directory
time_model = io_args.time
file_path_project = io_args.file_path  # Now == file_path/protein
file_path = '/groups/cherkasvgrp/share/progressive_docking/nCoV/mpro_40B/biggest_docking_job_ever'
nhp = int(io_args.number_of_hyp)
isl = io_args.is_last
titr = int(io_args.total_iterations)

num_molec = int(io_args.number_mol)

percent_first_mols = float(io_args.percent_first_mols)
percent_last_mols = float(io_args.percent_last_mols)

exponential_dec = int(io_args.exponential_dec)
polynomial_dec = int(io_args.polynomial_dec)

# sums the first column and divides it by 1 million
# is this the average score for the molecules? Why divide by 1000000?
# replace with => pd.to_numeric(df[0]).sum()  # returns a single number representing the sum
t_mol = pd.read_csv(mdd + '/Mol_ct_file.csv', header=None)[[0]].sum()[
            0] / 1000000  # num of compounds in each file is mol_ct_file

try:
    os.mkdir(file_path_project + '/iteration_' + str(n_it) + '/simple_job')
except OSError:  # catching file exists error
    pass

# Clearing up space from previous iteration
for f in glob.glob(file_path_project + '/iteration_' + str(n_it) + '/simple_job/*'):
    os.remove(f)

scores_val = []
with open(file_path + '/iteration_' + str(1) + '/validation_labels.txt', 'r') as ref:
    ref.readline()  # first line is ignored
    for line in ref:
        scores_val.append(float(line.rstrip().split(',')[0]))

scores_val = np.array(scores_val)

first_mols = int(100 * t_mol / 13) if percent_first_mols == -1 else int(percent_first_mols * len(scores_val))

if n_it == 1:
    # 'good_mol' is the number of top scoring molecules to save at the end of the iteration
    good_mol = first_mols
else:
    if exponential_dec != -1:
        good_mol = int()  # TODO: create functions for these
    elif polynomial_dec != -1:
        good_mol = int()
    else:
        good_mol = int(((100 - first_mols) * n_it + titr * first_mols - 100) / (
                    titr - 1))  # linear decrease as interations increase

print(isl)
# If this is the last iteration then we save only 100 molecules
if isl:
    # 100 mols is 0.0001% of an inital of 1 million input molecules
    good_mol = 100 if percent_last_mols == -1 else int(percent_last_mols * len(scores_val))

cf_start = np.mean(scores_val)  # the mean of all the docking scores (labels) of the validation set:
t_good = len(scores_val)

# we decrease the threshold value until we have our desired num of mol left.
while t_good > good_mol:
    cf_start -= 0.005
    t_good = len(scores_val[scores_val < cf_start])

print('Threshold (cutoff):', cf_start)
print('Molec under threshold:', t_good)
print('Goal molec:', good_mol)
print('Total molec:', len(scores_val))

ct = 1  # The current job number
# Creating all the jobs for each hyperparameter combination:
other_args = ' '.join(extra_args) + ' -n_it {} -t_mol {} --file_path {} -n_mol {}'.format(n_it, t_mol, file_path_project, num_molec)
pd_python_pose = '/groups/cherkasvgrp/share/progressive_docking/development/pd_python_pose'
pd_python_pose_v2 = '/groups/cherkasvgrp/share/progressive_docking/development/pd_python_pose_v2/DD_dev_slurm/\n'
activation = 'source /home/jgleave/.conda/envs/keras_tuning/bin/activate\n'


# Gather all of the models
models = []
model_dir = io_args.model_dir
files = os.listdir(model_dir)

print("Creating Simple Jobs:")
# cf_start = -10.031905770759012
for file in files:
    if 'json' in file:
        print("- Creating job file for", file)
        with open(file_path_project + '/iteration_' + str(n_it) + '/simple_job/simple_job_' + str(ct) + '.sh', 'w') as ref:
            ref.write('#!/bin/bash\n')
            ref.write('#SBATCH --ntasks=1\n')
            ref.write('#SBATCH --gres=gpu:1\n')
            ref.write('#SBATCH --cpus-per-task=1\n')
            ref.write('#SBATCH --job-name=phase_4\n')
            ref.write('#SBATCH --mem=0               # memory per node\n')
            ref.write('#SBATCH --time=' + time_model + '            # time (DD-HH:MM)\n')
            ref.write('\n')
            ref.write('cd {}'.format(pd_python_pose_v2))
            ref.write(activation)
            hyp_args = '-os {} -bs {} -cf {}'.\
                format(10, 256, cf_start)
            ref.write('python -u progressive_docking_model_selection.py '
                      + hyp_args + ' '
                      + other_args
                      + ' -model_path ' + model_dir + "/" + file)
        ct += 1

print('Runtime:', time.time() - START_TIME)
