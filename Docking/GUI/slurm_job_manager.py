import os
import glob
import subprocess


"""
This script is used to check for errors in slurm files.
post_crash_report will check for errors in finished jobs.
running_job_manager will check for errors in running jobs.

Since we are using this script to read through all of the .err files anyway, 
we might as well save the PID of each to a new file for each running file in running_job_monitor.
"""


def post_crash_report(project_path, current_iteration):
    """
    Detect crashes after the phase has finished by looking through the slurm files in slurm_out_files
    """

    # Check if we have created the slurm file directory
    if not os.path.exists("slurm_out_files"):
        print("Crash Report: Could not find 'slurm_out_files' directory")
        return {"error": False, "traceback": [], "filename": None}

    # If we have, grab the files
    project_name = os.path.basename(project_path)
    slurm_files = glob.glob("slurm_out_files/" + project_name + f"/*itr_{current_iteration}*/*")

    # Read the files and look for a crash!
    for file in slurm_files:
        # Only read the error files
        if ".err" in file:
            # Open the error file and read the lines
            with open(file, "r") as error_file:
                lines = error_file.readlines()
                for line in lines:
                    # Look for a crash with the keyword "Traceback"
                    if "Traceback" in line:
                        return {"error": True, "traceback": lines, "filename": file}

    # If we make it through every error file without issue then return
    return {"error": False, "traceback": [], "filename": None}


def running_job_monitor(project_path, scripts_path, current_iteration, current_phase, username="x", project_name=""):
    """ Detects crashes mid phase """

    # Key words to look for an error
    slurm_error = "sbatch: error:"
    python_error = "Traceback"

    # Save our project location
    path = project_path + "/" + str(current_iteration) + "/"

    # Grab error files in scripts directory
    # TODO check to see if these files belong to the project we are looking at

    # Only add parent files that belong to the project
    # This section checks the lines of the file for the header "Project Name: " followed by the project name
    parent_errors = []
    for filename in glob.glob(scripts_path + "/" + "*.err"):
        belongs_to_project = False
        with open(filename.replace(".err", ".out"), "r") as f:
            for line in f.readlines():
                if "Project Name:" in line and project_name in line:
                    belongs_to_project = True
                    break
        if belongs_to_project:
            parent_errors.append(filename)

    # Grab the error files found in the project
    # These are 100% going to be a part of the project we are looking at because the are in the project folder
    child_errors = glob.glob(path + "*.err")

    # Where the rest of the error files appear in the project depends on the phase
    # These are 100% going to be a part of the project we are looking at because the are in the project folder
    grand_child_errors = []
    if current_phase == 2:
        grand_child_errors += glob.glob(path + "chunk*/*/slurm-phase_2*.err")
    elif current_phase == 3:
        grand_child_errors += glob.glob(path + "res/*/slurm-phase_3*.err")
    elif current_phase == 4:
        grand_child_errors += glob.glob(path + "simple_job/slurm-phase_4*.err")
    elif current_phase == 5:
        grand_child_errors += glob.glob(path + "simple*predictions/slurm-phase_5*.err")
        grand_child_errors += glob.glob(scripts_path + "/GUI/slurm-phase_5*.err")  # From smile searching

    # Combine all error files
    all_error_files = parent_errors + child_errors + grand_child_errors
    all_sbatch_submissions = []
    running_jobs = set()
    crashes = []

    # Open a new file to hold which processes are currently running or have finished under the current phase
    phase_jobs = open(scripts_path + f"/GUI/Users/{username}/{username}_phase_jobs.csv", "w")
    phase_jobs.write("job_name,job_id,is_running,is_pending,contains_errors\n")

    # Read every error file and look for crashes!
    for p2err in all_error_files:
        # Store the details of the crash
        details = {"traceback": "", "where": "", "error": "", "kind": ""}

        # Get the name of the error file and extract the job id
        # slurm-phase_X.123456.err -> ['slurm-phase_X', 123456, err] -> 123456
        file_name = os.path.basename(p2err)
        job_id = file_name.split(".")[1]

        # TODO use username here to further increase confidence that this job has been run by the user!
        is_running = "True" if os.system('squeue|grep ' + job_id + " &>/dev/null ") == 0 else "False"
        contains_errors = False

        print("Job ID:", job_id, "Is Running ->", is_running)

        with open(p2err, 'r') as err:
            # Read the file
            contents = err.read()

            # Check if error key words were detected
            if slurm_error in contents:
                # Split into lines to find where the error happened
                # There tends to be a lot of repetition in these error files so we crunch it to a set
                lines = set(contents.split("\n"))

                # Initialize a basic sbatch error
                error = "sbatch error"

                # Read the lines and check for errors
                # This is simpler than a python error
                for line in lines:
                    if slurm_error in line:
                        details["traceback"] += line + "\n"

                    # We know a few errors that we have seen before:
                    if "invalid partition" in line:
                        error = "invalid partition"
                    elif "line must start with #!" in line:
                        error = "not a batch script"

                details["where"] = "phase " + str(current_phase)
                details["error"] = error
                details["kind"] = "slurm"
                crashes.append(details)
                contains_errors = True

            elif python_error in contents:
                # Split into lines to find where the error happened
                lines = contents.split("\n")

                # Read every line
                write = False
                for line in lines:
                    # Check if we have found the error location and save the traceback
                    if python_error in line:
                        # Initialize the string to inscribe the traceback as well as the string to store the file
                        traceback_string = ""
                        where_error = ""
                        write = True
                    elif write and line[0] == " ":  # Indentation follows the traceback
                        # Write the traceback line by line to the details
                        traceback_string += line + "\n"

                        # Lets write which file the error happened in as well
                        if "File " in line:
                            where_error = line
                    elif write:
                        write = False

                        # Write the final line to the traceback
                        traceback_string += line + "\n"

                        # Get the specific error that occurred
                        error = line.rstrip().split(":")[0]

                        # Save findings
                        details["traceback"] = traceback_string
                        details["where"] = where_error
                        details["error"] = error
                        details["kind"] = "python"
                        crashes.append(details)
                        contains_errors = True

        # Find every sbatch submission
        with open(p2err.replace(".err", ".out")) as out:
            # We ignore phase a slurm files from this
            if 'phase_a' not in p2err.replace(".err", ".out"):
                # Store the PIDs of all submitted jobs
                sbj = "Submitted batch job"
                belongs_to_project = False
                for line in out.readlines():
                    # Every parent job's out file created by a project will have the line
                    # "Project Name: project_name".
                    # We can use this to determine if a slurm out file was created by a certain project.
                    # We can also use the path of the project to determine this since the project path will be embedded
                    # in the filepath
                    if "Project Name:" in line and project_name in line or path in p2err:
                        belongs_to_project = True

                    # If a batch job was submitted by the passed project it will be added to the submissions.
                    if sbj in line and belongs_to_project:
                        all_sbatch_submissions.append(line.split(" ")[-1].replace("\n", ""))

        # Write to the file
        # TODO Check to see if the file we are looking at belongs to the project before writing to phase jobs
        phase_jobs.write(f"{file_name},{job_id},{is_running},False,{contains_errors}\n")

        # Add the job id to the set of running jobs
        running_jobs.add(job_id)

    # Check for the final phase and add it to the submissions if it is pending
    # We only need to check here if it is pending because it would not have generated any out files yet.
    # Once the job begins executing, it will overwrite the final_phase file with 'running'.
    if current_phase == 6 and os.path.exists(path + "/final_phase.info"):
        with open(path + "/final_phase.info", "r") as final_phase:
            contents = final_phase.readlines()
            if "Pending" in contents[0]:
                # Once submitted by phase a, we create the file with the job id within it.
                job_id = contents[1].split(" ")[-1].replace("\n", "")
                # We have to make sure it is pending, in case it has been cancelled while pending.
                # TODO use username here to further increase confidence that this job has been run by the user!
                if os.system('squeue|grep ' + job_id) == 0:
                    all_sbatch_submissions.append(job_id)
            else:
                # We pass here because the job is running and there will be out files generated for the job which would
                # have been in the parent jobs.
                pass

    # Add pending processes
    all_sbatch_submissions = set(all_sbatch_submissions)
    pending_submissions = all_sbatch_submissions.difference(running_jobs)

    for pd in pending_submissions:
        phase_jobs.write(f"NA,{pd},False,True,NA\n")

    # Close our jobs file
    phase_jobs.close()

    return crashes

