"""
This script will be called when a new project is created or a new project is loaded.
It will adjust the number of cpus in each slurm script according to the passed n_cpu argument.
It will also change the partition for the slurm scrips.

v1.0.1
"""

import os

def save_slurm_arg(project_name, path, n_cpu, cpu_partition, gpu_partition, custom_headers=None):
    # this saves all the slurm arguments as a single line so that it can 
    # be called on as arguments to sbatch submissions
    try:
        os.mkdir("slurm_args")
    except: # folder already exists.
        pass

    with open(f"./slurm_args/{project_name}_slurm_args.txt", "w") as f:
        # "#SBATCH h1#SBATCH h2...#SBATCH hn" --> "h1 h2 ... hn"
        slurm_args = " ".join(custom_headers.split("#SBATCH")).strip() if custom_headers is not None else ""
        slurm_args_cpart = slurm_args 
        slurm_args_cpart += " --partition=" + cpu_partition if cpu_partition is not None and "partition" not in slurm_args else ""
        f.write(slurm_args_cpart + "\n") # 1: write without cpu arg for non-gpu scripts 

        slurm_args_cpart += " --cpus-per-task="+str(n_cpu) if n_cpu is not None and "cpus-per-task" not in slurm_args else ""
        f.write(slurm_args_cpart + "\n") # 2: write with cpu arg for non-gpu scripts 
        
        slurm_args_gpart = slurm_args 
        slurm_args_gpart += " --partition=" + gpu_partition if gpu_partition is not None and "partition" not in slurm_args else ""
        f.write(slurm_args_gpart + "\n") # 3: write without cpu arg for gpu req scripts 

        slurm_args_gpart += " --cpus-per-task="+str(n_cpu) if n_cpu is not None and "cpus-per-task" not in slurm_args else ""
        f.write(slurm_args_gpart + "\n") # 4: write with cpu arg for gpu req scripts 


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, required=True)
    parser.add_argument("--n_cpu", type=int, required=True)
    parser.add_argument("--cpu_partition", type=str, required=True)
    parser.add_argument("--gpu_partition", type=str, required=True)
    parser.add_argument("--custom_headers", type=str, required=True)
    parser.add_argument("--project_name", type=str, required=True)

    args = parser.parse_args()

    # Set to None if none were passed
    if args.cpu_partition == "":
        args.cpu_partition = None

    if args.gpu_partition == "":
        args.gpu_partition = None

    if args.custom_headers == "":
        args.custom_headers = None

    save_slurm_arg(project_name=args.project_name, path=args.path, n_cpu=args.n_cpu,
                    cpu_partition=args.cpu_partition, gpu_partition=args.gpu_partition, 
                    custom_headers=args.custom_headers)
