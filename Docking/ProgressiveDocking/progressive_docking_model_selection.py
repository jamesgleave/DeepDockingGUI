"""
V 1.0.0
"""
import argparse
import glob
import os
import random
import sys
import time

import numpy as np
import pandas as pd
from tensorflow.keras.callbacks import Callback
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.metrics import auc
from sklearn.metrics import precision_recall_curve, roc_curve

from Docking.ML import *
from Docking.ML.DDMetrics import precision, f1

START_TIME = time.time()
print("Parsing args...")
parser = argparse.ArgumentParser()
parser.add_argument('-cf', '--cf', required=True)
parser.add_argument('-n_it', '--n_it', required=True)
parser.add_argument('-t_mol', '--t_mol', required=True)
parser.add_argument('-bs', '--bs', required=True)
parser.add_argument('-os', '--os', required=True)
parser.add_argument('-f_path', '--file_path', required=True)
parser.add_argument('-model_path', required=True)


# allowing for variable number of molecules to train from:
parser.add_argument('-n_mol', '--number_mol', required=False, default=1_000_000)
parser.add_argument('-cont', '--continuous', required=False, action='store_true')   # Using binary or continuous labels
parser.add_argument('-smile', '--smiles', required=False, action='store_true')      # Using smiles or morgan as or continuous labels
parser.add_argument('-norm', '--normalization', required=False, action='store_false')   # if continuous labels are used -> normalize them?


io_args = parser.parse_args()

print(sys.argv)

cf = float(io_args.cf)
n_it = int(io_args.n_it)
bs = int(io_args.bs)
oss = int(io_args.os)
t_mol = float(io_args.t_mol)
file_path = io_args.file_path
model_path = io_args.model_path


CONTINUOUS = False
NORMALIZE = False
SMILES = False
num_molec = 1_000_000

iter_path = file_path + '/iteration_'
print("Changing the itr path to",
      '/groups/cherkasvgrp/share/progressive_docking/nCoV/mpro_40B/biggest_docking_job_ever/iteration_')

new_iter_path = '/groups/cherkasvgrp/share/progressive_docking/nCoV/mpro_40B/biggest_docking_job_ever/iteration_'

print("Finished parsing args...")


def encode_smiles(series):
    print("Encoding smiles")
    # parameter is a pd.series with ZINC_IDs as the indicies and smiles as the elements
    encoded_smiles = DDModel.process_smiles(series.values, 100, fit_range=100, use_padding=True, normalize=True)
    encoded_dict = dict(zip(series.keys(), encoded_smiles))
    # returns a dict array of the smiles.
    return encoded_dict


def get_oversampled_smiles(Oversampled_zid, smiles_series):
    # Must return a dictionary where the keys are the zids and the items are
    # numpy ndarrys with n numbers of the same encoded smile
    # the n comes from the number of times that particular zid was chosen at random.
    oversampled_smiles = {}
    encoded_smiles = encode_smiles(smiles_series)

    for key in Oversampled_zid.keys():
        smile = encoded_smiles[key]
        oversampled_smiles[key] = np.repeat([smile], Oversampled_zid[key], axis=0)
    return oversampled_smiles


def get_oversampled_morgan(Oversampled_zid, fname):
    print('x data from:', fname)
    # Gets only the morgan fingerprints of those randomly selected zinc ids
    with open(fname, 'r') as ref:
        for line in ref:
            tmp = line.rstrip().split(',')

            # only extracting those that were randomly selected
            if (tmp[0] in Oversampled_zid.keys()) and (type(Oversampled_zid[tmp[0]]) != np.ndarray):
                train_set = np.zeros([1, 1024])
                on_bit_vector = tmp[1:]

                for elem in on_bit_vector:
                    train_set[0, int(elem)] = 1

                # creates a n x 1024 numpy ndarray where n is the number of times that zinc id was randomly selected
                Oversampled_zid[tmp[0]] = np.repeat(train_set, Oversampled_zid[tmp[0]], axis=0)
    return Oversampled_zid


def get_morgan_and_scores(morgan_path, ID_labels: pd.Series):
    # ID_labels is a dataframe containing the zincIDs and their corresponding scores.
    morgan_set = np.zeros([num_molec, 1024], dtype=bool)  # using bool to save space
    morgan_ids = []

    print('x data from:', morgan_path)
    with open(morgan_path, 'r') as ref:
        line_no = 0
        for line in ref:
            if line_no >= num_molec:
                break

            mol_info = line.rstrip().split(',')
            morgan_ids.append(mol_info[0])

            # "Decompressing" the information from the file about where the 1s are on the 1024 bit vector.
            bit_indicies = mol_info[
                           1:]  # array of indexes of the binary 1s in the 1024 bit vector representing the morgan fingerprint
            for elem in bit_indicies:
                morgan_set[line_no, int(elem)] = 1

            line_no += 1

    morgan_set = morgan_set[:line_no, :]

    print('Done...')
    morgan_pd = pd.DataFrame(data=morgan_set, dtype=np.uint8)
    morgan_pd['ZINC_ID'] = morgan_ids

    ID_labels = ID_labels.to_frame()
    print(ID_labels.columns)
    score_col = ID_labels.columns.difference(['ZINC_ID'])[0]
    print(score_col)

    morgan_data = pd.merge(ID_labels, morgan_pd, how='inner', on=['ZINC_ID'])
    X_morgan = morgan_data[morgan_data.columns.difference(['ZINC_ID', score_col])].values  # input
    y_labels = morgan_data[[score_col]].values  # labels
    return X_morgan, y_labels


# Gets the labels data
def get_data(smiles_path, morgan_path, labels_path) -> pd.DataFrame:
    # Loading the docking scores (with corresponding Zinc_IDs)
    labels = pd.read_csv(labels_path, sep=',', header=0)

    # Merging and setting index to the ID if smiles flag is set
    if SMILES:
        smiles = pd.read_csv(smiles_path, sep=' ', names=['smile', 'ZINC_ID'])
        data = smiles.merge(labels, on='ZINC_ID')
    else:
        morgan = pd.read_csv(morgan_path, usecols=[0], header=0, names=['ZINC_ID'])  # reading in only the zinc ids
        data = morgan.merge(labels, on='ZINC_ID')
    data.set_index('ZINC_ID', inplace=True)
    return data


n_iteration = n_it
total_mols = t_mol

try:
    os.mkdir(iter_path + str(n_iteration) + '/all_models')
except OSError:
    pass

# Getting data from prev iterations and this iteration
data_from_prev = pd.DataFrame()
train_data = pd.DataFrame()
test_data = pd.DataFrame()
valid_data = pd.DataFrame()
y_valid_first = pd.DataFrame()
y_test_first = pd.DataFrame()
for i in range(1, n_iteration + 1):

    # getting all the data
    print("\nGetting data from iteration", i)
    smiles_path = new_iter_path + str(i) + '/smile/{}_smiles_final_updated.smi'
    morgan_path = new_iter_path + str(i) + '/morgan/{}_morgan_1024_updated.csv'
    labels_path = new_iter_path + str(i) + '/{}_labels.txt'

    # Resulting dataframe will have cols of smiles (if selected) and docking scores with an index of Zinc IDs
    train_data = get_data(smiles_path.format('train'), morgan_path.format('train'), labels_path.format('training'))
    test_data = get_data(smiles_path.format('test'), morgan_path.format('test'), labels_path.format('testing'))
    valid_data = get_data(smiles_path.format('valid'), morgan_path.format('valid'), labels_path.format('validation'))

    print("Data acquired...")
    print("Train shape:", train_data.shape, "Valid shape:", valid_data.shape, "Test shape:", test_data.shape)

    if i == n_iteration:
        break  # not adding the current iteration data to the data_from_prev variable

    if i == 1:  # for the first iteration we only add the training data
        # because test and valid from this iteration is used by all subsequent iterations (constant dataset).
        bin_valid = valid_data < cf
        print(int(bin_valid.sum()))  # printing out total number of "hits".

        y_test_first = test_data  # test and valid should be seperate from training dataset
        y_valid_first = valid_data
        y_old = train_data
    else:
        y_old = pd.concat([train_data, valid_data, test_data], axis=0)

    data_from_prev = pd.concat([y_old, data_from_prev], axis=0)

    print("Data Augmentation iteration {} data shape: {}".format(i, data_from_prev.shape))

# Always using the same valid and test dataset across all iterations:
if n_iteration != 1:
    train_data = pd.concat([train_data, test_data, valid_data],
                           axis=0)  # These datasets are from the current iteration.
    valid_data = y_valid_first
    test_data = y_test_first

# Exiting if there are not enough hits
if (valid_data.r_i_docking_score < cf).values.sum() <= 10 or \
        (test_data.r_i_docking_score < cf).values.sum() <= 10:
    sys.exit()

# Finally combining all the datasets into a single training set:
train_data = pd.concat([train_data, data_from_prev])  # this won't do anything for the first iteration (duh)
print("Training labels shape: ", train_data.shape)

if CONTINUOUS:
    print('Using continuous labels...')
    y_valid = valid_data.r_i_docking_score
    y_test = test_data.r_i_docking_score
    y_train = train_data.r_i_docking_score

    if NORMALIZE:
        print('Adding cutoff to be normalized')
        cutoff_ser = pd.Series([cf], index=['cutoff'])
        y_train = y_train.append(cutoff_ser)

        print("Normalizing docking scores...")
        # Normalize the docking scores
        y_valid = DDModel.normalize(y_valid)
        y_test = DDModel.normalize(y_test)
        y_train = DDModel.normalize(y_train)

        print('Extracting normalized cutoff...')
        cf_norm = y_train['cutoff']
        y_train.drop(labels=['cutoff'], inplace=True)  # removing it from the dataset

        cf_to_use = cf_norm
    else:
        cf_to_use = cf

    # Getting all the ids of hits and non hits.
    y_pos = y_train[y_train < cf_to_use]
    y_neg = y_train[y_train >= cf_to_use]

else:
    print('Using binary labels...')
    y_valid = valid_data.r_i_docking_score < cf  # This will be from the first iteration
    y_test = test_data.r_i_docking_score < cf  # ^^
    y_train = train_data.r_i_docking_score < cf

    # Getting all the ids of hits and non hits.
    y_pos = y_train[y_train == 1]  # true
    y_neg = y_train[y_train == 0]  # false

print('Converting y_pos and y_neg to dict (for faster access time)')
y_pos = y_pos.to_dict()
y_neg = y_neg.to_dict()

num_neg = len(y_neg)
num_pos = len(y_pos)

print('number of negatives', num_neg)
print('number of positives', num_pos)
print('Training size:', num_pos + num_neg)
# sample_size = np.min([num_neg, num_pos * oss])
sample_size = 500_000

print("\nOversampling...", "size:", sample_size)
Oversampled_zid = {}  # Keeps track of how many times that zinc_id is randomly selected
Oversampled_zid_y = {}

pos_keys = list(y_pos.keys())
neg_keys = list(y_neg.keys())

for i in range(sample_size):
    # Randomly sampling equal number of hits and misses:
    idx = random.randint(0, num_pos - 1)
    idx_neg = random.randint(0, num_neg - 1)
    pos_zid = pos_keys[idx]
    neg_zid = neg_keys[idx_neg]

    # Adding both pos and neg to the dictionary
    try:
        Oversampled_zid[pos_zid] += 1
    except KeyError:
        Oversampled_zid[pos_zid] = 1
        Oversampled_zid_y[pos_zid] = y_pos[pos_zid]

    try:
        Oversampled_zid[neg_zid] += 1
    except KeyError:
        Oversampled_zid[neg_zid] = 1
        Oversampled_zid_y[neg_zid] = y_neg[neg_zid]

# Getting the inputs
if SMILES:
    print("Using smiles...")
    X_valid, y_valid = np.array(encode_smiles(valid_data.smile).values()), y_valid.to_numpy()
    X_test, y_test = np.array(encode_smiles(test_data).values()), y_test.to_numpy()

    # The training data needs to be oversampled:
    print("Getting oversampled smiles...")
    Oversampled_zid = get_oversampled_smiles(Oversampled_zid, train_data.smile)
    Oversampled_X_train = np.zeros([sample_size * 2, len(list(Oversampled_zid.values())[0][0])])
    print(len(list(Oversampled_zid.values())[0]))
else:
    Oversampled_X_train = np.zeros([sample_size * 2, 1024])
    print('Using morgan fingerprints...')
    # this part is what gets the morgan fingerprints:
    print('looking through file path:', new_iter_path + str(n_iteration) + '/morgan/*')
    for i in range(1, n_iteration + 1):
        for f in glob.glob(new_iter_path + str(i) + '/morgan/*'):
            set_name = f.split('/')[-1].split('_')[0]
            print('\t', set_name)
            # Valid and test datasets are always going to be from the first iteration.
            if i == 1:
                if set_name == 'valid':
                    X_valid, y_valid = get_morgan_and_scores(f, y_valid)  # this will always be y_valid_first
                elif set_name == 'test':
                    X_test, y_test = get_morgan_and_scores(f, y_test)

            # Fills the dictionary with the actual morgan fingerprints
            Oversampled_zid = get_oversampled_morgan(Oversampled_zid, f)

print("y validation shape:", y_valid.shape)

ct = 0
Oversampled_y_train = np.zeros([sample_size * 2, 1])
print("oversampled sample:", list(Oversampled_zid.items())[0])
num_morgan_missing = 0
for key in Oversampled_zid.keys():
    try:
        tt = len(Oversampled_zid[key])
    except TypeError as e:
        # print("Missing morgan fingerprint for this ZINC ID")
        # print(key, Oversampled_zid[key])
        num_morgan_missing += 1
        continue  # Skipping data that has no labels for it

    Oversampled_X_train[ct:ct + tt] = Oversampled_zid[
        key]  # repeating the same data for as many times as it was selected
    Oversampled_y_train[ct:ct + tt] = Oversampled_zid_y[key]
    ct += tt

print("Done oversampling, number of missing morgan fingerprints:", num_morgan_missing)


class TimedStopping(Callback):
    '''
    Stop training when enough time has passed.
    # Arguments
        seconds: maximum time before stopping.
        verbose: verbosity mode.
    '''

    def __init__(self, seconds=None, verbose=1):
        super(Callback, self).__init__()

        self.start_time = 0
        self.seconds = seconds
        self.verbose = verbose

    def on_train_begin(self, logs={}):
        self.start_time = time.time()

    def on_epoch_end(self, epoch, logs={}):
        print('epoch done')
        if time.time() - self.start_time > self.seconds:
            self.model.stop_training = True
            if self.verbose:
                print('Stopping after %s seconds.' % self.seconds)


print("Data prep time:", time.time() - START_TIME)
print("Configuring model...")

# This is our new model

print("\n" + "-" * 20)
print("Training data info:" + "\n")
print("X Data Shape[1:]", Oversampled_X_train.shape[1:])
print("X Data Shape", Oversampled_X_train.shape)
print("X Data example", Oversampled_X_train[0])

num_hit_in_val = 0
for v in y_valid:
    if v:
        num_hit_in_val += 1
print("Hit % in validation data:", (num_hit_in_val/len(y_valid) * 100, "%"))


name = os.path.basename(model_path).replace(".json", "")
progressive_docking = DDModel.load(model_path,
                                   metrics=['accuracy', precision, f1],
                                   name=name)
progressive_docking.model.summary()

# If there was a class weight with the model then set it else 1
try:
    wt = progressive_docking.hyperparameters['class_weight']
except KeyError:
    wt = 1

es = EarlyStopping(monitor='val_f1', min_delta=0, patience=5, verbose=0, mode='auto')
es1 = TimedStopping(seconds=10800)
cw = {0: 2, 1: 1}  # Just swapped the weight values to test

delta_time = time.time()
num_epochs = 40  # 500

progressive_docking.fit(Oversampled_X_train, Oversampled_y_train, epochs=num_epochs, batch_size=bs, shuffle=True,
                        class_weight=cw, verbose=1, validation_data=(X_valid, y_valid), callbacks=[es, es1])

# Delta time records how long a model takes to train num_epochs amount of epochs
delta_time = time.time() - delta_time
print("Training Time:", delta_time)

# keeping track of what model number this currently is and saving
try:
    with open(iter_path + str(n_iteration) + '/model_no.txt', 'r') as ref:
        mn = int(ref.readline().rstrip()) + 1
    with open(iter_path + str(n_iteration) + '/model_no.txt', 'w') as ref:
        ref.write(str(mn))

except IOError:  # file doesnt exist yet
    mn = 1
    with open(iter_path + str(n_iteration) + '/model_no.txt', 'w') as ref:
        ref.write(str(mn))
print("Saving the model...")
progressive_docking.save(iter_path + str(n_iteration) + '/all_models/model_' + str(mn))

print('Predicting on validation data')
prediction_valid = progressive_docking.predict(X_valid)

print('Predicting on testing data')
prediction_test = progressive_docking.predict(X_test)

if CONTINUOUS:
    # Converting back to binary values to get stats
    y_valid = y_valid < cf_to_use
    prediction_valid = prediction_valid < cf_to_use
    y_test = y_test < cf_to_use
    prediction_test = prediction_test < cf_to_use

print('Getting stats from predictions...')
# Getting stats for validation
precision_vl, recall_vl, thresholds_vl = precision_recall_curve(y_valid, prediction_valid)
fpr_vl, tpr_vl, thresh_vl = roc_curve(y_valid, prediction_valid)
auc_vl = auc(fpr_vl, tpr_vl)
pr_vl = precision_vl[np.where(recall_vl > 0.9)[0][-1]]
pos_ct_orig = np.sum(y_valid)
Total_left = 0.9 * pos_ct_orig / pr_vl * total_mols * 1000000 / len(y_valid)
tr = thresholds_vl[np.where(recall_vl > 0.90)[0][-1]]

# Getting stats for testing
precision_te, recall_te, thresholds_te = precision_recall_curve(y_test, prediction_test)
fpr_te, tpr_te, thresh_te = roc_curve(y_test, prediction_test)
auc_te = auc(fpr_te, tpr_te)
pr_te = precision_te[np.where(thresholds_te > tr)[0][0]]
re_te = recall_te[np.where(thresholds_te > tr)[0][0]]
pos_ct_orig = np.sum(y_test)
Total_left_te = re_te * pos_ct_orig / pr_te * total_mols * 1000000 / len(y_test)

with open(iter_path + str(n_iteration) + '/hyperparameter_morgan_with_freq_v3.csv', 'a') as ref:
    ref.write(str(mn) + ',' + str(oss) + ',' + str(bs)
              + ',' + str(progressive_docking.hyperparameters['learning_rate'])
              + ',' + str(progressive_docking.hyperparameters['num_units'])
              + ',' + str(progressive_docking.hyperparameters['dropout_rate'])
              + ',' + str(wt)
              + ',' + str(cf)
              + ',' + str(auc_vl)
              + ',' + str(pr_vl)
              + ',' + str(Total_left)
              + ',' + str(auc_te)
              + ',' + str(pr_te)
              + ',' + str(re_te)
              + ',' + str(Total_left_te)
              + ',' + str(pos_ct_orig) + '\n')

with open(iter_path + str(n_iteration) + '/hyperparameter_morgan_with_freq_v3.txt', 'a') as ref:
    # The sting of hyperparameters that stores what will be appended to the file ref
    hp = "\n" + "-" * 15 + "\n" + "Hyperparameters:" + "\n"
    hp += "- Model Number: " + str(mn) + "\n"
    hp += "- Model Name: " + str(name) + "\n"
    hp += "- Training Time: " + str(round(delta_time, 3)) + "\n"
    hp += "  - OS: " + str(oss) + "\n"
    hp += "  - Batch Size: " + str(bs) + "\n"
    hp += "  - Learning Rate: " + str(progressive_docking.hyperparameters['learning_rate']) + "\n"
    hp += "  - Num. Units: " + str(progressive_docking.hyperparameters['num_units']) + "\n"
    hp += "  - Dropout Freq.: " + str(progressive_docking.hyperparameters['dropout_rate']) + "\n" * 2

    hp += "  - Class Weight Parameter wt: " + str(wt) + "\n"
    hp += "  - cf: " + str(cf) + "\n"
    hp += "  - auc vl: " + str(auc_vl) + "\n"
    hp += "  - auc te: " + str(auc_te) + "\n"
    hp += "  - Precision validation: " + str(pr_vl) + "\n"
    hp += "  - Precision testing: " + str(pr_te) + "\n"
    hp += "  - Recall testing: " + str(re_te) + "\n"
    hp += "  - Pos ct orig: " + str(pos_ct_orig) + "\n"
    hp += "  - Total Left: " + str(Total_left) + "\n"
    hp += "  - Total Left testing: " + str(Total_left_te) + "\n\n"

    hp += "-" * 15
    ref.write(hp)

print("Model number", mn, "complete.")
