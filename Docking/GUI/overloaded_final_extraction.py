from multiprocessing import Pool
from contextlib import closing
import multiprocessing
import pandas as pd
import argparse
import random
import glob
import sys
import os


def merge_on_smiles(pred_file):
    print("Merging " + os.path.basename(pred_file) + "...", end=" ")

    # Read the predictions
    pred = pd.read_csv(pred_file, names=["id", "score"], index_col=0)
    pred.drop_duplicates()

    # Read the smiles
    smile_file = os.path.join(args.smile_dir, os.path.basename(pred_file))
    smi = pd.read_csv(smile_file, delimiter=" ", names=["smile", "id"], index_col=1)
    smi = smi.drop_duplicates()

    # Merge on the IDs and sort by the score
    merged = pd.merge(pred, smi, how="inner", on=["id"])
    merged.sort_values(by="score", ascending=False, inplace=True)

    # Save to a csv as (mean_score)_(base_name).csv
    size = len(merged)
    file_name = "extracted_smiles/" + str(size) + "_" + os.path.basename(pred_file) + ".csv"
    merged.to_csv(file_name)
    print("Done")

    return file_name


def kinda_merge_sort(f):
    # Unpack
    n, f1, f2 = f
    if n is None:
        print("Merging", f1, "with", f2, " - Non Terminal")
    else:
        print("Merging", f1, "with", f2, " - Terminal")

    # Combine f1 and f2 then sort the dataframe
    combined = pd.concat([pd.read_csv(f1, index_col=0),
                          pd.read_csv(f2, index_col=0)])
    combined.sort_values(by="score", ascending=False, inplace=True)

    # Remove the two files
    os.remove(f1)
    os.remove(f2)

    # If it is the final merge then get the top_n and save to csv
    if n is not None and n != "all":
        # If n != "all", then we should not take all of the top hits...
        combined = combined.head(int(n))
        # We will finalize our extraction by separating our combined dataframe into two new ones
        finalize(combined)
        return ""
    elif n is not None and n == "all":
        # We will finalize our extraction by separating our combined dataframe into two new ones
        finalize(combined)
        return ""
    else:
        # If it is not the final merge iteration, merge as usual
        # Generate a random key
        size = len(combined)
        key = str(size) + "-"
        for _ in range(30):
            key += str(random.randint(0, 9))

        f12 = "extracted_smiles/" + key + ".csv"
        combined.to_csv(f12)
        return f12


def finalize(combined):
    print("Finished... Saving")
    # Rearrange the smiles
    smiles = combined.drop('score', 1)
    smiles = smiles[["smile"]]
    print("Here is the smiles:")
    print(smiles.head())
    smiles.to_csv("smiles.csv", sep=" ")

    # Rearrange for id,score
    combined.drop("smile", 1, inplace=True)
    combined.to_csv("id_score.csv")
    print("Here are the ids and scores")
    print(combined.head())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-smile_dir", required=True)
    parser.add_argument("-morgan_dir", required=True)
    parser.add_argument("-processors", required=True)
    parser.add_argument("-mols_to_dock", required=False, default="all")

    args = parser.parse_args()
    predictions = []

    for file in glob.glob(args.morgan_dir + "/*"):
        if "smile" in os.path.basename(file):
            predictions.append(file)

    print("Morgan Dir: " + args.morgan_dir)
    print("Smile Dir: " + args.smile_dir)
    print("Number Of Files: ", len(predictions))
    # Sort the predictions
    # Our name looks like -> smile_all_N.txt and we want N so we get:
    #   smile_all_N.txt -> ["smile_all_N", "txt"] -> "smile_all_N" -> ["smile", "all", "N"] -> N
    predictions.sort(key=lambda x: int(x.split(".")[0].split("_")[-1]))

    # combine the files
    print("Finding smiles...")
    print("Number of CPUs: " + str(multiprocessing.cpu_count()))
    num_jobs = min(len(predictions), int(args.processors))

    # Try to create a directory for the smile CSVs
    try:
        print("Created 'extracted_smiles' Directory")
        os.mkdir("extracted_smiles/")
        with closing(Pool(num_jobs)) as pool:
            file_paths = pool.map(merge_on_smiles, predictions)
    except IOError:
        print("The 'extracted_smiles' Directory Exists... Skipping initial merge.")
        file_paths = ["extracted_smiles/" + f for f in os.listdir("extracted_smiles/")]

    # combine all files in the list and sort the values
    print("Merging Complete - Concatenating all files...")

    # Run this mapping until we have only a single file left
    # We merge each file in parallel and sort them
    merging_iteration = 0
    num_files = len(os.listdir("extracted_smiles/"))
    is_final_iteration = False
    while num_files > 1:
        # Check if final iteration or if this merge is the final merge
        top_n = None if num_files != 2 else args.mols_to_dock
        merging_iteration += 1
        print("Merging Iteration:", merging_iteration)
        print("Files Remaining:", num_files)
        print("Percent Complete:", round(1 / num_files, 3) * 100, "%")

        # Create the arguments to run the merge
        merging_args = []
        for i in range(len(file_paths) - 1, -1, -2):
            if i - 1 >= 0:
                merging_args.append((top_n,
                                     file_paths[i],
                                     file_paths[i - 1]))

                # Remove the file paths from the list since they have been combined
                file_paths.remove(file_paths[i])
                file_paths.remove(file_paths[i - 1])

        # Run the jobs and gather all of the file path
        num_jobs = min(len(merging_args), int(args.processors))
        with closing(Pool(num_jobs)) as pool:
            file_paths += pool.map(kinda_merge_sort, merging_args)

        # Update the number of files
        num_files = len(os.listdir("extracted_smiles/"))

    with open("final_phase.info", "w") as info:
        info.write("Finished")