from multiprocessing import Pool
from contextlib import closing
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
    __builtin__.print('\t molecular_file_count_updated: ', end="")
    return __builtin__.print(*args, **kwargs)

def write_mol_count_list(file_name, mol_count_list):
    with open(file_name,'w') as ref:
        for ct,file_name in mol_count_list:
            ref.write(str(ct)+","+file_name.split('/')[-1])
            ref.write("\n")


def molecule_count(file_name):
    temp = 0
    with open(file_name,'r') as ref:
        ref.readline()
        for line in ref:
            temp+=1
    return temp, file_name


if __name__=='__main__': 
    parser = argparse.ArgumentParser()
    parser.add_argument('-pt','--protein_name',required=True)
    parser.add_argument('-it','--n_iteration',required=True)
    parser.add_argument('-cdd','--data_directory',required=True)
    parser.add_argument('-cpd','--project_directory',required=True)
    parser.add_argument('-t_pos','--tot_process',required=True)
    parser.add_argument('-t_samp','--tot_sampling',required=True)
    io_args = parser.parse_args()

    protein = io_args.protein_name
    n_it = int(io_args.n_iteration)
    data_directory = io_args.data_directory
    project_directory = io_args.project_directory
    tot_process = int(io_args.tot_process)
    Total_sampling = int(io_args.tot_sampling)

    print("Parsed Args:")
    print(" - Iteration:", n_it)
    print(" - Data Directory:", data_directory)
    print(" - Num process nodes:", tot_process)
    print(" - Total Sampling:", Total_sampling)

    # Creating Mol_ct_file.csv if not already created 
    if not os.path.exists(project_directory + "/Mol_ct_file.csv"):
        files = []
        # saving the files:
        for f in glob.glob(data_directory+'/*.txt'):
            files.append(f)
        print("Number Of Files:", len(files))

        t=time.time()
        print("Reading Files...")
        # Counting num of molecules in each file
        with closing(Pool(np.min([tot_process,len(files)]))) as pool:
            mol_count = pool.map(molecule_count, files)
        print("Done Reading Files - Time Taken", time.time()-t)

        print("Saving File Count...") # as a Mol_ct_file.csv
        try:
            write_mol_count_list(project_directory + "/Mol_ct_file.csv", mol_count)
        except PermissionError:
            print("Mol_ct_file.csv already created by other user")

    # Creating Mol_ct_file_updated.csv if not already created (project specific)
    if not os.path.exists(project_directory + "/Mol_ct_file_updated.csv"):
        mol_ct = pd.read_csv(project_directory+'/Mol_ct_file.csv',header=None)
        mol_ct.columns = ['Number_of_Molecules','file_name']

        Total_mols_available = np.sum(mol_ct.Number_of_Molecules)
        mol_ct['Sample_for_million'] = [int(Total_sampling/Total_mols_available*elem) for elem in mol_ct.Number_of_Molecules]
        
        mol_ct.to_csv(project_directory+'/Mol_ct_file_updated.csv',sep=',',index=False)
        print("Done - Time Taken", time.time()-t)