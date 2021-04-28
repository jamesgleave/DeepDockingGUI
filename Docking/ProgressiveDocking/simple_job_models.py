import builtins as __builtin__
import pandas as pd
import numpy as np
import argparse
import glob
import time
import os

try:
    import __builtin__
except ImportError:
    # Python 3
    import builtins as __builtin__
    
# For debugging purposes only:
def print(*args, **kwargs):
    __builtin__.print('\t simple_jobs: ', end="")
    return __builtin__.print(*args, **kwargs)


START_TIME = time.time()


parser = argparse.ArgumentParser()
parser.add_argument('-n_it','--iteration_no',required=True)
parser.add_argument('-time','--time',required=True)
parser.add_argument('-file_path','--file_path',required=True)
parser.add_argument('-nhp','--number_of_hyp',required=True)
parser.add_argument('-titr','--total_iterations',required=True)

parser.add_argument('-isl','--is_last',required=False, action='store_true')

# adding parameter for where to save all the data to:
parser.add_argument('-save', '--save_path', required=False, default=None)

# allowing for variable number of molecules to test and validate from:
parser.add_argument('-n_mol', '--number_mol', required=False, default=1000000)

parser.add_argument('-pfm', '--percent_first_mols', required=False, default=-1)  # these two inputs must be percentages
parser.add_argument('-plm', '--percent_last_mols', required=False, default=-1)


# Pass the threshold
parser.add_argument('-ct', required=False, default=0.9)

# Flag for switching between functions that determine how many mols to be left at the end of iteration 
#   if not provided it defaults to a linear dec
funct_flags = parser.add_mutually_exclusive_group(required=False)
funct_flags.add_argument('-expdec', '--exponential_dec', required=False, default=-1) # must pass in the base number
funct_flags.add_argument('-polydec', '--polynomial_dec', required=False, default=-1) # You must also pass in to what power for this flag

# This determines whether or not you want to choose a continuous range of hyperparameters
parser.add_argument('-chp', '--continuous_hyperparameters', required=False, default=False, type=bool)

io_args, extra_args = parser.parse_known_args()
n_it = int(io_args.iteration_no)
time_model = io_args.time
nhp = int(io_args.number_of_hyp)
isl = io_args.is_last
titr = int(io_args.total_iterations)
ct = float(io_args.ct)

num_molec = int(io_args.number_mol)

percent_first_mols = float(io_args.percent_first_mols)
percent_last_mols = float(io_args.percent_last_mols)

exponential_dec = int(io_args.exponential_dec)
polynomial_dec = int(io_args.polynomial_dec)

dynamic_hyperparameters = io_args.continuous_hyperparameters

PROJECT_PATH = io_args.file_path   # Now == file_path/protein
SAVE_PATH = io_args.save_path
# if no save path is provided we just save it in the same location as the data
if SAVE_PATH is None: SAVE_PATH = PROJECT_PATH

# sums the first column and divides it by 1 million (the size of our dataset)
t_mol = pd.read_csv(PROJECT_PATH+'/Mol_ct_file.csv',header=None)[[0]].sum()[0]/1000000 # num of compounds in each file is mol_ct_file


"""
Hyperparameter information:
------------------------------------------------------------------------------------------------------------------------
Note that we have 7 hyperparameters that we can tune. 

1. num_units (number of neurons per layer)
2. dropout (dropout per layer)
3. learn_rate (model's learning rate)
4. bin_array (number of deep layers for model)
5. wt (class weight for training)
6. bs (batch size for training)
7. oss (over sample size for training)

Since the models are going to be a combination of these values, we have:
    * Let Hyperparameter Name = len(Hyperparameter Name) for simplicity:
        - Number of models = num_units * dropout * learn_rate * bin_array * wt * bs * oss

Since we have a number of hyperparameter predefined, we should create a range given the passed number of HPs
------------------------------------------------------------------------------------------------------------------------
"""

# Changes the way we create our hyperparameters
cummulative = 0.25 * n_it
if dynamic_hyperparameters:

    # len(num_units) <= num_values_per_hyperparameters
    num_values_per_hyperparameters = round(nhp ** (1/7))

    # Define ranges of hyperparameters
    unit_range = [100, 2000]
    dropout_range = [0.2, 0.5]
    learn_rate_range = [0.0001, 0.0001]
    bin_array_range = [2, 3]
    wt_range = [2, 3]
    bs_range = [128, 256]
    oss_range = [5, 20]

else:
    # Use predefined sizes
    num_units = [100, 1500, 2000]
    dropout = [0.2, 0.5]
    learn_rate = [0.0001]
    bin_array = [2, 3]
    wt = [2, 3]

    if nhp < 144:
       bs = [256]
    else:
        bs = [128, 256]

    if nhp < 48:
        oss = [10]
    elif nhp < 72:
        oss = [5, 10]
    else:
        oss = [5, 10, 20]

# Precalculate the number of models
number_of_models = len(num_units) * len(dropout) * len(learn_rate) * len(bin_array) * len(wt) * len(bs) * len(oss)
print("Number of models:", number_of_models)

try:
    os.mkdir(SAVE_PATH+'/iteration_'+str(n_it)+'/simple_job')
except OSError: # catching file exists error
    pass

# Clearing up space from previous iteration
for f in glob.glob(SAVE_PATH+'/iteration_'+str(n_it)+'/simple_job/*'):
    os.remove(f)

scores_val = []
with open(PROJECT_PATH+'/iteration_'+str(1)+'/validation_labels.txt','r') as ref:
    ref.readline()  # first line is ignored
    for line in ref:
        scores_val.append(float(line.rstrip().split(',')[0]))

scores_val = np.array(scores_val)

first_mols = int(100*t_mol/13) if percent_first_mols == -1.0 else int(percent_first_mols * len(scores_val))

if n_it==1:
    # 'good_mol' is the number of top scoring molecules to save at the end of the iteration
    good_mol = first_mols
else:
    if exponential_dec != -1:
        good_mol = int() #TODO: create functions for these
    elif polynomial_dec != -1:
        good_mol = int()
    else:
        good_mol = int(((100-first_mols)*n_it + titr*first_mols-100)/(titr-1))     # linear decrease as interations increase

# If this is the last iteration
if isl:
    # 100 mols is 0.0001% of an initial of 1 million input molecules
    good_mol = 100 if percent_last_mols == -1.0 else int(percent_last_mols * len(scores_val))

cf_start = np.mean(scores_val)  # the mean of all the docking scores (labels) of the validation set:
t_good = len(scores_val)

# we decrease the threshold value until we have our desired num of mol left.
while t_good > good_mol: 
    cf_start -= 0.005
    t_good = len(scores_val[scores_val<cf_start])

print('Threshold (cutoff):',cf_start)
print('Molec under threshold:', t_good)
print('Goal molec:', good_mol)
print('Total molec:', len(scores_val))

all_hyperparas = []
for o in oss:   # Over Sample Size
    for batch in bs:
        for nu in num_units:
            for do in dropout:
                for lr in learn_rate:
                    for ba in bin_array:
                        for w in wt:    # Weight
                            all_hyperparas.append([o,batch,nu,do,lr,ba,w,cf_start])

print('Total Hyperparameters:', len(all_hyperparas))
# Creating all the jobs for each hyperparameter combination:

other_args = ' '.join(extra_args) + ' -n_it {} -t_mol {} --data_path {} --save_path {} -n_mol {}'.format(n_it, t_mol, PROJECT_PATH, SAVE_PATH, num_molec)
print("Args:", other_args)
for i in range(len(all_hyperparas)):
    model_number = i + 1
    with open(SAVE_PATH+'/iteration_'+str(n_it)+'/simple_job/simple_job_'+str(model_number)+'.sh', 'w') as ref:
        ref.write('#!/bin/bash\n')
        ref.write('#SBATCH --ntasks=1\n')
        ref.write('#SBATCH --gres=gpu:1\n')
        ref.write('#SBATCH --cpus-per-task=1\n')
        ref.write('#SBATCH --job-name=phase_4\n')
        ref.write('#SBATCH --mem=0               # memory per node\n')
        ref.write('#SBATCH --time='+time_model+'            # time (DD-HH:MM)\n')

        # Reads the custom header file to add the custom headers and partition
        try:
            with open("custom_slurm_header.txt", "r") as custom_slurm_header:
                for line in custom_slurm_header.readlines():
                    ref.write(line)
        except OSError:
            pass

        ref.write("#SBATCH --output=slurm-phase_4-%x.%j.out\n")
        ref.write("#SBATCH --error=slurm-phase_4-%x.%j.err\n")
        ref.write('\n')

        cwd = os.getcwd()
        ref.write('cd {}\n'.format(cwd))
        ref.write('source ~/.bashrc\n')
        ref.write('source activation_script.sh\n')
        hyp_args = '-os {} -bs {} -num_units {} -dropout {} -learn_rate {} -bin_array {} -wt {} -cf {}'.format(*all_hyperparas[i])
        ref.write('python -u progressive_docking.py ' + hyp_args + ' ' + other_args + ' --model_number ' + str(model_number))
        ref.write("\n echo complete")


print('Runtime:', time.time() - START_TIME)
