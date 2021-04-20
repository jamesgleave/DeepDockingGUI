from multiprocessing import Pool
from contextlib import closing
import pandas as pd
import os
try:
    import __builtin__
except ImportError:
    # Python 3
    import builtins as __builtin__

# For debugging purposes only:
def print(*args, **kwargs):
    __builtin__.print('\t fast top hit search: ', end="")
    return __builtin__.print(*args, **kwargs)


def find_top_n_predicted_molecules(file_path):
    # Search through the predicted morgan files and find the top hits
    n = search_size
    n = min(100, n)  # Cap the number of molecules to 100

    # Read the CSV and extract the top hits
    df = pd.read_csv(file_path, names=['id', "score", ])
    top_n = df.nlargest(n, "score")

    # return a series of the top n predictions as a value in a dictionary where the key is the file it was found in
    return os.path.basename(file_path), top_n


def find_matching_smiles(smile_database_path, file_path, search_dict):
    # Grab the targets we are looking for
    targets = search_dict[file_path]['id'].tolist()
    print("Debug: This process is searching for", targets, "in file", file_path)

    # Read the smile file corresponding to the predictions
    smile_file = os.path.join(smile_database_path, os.path.basename(file_path))
    df = pd.read_csv(smile_file, delimiter=" ", index_col=1)

    # Loop through the targets and check if it is found in the file
    with open("top_hits.csv", "a") as top_hits:
        for target in targets:
            if target in df.index:
                print("Found target:", target)
                found_smile = df.loc[target, 'smiles']
                # Write to the top_hits.csv file as: smile,id,score
                top_hits.write(found_smile + "," + target + "\n")


if __name__ == '__main__':
    import argparse
    args = argparse.ArgumentParser()
    args.add_argument("-sdb", "--smile_database", required=True)
    args.add_argument("-pdb", "--predicted_database", required=True)
    args.add_argument("-tp", "--total_processors", required=True, type=int)
    args.add_argument("-n", required=True, type=int)
    info = args.parse_args()

    # Get the search size for each process
    prediction_files = [os.path.join(info.predicted_database, f) for f in os.listdir(info.predicted_database) if 'smile' in f]
    num_prediction_files = len(prediction_files)
    search_size = round(info.n/num_prediction_files)
    num_processes = min([info.total_processors, num_prediction_files])

    # Make sure we have the prediction files
    assert os.path.exists(info.predicted_database), print("Phase 5 Incomplete...")
    with open("top_hits.csv", "w") as init_top_hits:
        init_top_hits.write("smile,id\n")

    print("Starting search...")
    print("We have the following arguments passed:")
    print("  - Number of files to search:", num_prediction_files)
    print("  - Number of molecules to find:", info.n)
    print("  - Search size:", search_size)
    print("  - Number of processes:", num_processes)
    print("  - Smile database:", info.smile_database)
    print("  - Predicted database:", info.predicted_database)

    print("Finding top predictions")
    # Search for the top predicted hits
    with closing(Pool(num_processes)) as pool:
        predicted = pool.map(find_top_n_predicted_molecules, prediction_files)
    print("  - Done")

    # Arrange all of the top predictions into a dictionary indexed by their file name
    search = {}
    print("Finding top smiles")
    for top_list in predicted:
        # {os.path.basename(file_path): top_n}
        file_name, predictions = top_list
        search[file_name] = predictions

    # Generate the args for the multiprocessing
    mp_args = []
    for key in search.keys():
        mp_args.append((info.smile_database, key, search))

    # Start searching for the top hits from the smile database
    with closing(Pool(num_processes)) as pool:
        pool.starmap(find_matching_smiles, mp_args)
    print("  - Done")

