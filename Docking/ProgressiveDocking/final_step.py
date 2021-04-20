from multiprocessing import Pool
from contextlib import closing
import pandas as pd
import numpy as np
import argparse
import gzip
import glob
import os

# Grab the args
parser = argparse.ArgumentParser()
parser.add_argument('-pt', '--protein_name', required=True)
parser.add_argument('-fp', '--file_path', required=True)
parser.add_argument('-it', '--n_iteration', required=True)
parser.add_argument('-t_pos', '--tot_process', required=True)
io_args = parser.parse_args()

# Set out globals
protein = io_args.protein_name
file_path = io_args.file_path
n_it = int(io_args.n_iteration)
tot_process = int(io_args.tot_process)


def get_z_ids(data):
    # Grabs the mol-id and put them into a dictionary
    sdfname, i, fname = data
    zids = {}
    for key in pd.read_csv(fname).ZINC_ID:
        zids[key] = 0
    return [sdfname, i, zids]


def get_pred_zids(fname):
    zids = {}
    with open(fname, 'r') as ref:
        for line in ref:
            zids[line.rstrip().split(',')[0]] = 1
    return zids


def get_mol_from_zid(data):
    # Decompose the data parameter
    sdfname, i, zids = data
    # Get the name of the sdf file
    name = sdfname.split('/')[-1].split('.')[0]

    # Create a zip file and write to is
    ref1 = gzip.open(file_path + '/' + protein + '/after_iteration/already_docked/' + name + '_' + str(i) + '.sdf.gz',
                     'wb')

    try:
        # Writing to the zip file...
        with gzip.open(sdfname, 'rb') as ref:
            # Loop through the lines in the sdf file
            for line in ref:
                # Decode the line and strip it of white spaces
                tmp = line.decode('utf-8').strip()
                # Check if the id is in the ids list
                if tmp in zids:
                    if zids[tmp] == 0:
                        zids[tmp] += 1
                        ref1.write(line)
                        for lines in ref:
                            ref1.write(lines)
                            if lines.decode('utf-8')[:4] == '$$$$':
                                break
                    else:
                        for lines in ref:
                            if lines.decode('utf-8')[:4] == '$$$$':
                                break
                else:
                    for lines in ref:
                        if lines.decode('utf-8')[:4] == '$$$$':
                            break
    except OSError:
        print("File not zipped, reading normally...")
        with open(sdfname, 'rb') as ref:
            for line in ref:
                tmp = line.decode('utf-8').strip()
                if tmp in zids:
                    if zids[tmp] == 0:
                        zids[tmp] += 1
                        ref1.write(line)
                        for lines in ref:
                            ref1.write(lines)
                            if lines.decode('utf-8')[:4] == '$$$$':
                                break
                    else:
                        for lines in ref:
                            if lines.decode('utf-8')[:4] == '$$$$':
                                break
                else:
                    for lines in ref:
                        if lines.decode('utf-8')[:4] == '$$$$':
                            break

    ref1.close()


if __name__ == '__main__':

    # Here we loop through each iteration and check if the molecules have been docked already...
    all_predocked = []
    for i in range(1, n_it + 1):
        for f in glob.glob(file_path + '/' + protein + '/' + 'iteration_' + str(i) + '/docked/*.sdf*'):

            # isolate the train, valid, or test term...
            if 'test' in os.path.basename(f):
                name = 'testing'
            elif 'valid' in os.path.basename(f):
                name = 'validation'
            elif 'train' in os.path.basename(f):
                name = 'training'
            else:
                print("Could not generate new training set")
                exit()

            # Grab the training, validation, and testing labels
            g = file_path + '/' + protein + '/' + 'iteration_' + str(i) + '/' + name + '_labels.txt'

            # Add them to the list containing molecules that have been previously docked = [file, iteration, labels]
            all_predocked.append([f, i, g])

    # multiprocess pool the get_z_ids func
    with closing(Pool(np.min([len(all_predocked), tot_process]))) as pool:
        returned = pool.map(get_z_ids, all_predocked)

    # Get rid of all cross over
    for i in range(len(returned)):
        for j in range(i + 1, len(returned)):
            for keys in returned[i][-1].keys():
                if keys in returned[j][-1].keys():
                    returned[j][-1].pop(keys)

    # Go through all predicted files and do the same as above
    all_files_predicted = []
    for f in glob.glob(file_path + '/' + protein + '/' + 'iteration_' + str(n_it) + '/morgan_1024_predictions/*.txt'):
        all_files_predicted.append(f)

    with closing(Pool(np.min([len(all_files_predicted), tot_process]))) as pool:
        returned_predicted = pool.map(get_pred_zids, all_files_predicted)
    all_predicted = {}
    for i in range(len(returned_predicted)):
        for key in returned_predicted[i].keys():
            all_predicted[key] = 0

    for i in range(len(returned)):
        tmp = {}
        for keys in returned[i][-1].keys():
            if keys in all_predicted:
                all_predicted.pop(keys)
                tmp[keys] = 0
        returned[i][-1] = tmp

    # Create all directories used in the final steps
    tmp = []
    try:
        os.mkdir(file_path + '/' + protein + '/after_iteration')
    except OSError:
        pass

    try:
        os.mkdir(file_path + '/' + protein + '/after_iteration/to_dock')
    except OSError:
        pass

    try:
        os.mkdir(file_path + '/' + protein + '/after_iteration/already_docked')
    except OSError:
        pass

    # Write to docked values to a file
    with closing(Pool(np.min([len(returned), tot_process]))) as pool:
        pool.map(get_mol_from_zid, returned)

    # Reinitialize the returned list?
    returned = []

    cnt = 1
    ref = open(file_path + '/' + protein + '/after_iteration/to_dock/to_dock_' + str(cnt) + '.txt', 'w')
    for i, keys in enumerate(all_predicted):
        # Number of molecules at the end...
        ref.write(keys + '\n')
        if i % 999999 == 0 and i != 0:
            ref.close()
            cnt += 1
            ref = open(file_path + '/' + protein + '/after_iteration/to_dock/to_dock_' + str(cnt) + '.txt', 'w')
    try:
        ref.close()
    except:
        pass
