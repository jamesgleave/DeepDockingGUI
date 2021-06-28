"""
Backend for DD GUI
James Gleave
1.4

TODO After the first we have finished the prototype, I will make large scale changes to the backend and the cluster.
"""
from __future__ import print_function

try:
    from .DataHistory import DataHistory
    from .backend_exceptions import *
    from .cluster_commands import *
except:
    from DataHistory import DataHistory
    from backend_exceptions import *
    from cluster_commands import *

import threading
import pickle
import json
import time
import os


class Colours:
    HEADER = '\033[95m'
    OK_BLUE = '\033[94m'
    OK_CYAN = '\033[96m'
    OK_GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Core:
    def __init__(self, ssh_connection):
        self.clock_rate = 0.1
        self.update_rate = 30
        self.updating = False
        self.clock = 0
        self.num_updates = 0
        self.running = True
        self.model_data = {}
        self.__ssh_connection = ssh_connection

        # Project information
        self.project_loaded = False
        self.loaded_project_name = ""
        self.loaded_project_information = {}

        # For updating
        # TODO: Sibling files not recognizing each other when called from another file path.
        self.user_data = json.loads(open('src/backend/db.json').read())
        self.update_path = self.user_data['remote_gui_path'] + "update_gui.sh "
        self.update_command = "bash " \
                              + self.update_path \
                              + self.user_data['project_path'] \
                              + "/" + self.loaded_project_name \
                              + " " + self.user_data['remote_gui_path'] \
                              + " " + self.__ssh_connection.user

    def start(self):
        self.running = True
        while self.running:
            self.update()
            self.clock += self.clock_rate
            time.sleep(self.clock_rate)

    def stop(self):
        self.updating = False
        self.clock = 0
        self.num_updates = 0
        self.running = False
        self.model_data = {}

        # Clear project data
        self.project_loaded = False
        self.loaded_project_name = ""
        self.loaded_project_information = {}
        print("project stopped!")

    def update(self, forced=False, verbose=1):
        update_condition = (round(self.clock, 2) % self.update_rate == 0 and
                            not self.updating)
                                    
        # Here we update the user data and the project data to be read by the backend
        self.user_data = json.loads(open('src/backend/db.json').read())
        self.update_path = self.user_data['remote_gui_path'] + "update_gui.sh "
        self.update_command = "bash " \
                              + self.update_path \
                              + self.user_data['project_path'] \
                              + "/" + self.loaded_project_name \
                              + " " + self.user_data['remote_gui_path'] \
                              + " " + self.__ssh_connection.user

        # Updating project information by reading the json file associated with the currently loaded project.
        self.loaded_project_information = json.loads(open('src/backend/projects/{}.json'.format(
            self.loaded_project_name)).read()
            )

        debug_message = "\n" + Colours.HEADER + "Updating Data:\n"
        if update_condition or forced:
            self.updating = True
            self.num_updates += 1
            start_time = time.time()

            # Generate the pickle in the GUI folder
            activation_command = activate_venv() + "; "
            command = f"cd {self.user_data['remote_path']}; " + activation_command + self.update_command + " >| update.log 2>&1"
            out = self.__ssh_connection.command(command)  # Run the command and generate the pickle

            # Create the debug message for the updating command
            debug_message += Colours.OK_BLUE + "\nSending Update Command:\n"
            debug_message += Colours.OK_CYAN + command + "\n\n"

            # wait for the command to finish
            if self.model_data == {}:
                out.read()
                debug_message += Colours.OK_CYAN + "- There is no data yet so we must gather it...\n"
            if forced:
                out.read()

            # Read the pickle from the remote computer
            try:
                # First, try to read the file from the cluster,
                pickle_name = "{}_data.pickle".format(self.__ssh_connection.user)
                # Get the path to the pickle (in the user's directory)
                user_path = f"/Users/{self.__ssh_connection.user}/"
                # Read the pickle off the remote cluster
                pickled_data = self.__ssh_connection.read(self.user_data['remote_gui_path'] + user_path + pickle_name)
                # add to the debug message
                debug_message += Colours.OK_CYAN + "- Reading data from the cluster...\n"
                # load the data from the pickle and add to the debug message
                self.model_data = pickle.load(pickled_data)
                debug_message += Colours.OK_GREEN + "- Loading the data was successful!\n"
            except FileNotFoundError:
                debug_message += Colours.FAIL + "- No model data present!\n"
                self.model_data = {}
            except UnicodeDecodeError or KeyError as e:
                debug_message += Colours.FAIL + "- There was a problem getting the data!\n"
                debug_message += Colours.FAIL + f"  - {e}\n"
            except Exception as e:
                debug_message += Colours.FAIL + "- There was an unexpected problem getting the data!\n"
                debug_message += Colours.FAIL + f"  - {e}\n"

            """Here we are updating the current iteration in the project file if it has been changed."""
            current_iteration = len(self.model_data.keys())
            
            if self.loaded_project_information['specifications']['iteration'] != current_iteration:
                self.loaded_project_information['specifications']['iteration'] = current_iteration

                # Check to see if it is the final iteration
                if current_iteration == self.loaded_project_information['specifications']['total_iterations']:
                    self.loaded_project_information['specifications']['is_final_iteration'] = True

                with open('src/backend/projects/{}.json'.format(self.loaded_project_name), 'w') as new_db:
                    new_db.write(json.dumps(self.loaded_project_information))

                # Change in iterations
                debug_message += Colours.OK_BLUE + "- Iteration Change Detected - Current Iteration: " + str(current_iteration) + "\n"
            else:
                # No change detected
                debug_message += Colours.OK_GREEN + "- Current Iteration: " + str(current_iteration) + "\n"

            """Here we are updating the current phase in the project file if it has been changed."""
            try:
                current_phase = self.model_data[list(self.model_data.keys())[-1]]["itr"]["current_phase"]
                if self.loaded_project_information['specifications']['current_phase'] != current_phase:
                    self.loaded_project_information['specifications']['current_phase'] = current_phase
                    with open('src/backend/projects/{}.json'.format(self.loaded_project_name), 'w') as new_db:
                        new_db.write(json.dumps(self.loaded_project_information))

                    # Change detected
                    debug_message += Colours.OK_BLUE + "- Phase Change Detected - Current Phase: " + str(current_phase) + "\n"
                else:
                    # No change detected
                    debug_message += Colours.OK_GREEN + "- Current Phase: " + str(current_phase) + "\n"
            except IndexError:
                pass

            """
            Note the try catch is present because these values will only be present if we have had at least one update.
            Here we are adding the error information to the debug display and also updating the
            total percentage
            """
            try:
                # Add error info to the log message
                error_info = self.model_data["iteration_" + str(current_iteration)]['itr']['crash_report']
                if len(error_info) > 0:
                    debug_message += Colours.WARNING + "- Error Information " + \
                                     self.model_data["iteration_" +
                                                     str(current_iteration)]['itr']['crash_report'][-1]['traceback'] + "\n"
                else:
                    debug_message += Colours.OK_GREEN + "- No Errors" + "\n"

                """
                Update and calculate the full run percent complete since we know the total iterations here.
                This section uses the information gotten from each update to determine the total completeiton 
                percentage.
                """
                total_iterations = int(self.loaded_project_information['specifications']['total_iterations'])
                # This is an integer plus a percentage -> iteration_x.iteration_(x+1)_percent_complete
                complete = self.model_data["iteration_" + str(current_iteration)]['itr']['itr_percent'] + current_iteration
                # complete - 1 because we have "complete" itr. inclusive
                full_percent = max((complete - 1) / total_iterations, 0)

                # If the final phase is not locked, then we must be finished
                if self.model_data["iteration_" + str(current_iteration)]['itr']['final_phase'] != "locked":
                    full_percent = 1

                # Add the full percent
                self.model_data["iteration_" + str(current_iteration)]['itr']['full_percent'] = round(full_percent, 3)

                # Add the calculated full run percent and the itr run percent to the debug log
                debug_message += Colours.OK_GREEN + "- Iteration percent complete: " + \
                                 str(100 *
                                     self.model_data["iteration_" + str(current_iteration)]['itr'][
                                         'itr_percent']) + "%\n"
                debug_message += Colours.OK_GREEN + "- Full run percent complete: " + \
                                 str(100 * self.model_data["iteration_" + str(current_iteration)]['itr'][
                                     'full_percent']) + "%\n"

                # If we are fully finished every iteration, we can show the progress of the final extraction
                if int(full_percent) == 1:
                    status = self.model_data["iteration_" + str(current_iteration)]['itr']['final_phase']
                    # If the full run is finished the iteration percentage should be set to 1
                    self.model_data["iteration_" + str(current_iteration)]['itr']['itr_percent'] = 1
                    debug_message += Colours.OK_GREEN + "- Final Extraction -> " + status + "\n"
            except KeyError:
                pass

            # Conclude the update
            end_time = time.time()
            debug_message += Colours.OK_CYAN + "- Time taken during update: " + str(end_time - start_time) + "\n"
            debug_message += Colours.OK_GREEN + "- Update " + str(self.num_updates) + " Successful\n"
            self.clock = 1
            self.updating = False

            if verbose > 0:
                self.__debug_print(debug_message)

    def force_update(self, header=None, verbose=1):
        debug_message = ""
        if header is None:
            header = "Forced Update:\n"
        debug_message += Colours.HEADER + header + "\n"

        self.clock = 1
        self.update(forced=True)

        if verbose > 0:
            self.__debug_print(message=debug_message)

    def get_model_data(self):
        return self.model_data

    @staticmethod
    def __debug_print(message):
        print(message + "\033[0;0m")

    @staticmethod
    def __isfloat(value):
        # Returns True if float and False otherwise
        try:
            float(value)
            return True
        except ValueError:
            return False


class Backend:
    def __init__(self, ssh):
        """
        The main backend for the deep docking gui
        """
        # These are the threads to the core
        self.ssh = ssh
        self.core = Core(self.ssh)
        self.thread = None

        # The model data
        self.models = None
        self.current_model = 0

        # Current iteration
        self.current_iteration = 1
        self.current_phase = 1

        # the connection to the cluster
        self.short_cache = {"hyperparameters": None, "previous_command": None, "top_hits": []}
        try:
            self.user_data = json.loads(open('src/backend/db.json').read())
            self.loaded_project = ""
            self.project_data = {}
        except FileNotFoundError as e:
            print(e.__traceback__, "'db.json' not found! Please run the installation first before running GUI.")

    def start(self):
        # Starts the thread and runs the core
        if self.core.project_loaded:
            self.thread = threading.Thread(target=self.core.start)
            self.thread.start()
        else:
            raise NullProjectException()

    def reset(self):
        self.core.stop()

    def pull(self) -> DataHistory:
        dh = DataHistory(self.core.get_model_data())
        return dh

    def status(self):
        core_status = len(self.core.model_data.keys())
        return "fetching" if core_status == 0 else "ready"

    """ The following section of the backend deals with user interaction with the cluster"""
    def send_command(self, command, debug=False, redirect=True):
        cd = "cd {}; ".format(self.user_data['docking_path'])

        # We sometimes want the stdout so do not always redirect it
        if redirect:
            command = cd + command + " >| previous_command.log 2>&1"
        else:
            command = cd + command

        stdout = self.ssh.command(command)
        if debug:
            print("stdout:", stdout.read())
            print("Command:", command)

        # Cache the command and return the standard output
        self.short_cache['previous_command'] = command
        return stdout

    def get_model_image(self, iteration, model):
        """Generates and downloads model image and returns local path"""
        assert type(model) is int and type(iteration) is int
        start_time = time.time()

        # Build our command
        command_prefix = "{}; python GUI/generate_images.py ".format(self.user_data['env_activation_command'])
        command_args = "-imof model --path_to_model {path_to_model}".format(
            path_to_model=
            self.user_data['project_path'] +
            "/{}/iteration_{}/all_models/model_{}".format(self.loaded_project, iteration, model))

        # Send command
        command = command_prefix + command_args

        # Decode output then return the image and hyperparameters
        stdout = self.send_command(command, debug=False, redirect=False)
        decoded_output = stdout.read().decode('ascii').replace("\n", "").split("&&&")
        file_name = self.user_data['docking_path'] + "/" + decoded_output[0]
        hyperparameters = json.loads(decoded_output[1].replace("'", '"'))

        print("Time taken to grab model image:", time.time()-start_time, "seconds.")
        self.short_cache["hyperparameters"] = hyperparameters
        return self.ssh.get_image(file_name), hyperparameters

    def get_top_hits(self):

        # Store current iteration
        current_iteration = self.project_data['specifications']['iteration']

        # Since the search happens at the very end of an iteration, we gotta look in the previous iteration directory
        current_iteration -= 1 if current_iteration > 1 else 0

        # Get the full path to the project:
        itr = f"/{self.loaded_project}/iteration_{current_iteration}"
        fp = self.user_data['project_path'] + itr

        # Reads the top_hits.csv file generated at the end of phase 5
        lines = read_top_hits(self.ssh, fp)
        smiles = []

        # Loop through the smiles
        for line in lines[1:]:
            smile, _ = line.split(",")
            smiles.append(smile)

        # If we have top hits, we save them to the short cache
        if len(smiles) > 0:
            self.short_cache["top_hits"] = smiles
        elif len(smiles) == 0 and len(self.short_cache["top_hits"]) > 0:
            # If there are no smiles found, and we have smiles in the short cache, return the previously found smiles
            smiles = self.short_cache["top_hits"]

        return smiles

    def get_final_phase_results(self):
        # Reads the top_hits.csv file generated at the end of docking
        lines = read_final_top_hits(self.ssh, self.user_data['project_path'] +
                                    f"/{self.loaded_project}/"
                                    f"iteration_{self.project_data['specifications']['iteration']}")
        smiles = []

        # Loop through the smiles
        for line in lines[1:]:
            _, smile, _ = line.split(" ")
            if smile == "": 
                break
            smiles.append(smile)
        return smiles

    def update_user_info(self):
        """Updates the user info by reading the database json file and the project file"""
        # TODO: Sibling files not recognizing each other when called from another file path.

        # Update the data in the backend
        self.user_data = json.loads(open('src/backend/db.json', 'r').read())
        self.project_data = json.loads(open('src/backend/projects/{}.json'.format(self.loaded_project), 'r').read())

        # Update the data in the core
        # I will eventually use the core to store the data entirely for I know this is redundant. It is just very
        # small amounts of data.
        self.core.loaded_project_name = self.loaded_project

    def update_specifications(self, specifications: dict):
        """
        Updates the specifications for starting a run (num cpu, etc)
        specifications =
        {"iteration": ...,
        "partition": "...",
        "total_iterations": ...,
        "num_cpu": ...,
        "is_final_iteration": ...,
        "licences": ...,
        "top_n": ...,
        "sample_size": ...,
        "optimize_models": ...}
        """
        # preprocessing the data:
        specifications['partition'] = '""' if specifications["partition"] == "Default"  else specifications["partition"]

        # Update the user info
        self.update_user_info()

        # Update the specifications
        for key in specifications:
            self.project_data['specifications'][key] = specifications[key]
            print(key, "has been updated to", specifications[key])

        # TODO: Sibling files not recognizing each other when called from another file path.
        with open('src/backend/db.json', 'w') as new_db:
            new_db.write(json.dumps(self.user_data))

        with open(f'src/backend/projects/{self.loaded_project}.json', 'w') as new_db:
            new_db.write(json.dumps(self.project_data))

        # Joining the headers (seperated by user inputted #SBATCH)
        headers = headers = "".join(self.project_data["specifications"]['slurm_headers'])

        # update the files on the cluster
        command = "python3 {}/setup_slurm_specifications.py --path {} --n_cpu {} --partition {} --custom_headers {} --project_name {}"
        command = command.format(self.user_data["remote_path"],
                                 self.user_data["remote_path"],
                                 self.project_data["specifications"]["num_cpu"],
                                 '"{}"'.format(self.project_data["specifications"]["partition"]),
                                 '"{}"'.format(headers), self.loaded_project)
        stdout = self.send_command(command, debug=True)

    def create_new_project(self, project_name, log_file_contents, specifications):
        """Creates a new project in the deep docking project directory"""
        out = create_project(ssh=self.ssh,
                             project_name=project_name,
                             logfile_contents=log_file_contents,
                             specifications=specifications)

        # Set the loaded project
        self.loaded_project = project_name

        # Update the user info
        self.update_user_info()

        # If the jobs are running, we must cancel them before loading another project
        if self.core.project_loaded:
            # self.cancel_jobs()
            pass

        # Tell the core that we have a project loaded
        self.core.project_loaded = True

        # If the core is running, then force an update.
        if self.core.running:
            log_message = "Forced Update:\n" \
                          " - Reason: Creating New Project"
            self.core.force_update(header=log_message)

        # Joining the headers (seperated by user inputted #SBATCH)
        headers = headers = "".join(specifications["slurm_headers"])

        # update the files on the cluster
        command = "python3 {}/setup_slurm_specifications.py --path {} --n_cpu {} --partition {} --custom_headers {} --project_name {}"
        command = command.format(self.user_data["remote_path"],
                                 self.user_data["remote_path"],
                                 specifications["num_cpu"],
                                 '"{}"'.format(specifications["partition"]),
                                 '"{}"'.format(headers), self.loaded_project)
        stdout = self.send_command(command, debug=True)
        return out

    def load_project(self, project_name):
        """Load up an old project"""

        # Set the loaded project
        self.loaded_project = project_name

        # Update the user info
        self.update_user_info()

        # If the jobs are running, we must cancel them before loading another project
        if self.core.project_loaded:
            # self.cancel_jobs()
            pass

        # Tell the core we have a project loaded
        self.core.project_loaded = True
        
        # If the core is running, then force an update.
        if self.core.running:
            log_message = "Forced Update:\n" \
                          " - Reason: Loading Project"
            self.core.force_update(header=log_message)

        
        # Joining the headers (seperated by user inputted #SBATCH)
        headers = headers = "".join(self.project_data["specifications"]['slurm_headers'])

        # update the files on the cluster
        command = "python3 {}/setup_slurm_specifications.py --path {} --n_cpu {} --partition {} --custom_headers {} --project_name {}"
        command = command.format(self.user_data["remote_path"],
                                 self.user_data["remote_path"],
                                 self.project_data["specifications"]["num_cpu"],
                                 '"{}"'.format(self.project_data["specifications"]["partition"]),
                                 '"{}"'.format(headers), self.loaded_project)
        stdout = self.send_command(command, debug=True)

        print("Project Loaded; Updated Specs:")
        for line in stdout.read().decode('ascii').split("\n"):
            print(" -  " + line)

        return 1

    def get_specifications(self):
        """Returns the specifications stored in project.json"""
        self.update_user_info()
        return self.project_data

    def cancel_jobs(self):
        """Cancels all jobs the user is running. Warning: this will not only cancel deep docking jobs."""
        command = f"python3 {self.user_data['remote_path']}/reset.py " \
                  f"--project_name {self.loaded_project} " \
                  f"--username {self.user_data['username']} " \
                  f"--remove_slurms False" \
                  f"--scripts {self.user_data['docking_path']}"
        self.send_command(command, False)

    def run_phase(self, phase, debug=False):
        """Run any phase from 1-5 or all of them"""

        # Update our user information
        self.update_user_info()

        command = ""
        if str(1) == str(phase):
            command = run_phase_1(project_name=self.loaded_project,
                                  specifications=self.project_data['specifications'],
                                  logs=self.project_data['log_file'])
        if str(2) == str(phase):
            command = run_phase_2(project_name=self.loaded_project,
                                  specifications=self.project_data['specifications'],
                                  logs=self.project_data['log_file'])
        if str(3) == str(phase):
            command = run_phase_3(project_name=self.loaded_project,
                                  specifications=self.project_data['specifications'],
                                  logs=self.project_data['log_file'])
        if str(4) == str(phase):
            command = run_phase_4(project_name=self.loaded_project,
                                  specifications=self.project_data['specifications'],
                                  logs=self.project_data['log_file'])
        if str(5) == str(phase):
            command = run_phase_5(project_name=self.loaded_project,
                                  specifications=self.project_data['specifications'],
                                  logs=self.project_data['log_file'])
        if str(0) == str(phase):
            command = run_all_phases(project_name=self.loaded_project,
                                     specifications=self.project_data['specifications'],
                                     logs=self.project_data['log_file'])
        if str(-1) == str(phase):
            command = run_final_phase(self.loaded_project, self.project_data['specifications'])

        # Create a debug message
        if phase == 0:
            log_phase = "a"
        elif phase == -1:
            log_phase = "f"
        else:
            log_phase = phase
        log_message = f"Forcing Update:\n"\
                      f" -  Reason: Running phase {log_phase}"

        # Before we run this phase, we should reset it for a fresh start
        # self.reset_phase(phase)

        if not debug:
            out = self.send_command(command, False)
            out.read()
        else:
            print(command)

        # Update the backend right away
        self.core.force_update(header=log_message)

    def reset_phase(self, phase=None):

        # Update the user info
        self.update_user_info()

        # Grab the current iteration and phase
        phase = self.core.loaded_project_information['specifications']['current_phase'] if phase is None else phase
        if phase == 0:
            phase += 1

        iteration = self.core.loaded_project_information['specifications']['iteration']

        # Used to reset a phase if it fails TODO: USE SBATCH INSTEAD? TO KEEP TRACK?
        command = f"bash reset{phase}.sh " \
                  f"{self.user_data['project_path']}/{self.loaded_project}/iteration_{iteration} " \
                  f"{self.loaded_project} " \
                  f"{self.user_data['username']} " \
                  f"{self.user_data['docking_path']}"

        print(command)
        out = self.send_command(command, False)
        log_message = f"Forcing Update:\n" \
                      f" -  Reason: Resetting phase {phase}"

        # Return the output and wait until the operation is finished
        output = out.read()

        # Update the backend right away
        self.core.force_update(header=log_message)

        return output

    def delete_project(self, project_name=None):
        # Getting project name if not specified
        project_name = self.core.loaded_project_name if project_name is None else project_name
                
        # Stop the core 
        self.core.stop()
        
        # Cancel all jobs
        self.cancel_jobs()

        # Delete the project from the cluster
        self.send_command(f"rm -r {self.user_data['project_path']}/{project_name}", False)

        # Remove the project file
        os.remove(f"src/backend/projects/{project_name}.json")

        # Reset values back to their original
        # These are the threads to the core
        self.thread = None

        # The model data
        self.models = None
        self.current_model = 0

        # Current iteration
        self.current_iteration = 1
        self.current_phase = 1

        # the connection to the cluster
        self.short_cache = {"hyperparameters": None, "previous_command": None}
        self.loaded_project = ""
        self.project_data = {}
