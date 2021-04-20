import json
import os


def read_info():
    info = open('src/backend/db.json',
                'r').read()  # TODO: Sibling files not recognizing each other when called from another file path.
    return json.loads(info)


def activate_venv():
    info = read_info()
    command = info['env_activation_command']
    return command


def run_phase_5(project_name, specifications, logs):
    # TODO Update this to work with current version
    # The args passing to phase a
    user_info = read_info()
    t_cpu = specifications['num_cpu']  # The total processors
    project_path = user_info['project_path']  # the path to the project dir
    current_it = specifications['iteration']  # current iteration when running phase_a
    local_path = user_info['remote_path']  # the path to the scripts

    command = f"bash deactivation_script.sh; sbatch {local_path}/phase_5.sh {current_it} {project_path}/{project_name} {local_path} {t_cpu}"
    return command


def run_phase_4(project_name, specifications, logs):
    # TODO Update this to work with current version
    # The args passing to phase a
    user_info = read_info()
    t_cpu = specifications['num_cpu']  # The total processors
    project_path = user_info['project_path']  # the path to the project dir
    project_name = project_name  # the project name
    current_it = specifications['iteration']  # current iteration when running phase_a
    final_iteration = specifications['total_iterations']  # the total number of iterations we should run
    local_path = user_info['remote_path']  # the path to the scripts

    # percent first mol to be true positives
    percent_first_mol = specifications['percent_first_mol']
    # The threshold for phase 1
    threshold = specifications['threshold']

    percent_last_mol = specifications['percent_last_mol']

    command = "bash deactivation_script.sh; " + \
              f"sbatch {local_path}/phase_4.sh " \
              f"{current_it} {t_cpu} {project_path}/{project_name} " \
              f"{final_iteration==current_it} {final_iteration} {local_path} " \
              f"{percent_first_mol} {threshold} {percent_last_mol}"
    return command


def run_phase_3(project_name, specifications, logs):
    # TODO Update this to work with current version
    user_info = read_info()
    project_path = user_info['project_path']  # the path to the project dir
    local_path = user_info['remote_path']  # the path to the scripts
    path_to_auto_dock = user_info['path_to_autodock']  # the path to auto dock
    path_to_fld_file = specifications['path_to_fld']  # path to the fld grid file
    n_it = specifications['iteration']  # current iteration when running phase_a

    # number of energy evaluations for autodock
    num_energy_evaluations = specifications['num_energy_evaluations']
    # number of runs for autodock
    num_runs = specifications['num_runs']

    command = f"bash deactivation_script.sh; " \
              f"sbatch {local_path}/phase_3.sh {path_to_fld_file} {num_energy_evaluations} {num_runs} {path_to_auto_dock} {project_path}/{project_name} {n_it} {local_path}"

    return command


def run_phase_2(project_name, specifications, logs):
    # TODO Update this to work with current version
    user_info = read_info()
    project_path = user_info['project_path']  # the path to the project dir
    current_it = specifications['iteration']  # current iteration when running phase_a
    mols_to_dock = specifications["log_file"]['n_molecules']  # Number of mols to dock (should be same as in logs)
    local_path = user_info['remote_path']  # the path to the scripts
    chunk_size = round(mols_to_dock/int(specifications['num_chunks']))
    extension=".smi"

    command = "bash deactivation_script.sh; " \
              f"sbatch {local_path}/phase_2.sh {extension} {chunk_size} {local_path} {project_path}/{project_name} {current_it}"
    return command


def run_phase_1(project_name, specifications, logs):
    # TODO Update this to work with current version
    info = read_info()
    logs = specifications['log_file']
    local_path = info["remote_path"]
    n_it = specifications["iteration"]
    t_cpu = specifications["num_cpu"]
    project_path = info['project_path']  # the path to the project dir
    mols_to_dock = logs["n_molecules"]
    command = "bash deactivation_script.sh; " \
              f"sbatch {local_path}/phase_1.sh {n_it} {t_cpu} {project_path} {project_name} {mols_to_dock} {local_path}"
    return command


def run_all_phases(project_name, specifications, logs):
    # The args passing to phase a
    user_info = read_info()
    t_cpu = specifications['num_cpu']  # The total processors
    project_path = user_info['project_path']  # the path to the project dir
    project_name = project_name  # the project name
    top_n = specifications['top_n']
    current_it = specifications['iteration']  # current iteration when running phase_a
    current_phase = int(specifications['current_phase'])  # current phase when running phase_a
    mols_to_dock = int(specifications['sample_size'])  # Number of mols to dock for training
    final_iteration = specifications['total_iterations']  # the total number of iterations we should run
    local_path = user_info['remote_path']  # the path to the scripts
    path_to_auto_dock = user_info['path_to_autodock']  # the path to auto dock
    path_to_fld_file = specifications['path_to_fld']  # path to the fld grid file

    # number of energy evaluations for autodock
    num_energy_evaluations = specifications['num_energy_evaluations']
    # number of runs for autodock
    num_runs = specifications['num_runs']
    # chunk size for phase 3
    num_chunks = int(specifications['num_chunks'])
    chunk_size = round((mols_to_dock * 3)/num_chunks)
    # percent first mol to be true positives
    percent_first_mol = specifications['percent_first_mol']
    # The threshold for phase 1
    threshold = specifications['threshold']
    # The percent last mol
    percent_last_mol = specifications['percent_last_mol']

    # Clamp the current phase before submitting job
    current_phase = current_phase if current_phase > 0 else 1
    command = f"sbatch {local_path}/phase_a.sh " \
              f"{t_cpu} {project_path} {project_name} {top_n} {current_it} {current_phase} " \
              f"{mols_to_dock} {final_iteration} {local_path} {path_to_auto_dock} " \
              f"{path_to_fld_file} {num_energy_evaluations} {num_runs} {chunk_size} " \
              f"{percent_first_mol} {threshold} {percent_last_mol}"
    return command


def run_final_phase(project_name, specifications):
    # TODO Update this to work with current version - THIS DOES NOT WORK YET

    # TODO Where is top_n used?
    user_info = read_info()
    num_iterations = specifications['total_iterations']
    num_cpu = specifications['num_cpu']
    project_path = user_info['project_path']  # the path to the project dir
    project_name = project_name  # the project name
    local_path = user_info['remote_path']  # the path to the scripts
    command = f"sbatch {local_path}/final_phase.sh " \
              f"{num_iterations} {num_cpu} {project_path} {project_name} {local_path}"
    return command


def read_top_hits(ssh):
    # open an ftp client to do work on the cluster
    ftp_client = ssh.ssh.open_sftp()

    # load up the data we have from installation
    info = read_info()
    try:
        return ftp_client.open(info['docking_path'] + "/GUI/top_hits.csv").readlines()
    except FileNotFoundError:
        return []


def read_final_top_hits(ssh, final_iteration_path):
    # open an ftp client to do work on the cluster
    ftp_client = ssh.ssh.open_sftp()
    print("Looking at", final_iteration_path + "/smiles.csv")
    try:
        return ftp_client.open(final_iteration_path + "/smiles.csv").readlines()
    except FileNotFoundError:
        return []


def slurm_clean():
    return "rm slurm*.out; rm GUI/slurm*.out"


def create_project(ssh,
                   project_name: str,
                   specifications: dict,
                   logfile_contents: dict):

    # open an ftp client to do work on the cluster
    ftp_client = ssh.ssh.open_sftp()

    # load up the data we have from installation
    with open('src/backend/db.json') as user_db:
        db = user_db.read()
        database = json.loads(db)

    # Fill in the partition as blank if it is just a default value
    specifications['partition'] = "" if specifications["partition"] == "Default" else specifications["partition"]
    specifications['current_phase'] = 1
    project_location = database['project_path'] + "/" + project_name
    new_project = {"location": project_location, "specifications": specifications, "log_file": logfile_contents}

    # create the project
    itr1_dir = project_location + "/iteration_1/"
    try:
        ftp_client.mkdir(project_location)
        ftp_client.mkdir(itr1_dir)
    except OSError:
        print("The project {} at {} already exists.".format(project_name, project_location))
        return -1

    # Create and populate the logs file
    log_txt = ftp_client.file(project_location + '/logs.txt', mode='w')
    log_txt.write(database['project_path'] + "\n")
    log_txt.write(project_name + "\n")
    log_txt.write(logfile_contents['grid_file'] + "\n")
    log_txt.write(logfile_contents['morgan_file'] + "\n")
    log_txt.write(logfile_contents['smile_file'] + "\n")
    log_txt.write(logfile_contents['sdf_file'] + "\n")
    log_txt.write(logfile_contents['docking_software'] + "\n")
    log_txt.write(str(logfile_contents['n_hyperparameters']) + "\n")
    log_txt.write(str(logfile_contents['n_molecules']) + "\n")
    log_txt.write(logfile_contents['glide_input'] + "\n")
    log_txt.close()

    # Save the new data to our database
    # TODO: Sibling files not recognizing each other when called from another file path.
    json_info = json.dumps(new_project)
    with open('src/backend/projects/{}.json'.format(project_name), 'w') as db:
        db.write(json_info)

    return 1
