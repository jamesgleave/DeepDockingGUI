import os
import glob
import shutil
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--phase", type=int)
parser.add_argument("--iteration", type=int)
parser.add_argument("--project_path", type=str)
parser.add_argument("--script_path", type=str, required=False)

args = parser.parse_args()

# Make a directory for all of the slurm files
try:
    os.mkdir("slurm_out_files")
except OSError:
    pass

# Create a directory for the project
project_name = os.path.basename(args.project_path)
try:
    os.mkdir("slurm_out_files/{}".format(project_name))
except OSError:
    pass

# Set the phase to "a" if 0 is passed
if args.phase == 0:
    args.phase = "final"

# Create a phase directory
phase_dir = "slurm_out_files/{}/slurm_itr_{}_phase_{}".format(project_name, args.iteration, args.phase)
project_path = args.project_path

print("Target Project:", project_name)
print("Iteration:", args.iteration)
print("Phase:", args.phase)


def make_the_move(f_err, f_out):
    # Moves slurm files that belong to the project "project_name"

    # move all slurm files
    for err, out in zip(f_err, f_out):

        # Read the file and make sure it belongs to the desired project
        with open(out, "r") as out_file:
            for line in out_file:
                # Move file if the project path is embedded within its own path (meaning it is in the project dir)
                # OR
                # If the out file has the line Project Name: project_name then move it
                if project_path in out or "Project Name:" in line and project_name in line:
                    # Move the error files
                    try:
                        shutil.move(err, "{phase_dir}/{err}".format(phase_dir=phase_dir, err=os.path.basename(err)))
                    except IOError:
                        print("Error on:", err)
                        pass

                    # Move the out files
                    try:
                        shutil.move(out, "{phase_dir}/{out}".format(phase_dir=phase_dir, out=os.path.basename(out)))
                    except IOError:
                        print("Error on:", out)
                        pass

                    break


# Running after phase 1
if args.phase == 1:
    # Create a directory for all of the slurm files
    try:
        os.mkdir(phase_dir)
    except OSError:
        print("The directory {} already exists.".format(phase_dir))

    # Gather the slurm files
    slurm_err = glob.glob("slurm-phase_1*.err")
    slurm_out = glob.glob("slurm-phase_1*.out")

    make_the_move(slurm_err, slurm_out)

elif args.phase == 2:
    # Create a directory for all of the slurm files
    try:
        os.mkdir(phase_dir)
    except OSError:
        print("The directory {} already exists.".format(phase_dir))

    # Gather the slurm files in the script dir
    slurm_err = glob.glob("slurm-phase_2*.err")
    slurm_out = glob.glob("slurm-phase_2*.out")

    # Gather the project dir
    slurm_err += glob.glob("{}/iteration_{}/slurm-phase_2*.err".format(args.project_path, args.iteration))
    slurm_out += glob.glob("{}/iteration_{}/slurm-phase_2*.out".format(args.project_path, args.iteration))

    # Grab the slurm files in the chunks
    slurm_err += glob.glob("{}/iteration_{}/chunk*/*/slurm*.err".format(args.project_path, args.iteration))
    slurm_out += glob.glob("{}/iteration_{}/chunk*/*/slurm*.out".format(args.project_path, args.iteration))

    make_the_move(slurm_err, slurm_out)

elif args.phase == 3:
    # Create a directory for all of the slurm files
    try:
        os.mkdir(phase_dir)
    except OSError:
        print("The directory {} already exists.".format(phase_dir))

    # Gather the slurm files in the script dir
    slurm_err = glob.glob("slurm-phase_3*.err")
    slurm_out = glob.glob("slurm-phase_3*.out")

    # Gather the project dir
    slurm_err += glob.glob("{}/iteration_{}/slurm-phase_3*.err".format(args.project_path, args.iteration))
    slurm_out += glob.glob("{}/iteration_{}/slurm-phase_3*.out".format(args.project_path, args.iteration))

    # Grab the slurm files in the res
    slurm_err += glob.glob("{}/iteration_{}/res/*/slurm-phase_3*.err".format(args.project_path, args.iteration))
    slurm_out += glob.glob("{}/iteration_{}/res/*/slurm-phase_3*.out".format(args.project_path, args.iteration))

    make_the_move(slurm_err, slurm_out)


elif args.phase == 4:
    # Create a directory for all of the slurm files
    try:
        os.mkdir(phase_dir)
    except OSError:
        print("The directory {} already exists.".format(phase_dir))

    # Gather the slurm files in the script dir
    slurm_err = glob.glob("slurm-phase_4*.err")
    slurm_out = glob.glob("slurm-phase_4*.out")

    # Grab the slurm files in the simple_jobs
    slurm_err += glob.glob("{}/iteration_{}/simple*/slurm-phase_4*.err".format(args.project_path, args.iteration))
    slurm_out += glob.glob("{}/iteration_{}/simple*/slurm-phase_4*.out".format(args.project_path, args.iteration))

    make_the_move(slurm_err, slurm_out)


elif args.phase == 5:
    # Create a directory for all of the slurm files
    try:
        os.mkdir(phase_dir)
    except OSError:
        print("The directory {} already exists.".format(phase_dir))

    # Gather the slurm files in the script dir
    slurm_err = glob.glob("slurm-phase_5*.err")
    slurm_out = glob.glob("slurm-phase_5*.out")

    # Grab the slurm files in the simple_jobs
    slurm_err += glob.glob("{}/iteration_{}/simple*predictions/slurm-phase_5*.err".format(args.project_path, args.iteration))
    slurm_out += glob.glob("{}/iteration_{}/simple*predictions/slurm-phase_5*.out".format(args.project_path, args.iteration))

    # Grab the slurm files in the GUI dir from smile searching
    slurm_err += glob.glob("GUI/slurm-*.err".format(args.script_path, args.iteration))
    slurm_out += glob.glob("GUI/slurm-*.out".format(args.script_path, args.iteration))

    make_the_move(slurm_err, slurm_out)

elif args.phase == "final":
    # This means everything is finished
    # Create a directory for all of the slurm files
    try:
        os.mkdir(phase_dir)
    except OSError:
        print("The directory {} already exists.".format(phase_dir))

    # Gather the slurm files in the script dir
    slurm_err = glob.glob("slurm-phase_*.err")
    slurm_out = glob.glob("slurm-phase_*.out")

    # Grab the files in the GUI directory
    slurm_err += glob.glob("GUI/slurm-*.err".format(args.script_path))
    slurm_out += glob.glob("GUI/slurm-*.out".format(args.script_path))

    make_the_move(slurm_err, slurm_out)
