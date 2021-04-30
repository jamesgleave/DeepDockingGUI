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
        bash_scripts = ['progressive_docking_model_selection.sh', 'morgan_fing.sh', 'prepare_ligands_ad.sh', 'final_phase.sh', 
                        'phase_1.sh', 'phase_2.sh', 'phase_3.sh', 'phase_4.sh', 'phase_5.sh',  'autodock_gpu_ad.sh', 
                        'progressive_docking_sampling.sh', 'final_extraction.sh', 'split_chunks.sh', 
                        'phase_3_concluding_combination.sh', 'phase_a.sh']
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
    else:
        custom_headers = []

    cpu_change_exclusion = ["phase_2.sh", "phase_3.sh", "phase_4.sh", "phase_5.sh", "split_chunks.sh"]
    # Loop through the bash scripts and change them
    for file in bash_scripts:
        lines = open(os.path.join(path, file), "r").readlines()
        contains_custom_headers = False
        wrote_partition = False
        for line_number, line in enumerate(lines):
            # Check to see if the file we are looking at should change its cpu per task
            if file not in cpu_change_exclusion:
                # Change the number of cpus
                if "#SBATCH --cpus-per-task=" in line and "*custom-header*" not in line:
                    print(file, "has had its numbers of CPUs changed to", n_cpu)
                    new_line = line.split("=")[0] + "=" + str(n_cpu) + "\n"
                    lines[line_number] = new_line

            # Changing partition as well
            if "#SBATCH --partition=" in line and "*custom-header*" not in line:
                print(file, "has had its partition changed to", partition)
                if partition == "": # if set to default we dont want to include partition
                    lines.pop(line_number)
                else:
                    lines[line_number] = line.split("=")[0] + "=" + str(partition) + "\n"
                wrote_partition = True

            # Check to see if our list contains custom headers
            # and remove to avoid duplicates
            if "*custom-header*" in line:
                lines.pop(line_number)
                contains_custom_headers = True

        if not wrote_partition and partition != "": 
            # This will occur if it was previously set to default and now needs to be changed.
            lines.insert(1, "#SBATCH --partition=" + str(partition) + "\n")

        # If we are using custom headers, include them in the bash script here...
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

    # At the end of this function, we create a file that contains the custom headers/gpu partition for
    # simple_job_models.py and simple_job_predictions.py to read so their slurm files are well formatted.
    with open("custom_slurm_header.txt", "w") as custom_slurm_header:
        if partition != "": # if not default
            custom_slurm_header.write("#SBATCH --partition=" + partition + "\n")
        for header in custom_headers:
            if header != "":
                new_line = header + " # *custom-header*\n"
                custom_slurm_header.write(new_line)


def rewrite_headers():
# This function is designed to adjust header parameters in all .sh files
    pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, required=True)
    parser.add_argument("--n_cpu", type=int, required=True)
    parser.add_argument("--partition", type=str, required=True)
    parser.add_argument("--custom_headers", type=str, required=True)

    args = parser.parse_args()

    # Set the custom headers to None if none were passed
    if args.custom_headers == "":
        args.custom_headers = None

    change_slurm(path=args.path, n_cpu=args.n_cpu, partition=args.partition, custom_headers=args.custom_headers)
