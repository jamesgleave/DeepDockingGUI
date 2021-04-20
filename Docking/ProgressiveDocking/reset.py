"""
This is used for resetting phases and cancelling jobs. It will remove the slurm files and/or cancel jobs that are
associated with the passed project name and username.
"""

import argparse
import glob
import csv
import os


def judge(slurm_files, project_name, phase_job, remove_slurms=True, test=False):
    """ Judges whether or not a file should be removed or jobs should be cancelled"""

    if remove_slurms:
        # Look at every file
        for slurm_file in slurm_files:
            # Read file
            with open(slurm_file, "r") as file:
                # Look at each line of file
                for line in file:
                    # If the project name is in the header
                    if "Project Name:" in line and project_name in line:
                        if not test:
                            # Get the job ID to cancel
                            job_id = slurm_file.split(".")[1]
                            os.system("scancel " + str(job_id))

                            # Remove the files
                            os.remove(slurm_file)
                            os.remove(slurm_file.replace("out", "err"))

                        print("Judged", os.path.basename(slurm_file))
                        break

    # Reads phase_jobs.csv and cancels each job
    print("Cancelling Jobs...")

    # Get the ids
    ids = []
    with open(phase_job, 'r') as file:
        # Read csv
        reader = [row for row in csv.reader(file)]
        # get the job id index
        index = reader[0].index("job_id")
        # get the index of the job_ids
        rows = reader[1:]
        # get the ids
        for row in rows:
            ids.append(row[index])

    for jid in ids:
        print("Cancelling Job", jid)
        if not test:
            os.system("scancel " + str(jid))


if __name__ == "__main__":
    # TODO Ensure this can cancel pending jobs too!
    parser = argparse.ArgumentParser()
    parser.add_argument("--project_name", type=str)
    parser.add_argument("--username", type=str)
    parser.add_argument("--scripts", type=str)
    parser.add_argument("--remove_slurms", type=bool, default=True, required=False)
    parser.add_argument("--test", type=bool, default=False, required=False)

    args = parser.parse_args()
    
    # Grab all of the slurm files
    files = glob.glob("slurm-*.out") + glob.glob("GUI/slurm-*.out")
    files = [args.scripts + "/" + f for f in files]
    pj = args.scripts + "/GUI/" + args.username + "_phase_jobs.csv"
    judge(files, project_name=args.project_name, phase_job=pj, remove_slurms=args.remove_slurms, test=args.test)


