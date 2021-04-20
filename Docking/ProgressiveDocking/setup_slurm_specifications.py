"""
This script will be called when a new project is created or a new project is loaded.
It will adjust the number of cpus in each slurm script according to the passed n_cpu argument.
It will also change the partition for the slurm scrips.

v1.0.1
"""

import os


def change_slurm(path, n_cpu, partition, specify=None, custom_headers=None):
    # Find all of the bash scripts
    if specify is None:
        bash_scripts = [f for f in os.listdir(path) if ".sh" in f]
        try:
            bash_scripts += ["GUI/" + f for f in os.listdir(path + "/GUI") if ".sh" in f]
        except FileNotFoundError:
            pass
    else:
        bash_scripts = specify if type(specify) is type(list) else [specify]

    # Check if we have any custom headers we want to include
    if custom_headers is not None:
        # the custom headers should come in the format h1,h2,...,hn
        custom_headers = custom_headers.strip("/n").split(",")
        using_custom_headers = True
    else:
        using_custom_headers = False

    # Check if the partition is empty
    if "No data" in partition:
        partition = ""

    cpu_change_exclusion = ["phase_2.sh", "phase_3.sh", "phase_4.sh", "phase_5.sh", "split_chunks.sh"]
    partition_include = ["phase_4.sh", "autodock_gpu_ad.sh"]
    # Loop through the bash scripts and change them
    for file in bash_scripts:
        lines = open(os.path.join(path, file), "r").readlines()
        contains_custom_headers = False
        for line_number, line in enumerate(lines):
            # Check to see if the file we are looking at should be changed...
            if file not in cpu_change_exclusion:
                # Change the number of cpus
                if "#SBATCH --cpus-per-task=" in line and "*custom-header*" not in line:
                    print(file, "has had its numbers of CPUs changed to", n_cpu)
                    new_line = line.split("=")[0] + "=" + str(n_cpu) + "\n"
                    lines[line_number] = new_line

            # check to see if excluded
            if file in partition_include:
                if "#SBATCH --partition=" in line and "*custom-header*" not in line:
                    print(file, "has had its partition changed to", partition)
                    new_line = line.split("=")[0] + "=" + str(partition) + "\n"
                    lines[line_number] = new_line

            # Check to see if our list contains custom headers
            if "*custom-header*" in line:
                contains_custom_headers = True

        # Remove all custom headers to avoid duplicates
        if contains_custom_headers:
            lines = [line for line in lines if "*custom-header*" not in line]

        # If we are using custom headers, include them in the bash script here...
        if using_custom_headers:
            # Add every custom header
            for header in custom_headers:
                if header != "":
                    # Create the new line
                    new_line = header + " # *custom-header*\n"

                    # Insert the new line on the second line of the script since the first must be "#!/bin/bash"
                    lines.insert(1, new_line)

        # Save the new file
        with open(os.path.join(path, file), "w") as updated_file:
            for line in lines:
                updated_file.write(line)

    # TODO: At the end of this function, we should create a file that contains the custom headers/gpu partition for
    #  simple_job_models.py and simple_job_predictions.py to read so their slurm files are well formatted.
    with open("custom_slurm_blueprint.txt", "w") as custom_slurm_blueprint:
        gpu_partition = "#SBATCH --partition=" + partition + "\n"
        custom_slurm_blueprint.write(gpu_partition)
        if using_custom_headers:
            for header in custom_headers:
                if header != "":
                    new_line = header + " # *custom-header*\n"
                    custom_slurm_blueprint.write(new_line)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str)
    parser.add_argument("--n_cpu", type=int)
    parser.add_argument("--partition", type=str)
    parser.add_argument("--custom_headers", type=str)

    args = parser.parse_args()

    # Set the custom headers to None if none were passed
    if args.custom_headers == "":
        args.custom_headers = None

    change_slurm(path=args.path, n_cpu=args.n_cpu, partition=args.partition, custom_headers=args.custom_headers)


