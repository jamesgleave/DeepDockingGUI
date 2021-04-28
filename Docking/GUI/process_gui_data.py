"""
v2.0.0
"""
import os
import time
import glob
import pandas as pd
import slurm_job_manager


def calculate_date_time(best, worst, average):

    # updates the information from seconds to 00:00:00 time
    def help_me(seconds):
        # Update to date time format
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        h, m, s = int(h), int(m), int(s)

        if h < 0:
            h = m = s = 0

        if h < 10:
            h = "0" + str(h)
        else:
            h = str(h)

        if m < 10:
            m = "0" + str(m)
        else:
            m = str(m)

        if s < 10:
            s = "0" + str(s)
        else:
            s = str(s)
        return h, m, s

    hour, minute, second = help_me(best)
    best = "{}:{}:{}".format(str(hour), str(minute), str(second))

    hour, minute, second = help_me(worst)
    worst = "{}:{}:{}".format(str(hour), str(minute), str(second))

    hour, minute, second = help_me(average)
    average = "{}:{}:{}".format(str(hour), str(minute), str(second))
    return best, worst, average


def find_max_iteration(iterations):
    """Returns the current iteration"""
    max_itr = iterations[0]
    for itr in iterations:
        if int(max_itr.split("_")[-1]) > int(itr.split("_")[-1]):
            pass
        else:
            max_itr = itr
    return max_itr


def get_current_phase(path):
    """Returns the current phase of the current iteration"""
    files = glob.glob(path + "/phase_*.sh")
    phases = [0]
    for file in files:
        file = os.path.basename(file)
        phase = file.split(".")[0]  # -> phase_x
        phase_num = int(phase.split("_")[-1])  # -> x
        phases.append(phase_num)
    return max(phases)


def is_idle(script_path, username):
    try:
        phase_jobs = script_path + "/" + username + "_phase_jobs.csv"
        jobs = pd.read_csv(phase_jobs)
        num_jobs = len(jobs)

        # returns true if the system is idle
        if num_jobs == 0:
            return True

        # return true if all jobs are not running
        is_running = False
        for status in jobs['is_running']:
            is_running = is_running or status
        if not is_running:
            return True

        return False

    except OSError:
        return True


def get_molecules_remaining(path) -> dict:
    """Returns the molecules remaining after predictions"""
    if 'best_model_stats.txt' not in os.listdir(path):
        return {'true': -1, 'estimate': -1, 'error': -1}

    try:
        with open(path + '/best_model_stats.txt') as bms:
            est_num_left = float(bms.readlines()[-1].split(": ")[1].strip("\n"))
    except IndexError:
        est_num_left = -1

    try:
        pred = pd.read_csv(path + '/morgan_1024_predictions/Mol_ct_file_updated.csv')
    except FileNotFoundError:
        return {'true': -1, 'estimate': est_num_left, 'error': -1}

    true_mol_rem = sum(pred.Number_of_Molecules)

    if est_num_left > 0:
        error = (abs(est_num_left - true_mol_rem) / true_mol_rem) * 100
    else:
        error = -1

    return {'true': true_mol_rem, 'estimate': est_num_left, 'error': error}


def get_model_data(path):
    """Gets the model training data"""
    # Walk through the directory
    log_files = []
    for root, dirs, files in os.walk(path, topdown=False):
        # Grab all of the log files
        for name in files:
            if "csv" in name and "model" in name:
                log_files.append(name)
    # Get each model log file and read it
    model_logs = []  # A list of dictionaries containing epoch based data
    for num in range(len(log_files)):
        try:
            name = path + "/" + "model_{}_train_log.csv".format(num + 1)
            model = pd.read_csv(name, index_col=0).to_dict()
            model_logs.append(model)
        except OSError:
            pass
    return model_logs


def get_phase_1_progress(path, iteration):

    # Find a sample smile file
    with open(path + "/logs.txt", "r") as logs:
        path_to_morgan = logs.readlines()[3].strip("\n")
        sample = os.listdir(path_to_morgan)

        # Remove non useful files from the list 
        # TODO: this will no longer be needed since they are now stored at the project path
        try:
            sample.remove("Mol_ct_file.csv")
        except ValueError:
            pass

        # Remove non useful files from the list
        try:
            sample.remove("Mol_ct_file_updated.csv")
        except ValueError:
            pass

        sample = sample[0]

    current_smile_size = os.path.getsize(os.path.join(path_to_morgan, sample))
    zinc_15_smile_size = 4991355635
    file_size_ratio = current_smile_size / zinc_15_smile_size

    # estimate the time to count the molecules (seconds
    time_mol_count = 297.3195502758026 * file_size_ratio
    time_sampling = 410.2387490272522 * file_size_ratio
    time_extracting = (394.7765419483185 + 130.1235864162445) * file_size_ratio
    total = time_mol_count + time_sampling + time_extracting
    best, worst, average = total * 0.6, total * 1.6, total

    # Update if reached zero seconds
    average = average if average > 0 else worst
    best = best if best > 0 else average

    # TODO use the slurm squeue time running to d etermine how long it has been running instead (in case it is PD)
    delta_time_since_execution = time.time() - os.path.getctime("{}/{}/phase_1.sh".format(path, iteration))
    eta_best = max(best - delta_time_since_execution, 0)
    eta_worst = max(worst - delta_time_since_execution, 0)
    eta_average = max(average - delta_time_since_execution, 0)

    # turn the seconds into datetime
    best, worst, average = calculate_date_time(best, worst, average)
    eta_best, eta_worst, eta_average = calculate_date_time(eta_best, eta_worst, eta_average)

    return {"best": eta_best, "worst": eta_worst, "average": eta_average,
            "best_remaining": best, "worst_remaining": worst, "average_remaining": average,
            "delta_time": delta_time_since_execution}


def get_phase_2_progress(path):

    # The path to the chunks
    chunk_path = path + "/chunks_smi/test_set_part0000"

    # Check if the path exists to read the pdbqt files
    if not os.path.exists(chunk_path):
        return {"best": -1, "worst": -1, "average": -1}

    delta_time_since_execution = time.time() - os.path.getctime("{}/phase_2.sh".format(path))
    delta_time_to_complete = None
    for file in os.listdir(chunk_path):
        if '.sdf' in file:
            delta_time_to_complete = time.time() - os.path.getctime(chunk_path + "/" + file)

    # If there is no sdf file, return
    if delta_time_to_complete is None:
        return {"best": -1, "worst": -1, "average": -1}

    # The time spent calculating the ligand
    time_per_prepare_ligand = delta_time_since_execution - delta_time_to_complete
    num_chunks = len(os.listdir(path + "/chunks_smi")) // 3

    total = time_per_prepare_ligand * num_chunks
    best, worst, average = total * 0.6, total * 1.6, total

    # Create ETA
    delta_time_since_execution = time.time() - os.path.getctime("{}/phase_2.sh".format(path))
    eta_best = max(best - delta_time_since_execution, 0)
    eta_worst = max(worst - delta_time_since_execution, 0)
    eta_average = max(average - delta_time_since_execution, 0)

    # Update if reached zero seconds
    average = average if average > 0 else worst
    best = best if best > 0 else average

    # turn the seconds into datetime
    best, worst, average = calculate_date_time(best, worst, average)
    eta_best, eta_worst, eta_average = calculate_date_time(eta_best, eta_worst, eta_average)

    return {"best": eta_best, "worst": eta_worst, "average": eta_average,
            "best_remaining": best, "worst_remaining": worst, "average_remaining": average,
            "delta_time": delta_time_since_execution}


def get_phase_3_progress(path):
    time_to_run_1 = 3.059
    try:
        chunk_size = len(open(f"{path}/chunks_smi/test_set_part0000/tautomers.log", "r").readlines())
        num_chunks = len(os.listdir(f"{path}/chunks_smi/"))
    except OSError:
        return {"best": "Calculating...", "worst": "Calculating...", "average": "Calculating..."}

    best = chunk_size * time_to_run_1
    worst = num_chunks * chunk_size * time_to_run_1
    average = (best + worst)/2

    try:
        delta_time_since_execution = time.time() - os.path.getctime("{}/phase_3.sh".format(path))
    except OSError:
        return {"best": "Idle...", "worst": "Idle...", "average": "Idle..."}

    eta_best = max(best - delta_time_since_execution, 0)
    eta_worst = max(worst - delta_time_since_execution, 0)
    eta_average = max(average - delta_time_since_execution, 0)

    # turn the seconds into datetime
    best, worst, average = calculate_date_time(best, worst, average)
    eta_best, eta_worst, eta_average = calculate_date_time(eta_best, eta_worst, eta_average)

    return {"best": eta_best, "worst": eta_worst, "average": eta_average,
            "best_remaining": best, "worst_remaining": worst, "average_remaining": average,
            "delta_time": delta_time_since_execution}


def get_phase_4_progress(models):
    # Use the largest ETA from the models to guess a phase ETA
    etas = [model["estimate_time"] for model in models]
    best = min(etas)
    worst = max(etas)
    average = (best + worst) / 2
    return {"best": best, "worst": worst, "average": average}


def get_phase_5_progress(path):
    simple_job_predictions = path + "/simple_job_predictions"


def get_phase_percentage(gui_path, username):
    """
    Reads the file produced by the job monitor.
    This file contains info on the jobs such as if the job is pending, running, its job id, etc.
    Using this info, we can determine the percent complete of each phase by their jobs.
    """
    jobs = pd.read_csv(gui_path + f"/{username}_phase_jobs.csv")
    finished = 0
    total = 1
    for row in jobs.iterrows():
        is_running = row[1][2]
        is_pending = row[1][3]
        name = row[1][0]
        if isinstance(name, str) and 'phase_a' not in name:
            # Incrememt runnning if we finn a running job
            finished += 1 if not is_running and not is_pending else 0
        total += 1

    percent_complete = round(finished / total * 100, 3)
    print("Percent complete:", percent_complete, "total jobs:", total, "jobs finished:", finished)
    return percent_complete


def check_pending(gui_path, username):
    # Read the phase jobs file
    phase_jobs = gui_path + username + "_phase_jobs.csv"
    jobs = pd.read_csv(phase_jobs)

    # If there are no jobs it is not pending
    if len(jobs) == 0:
        return False

    # Count the number of pending, total, and running jobs
    pending = 0
    running = 0
    total = 0
    for row in jobs.iterrows():
        pending += 1 if row[1][3] else 0
        running += 1 if row[1][2] else 0
        total += 1

    percent_running = 100 * round(running / total, 3)
    percent_pending = 100 * round(pending / total, 3)
    return {"%running": percent_running,
            "%pending": percent_pending,
            "running": running,
            "pending": pending,
            "total": total}


def read_iterations(project_path, pickle_path, username):
    # If the user is on windows, their end line will be \r and should be removed
    pickle_path = pickle_path.replace("\r", "")
    project_path = project_path.replace("\r", "")
    project_name = os.path.basename(project_path)

    # Find all iterations
    all_models_paths = []
    iterations = []

    for file in os.listdir(project_path):
        if 'iteration_' in file:
            iterations.append(file)

    print("Number of iterations:", len(iterations))
    iterations.sort(key=lambda x: int(x.split("_")[1]))
    for itr in iterations:
        if os.path.exists(os.path.join(project_path, itr) + "/all_models"):
            all_models_paths.append(os.path.join(project_path, itr) + "/all_models/")
        else:
            all_models_paths.append("NotFound")

    # Extract the data...
    max_itr = iterations[-1]
    data = dict.fromkeys(iterations)
    for path, iteration in zip(all_models_paths, iterations):
        # The iteration root is the path to the iteration
        iteration_root = os.path.join(project_path, iteration)

        # Get the current phase
        current_phase = get_current_phase(path=iteration_root)

        # Create the iteration info - the dict that holds all info about every iteration
        iteration_info = {}

        # Add a crash report, but the slurm job manager also creates a file called 'username'_phase_jobs.csv which
        # contains all running and pending jobs. The 'username'_phase_jobs.csv is very useful for finding if the
        # project is idle and for knowing which jobs to cancel since the 'username'_phase_jobs.csv file only contains
        # jobs that belong to the loaded project.
        scripts_dir = pickle_path.replace("/GUI", "")
        iteration_info["crash_report"] = slurm_job_manager.running_job_monitor(project_path,
                                                                               scripts_dir,
                                                                               iteration,
                                                                               current_phase,
                                                                               username,
                                                                               project_name)

        # Add values to our data to be sent back to the client
        iteration_info["molecules_remaining"] = get_molecules_remaining(iteration_root)
        iteration_info["current_phase"] = current_phase
        iteration_info["in_progress"] = iteration == max_itr
        iteration_info["is_idle"] = is_idle(script_path=pickle_path, username=username)

        # If the iteration is in progress then calculate the ETA
        if iteration_info["in_progress"]:
            # Get the ETA for the first 3 phases
            if iteration_info["current_phase"] == 1:
                phase_eta = get_phase_1_progress(project_path, iteration)
            elif iteration_info["current_phase"] == 2:
                phase_eta = get_phase_2_progress(iteration_root)
            elif iteration_info["current_phase"] == 3:
                phase_eta = get_phase_3_progress(iteration_root)
            else:
                phase_eta = -1
        else:
            # Else set the ETA to 0 because it is finished
            phase_eta = 0

        # Add the phase ETA
        iteration_info['phase_eta'] = phase_eta

        # Add the model data if there is any
        if path != 'NotFound':
            # enter the phase eta
            data[iteration] = {"models": get_model_data(path), "itr": iteration_info}
        else:
            # enter the phase eta
            data[iteration] = {"models": "No Model Data Present", "itr": iteration_info}

        # Add the % complete of the iteration
        if current_phase < 6:
            itr_percent = (current_phase - 1) + (get_phase_percentage(pickle_path, username) / 100)
            iteration_info["itr_percent"] = max(min(itr_percent / 5, 1.0), 0)  # Since we have 5 phases, we divide by 5
        else:
            # This means we are completely finished... thus we are 100% complete
            iteration_info["itr_percent"] = 1.0

        # TODO Ensure that this can function with edge cases (use PID from sbatch call) and move this into a function
        # Finally, we can check if we are running the final phase!
        final_phase_info = "locked"  # The final phase cannot be ran until we are on the final iteration
        # If this iteration contains our final_phase.info file, we know it is running.
        if os.path.exists(iteration_root + "/final_phase.info"):
            # Open the file and check if it is finished
            with open(iteration_root + "/final_phase.info", "r") as final_phase:
                contents = final_phase.read()
                if "Finished" in contents:
                    final_phase_info = "finished"
                elif "Pending" in contents:
                    final_phase_info = "pending"
                    iteration_info["is_idle"] = False
                elif "Running" in contents:
                    final_phase_info = "running"
                    iteration_info["is_idle"] = False
        iteration_info["final_phase"] = final_phase_info
        iteration_info["pending_info"] = check_pending(gui_path=pickle_path, username=username)

        # Delete Later
        print()
        print("Current iteration:", iteration)
        print("Current phase:", iteration_info['current_phase'])
        print("In progress:", iteration_info['in_progress'])
        print("Is Idle:", iteration_info['is_idle'])
        print("Is Pending:", check_pending(gui_path=pickle_path, username=username))
        print("Final Phase:", final_phase_info)

    # Save to a pickle
    pickle_name = "/{}_data.pickle".format(username)
    pd.to_pickle(data, pickle_path + pickle_name)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", required=False, default=False, type=bool)
    parser.add_argument("--project_path", required=True)
    parser.add_argument("--pickle_path", required=True)
    parser.add_argument("--current_user", required=True)

    args = parser.parse_args()
    read_iterations(args.project_path, args.pickle_path, args.current_user)
