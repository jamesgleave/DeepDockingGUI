"""
James Gleave
v1.0.3
"""

import json
import os
import sys
import time
from sys import platform
from getpass import getpass
sys.path.append('..')
from util.ProgressBar import ProgressBar


def install_dependencies(simulate):
    # TODO Split this function up in case a user only wants to redo parts of this installation process
    print_txt_message("welcome_message.txt")
    print("Welcome to the DeepDocking Installer\n")

    print("Before installing Deep Docking, we require you to have the required dependencies to run the GUI.")
    print("To do this, we will automatically create a new conda environment for you called DeepDockingLocal")
    if input("'y' to create or enter any other key to exit ") == 'y':
        # TODO Check the os and change this accordingly
        if not simulate:
            os.system("conda env create -f {}".format("DeepDockingLocal.yml"))
    else:
        exit()

    # Create venv and install dependencies
    print("Would you like to install the javascript dependencies for the GUI now?")
    if input("'y' to install or enter any other key to continue ") == 'y':
        # TODO Check to see that they have node installed
        err_code = os.system("cd ..; cd GUI; npm install")
        if err_code != 0:
            err_code = os.system("cd .. && cd GUI && npm install")



def install_deep_docking(simulate):
    # Now we can continue installing....
    print("To begin installing, we require you to log into your cluster")

    def login():
        login_info = input("Cluster username and IP (ex: johnsmith@111.209.108.241): ")
        while '@' not in login_info:
            print("Please re-enter a valid login:")
            login_info = input("Cluster username and IP (ex: johnsmith@111.209.108.241): ").strip(" ")
        password = getpass("Cluster password: ")
        ip = login_info.split("@")[1]
        user = login_info.split("@")[0]
        ssh = InstallationAssistant(host=ip)
        if not simulate:
            try:
                ssh.connect(user, password)
                print("\nLogging you in... Welcome, {}.".format(user))
                return True, ssh, ip
            except ssh.connection_exception:
                print("Login failed... please try again")
                return False, ssh, ip
        else:
            print("\nLogging you in... Welcome, {}.".format(user))
            return True, ssh, ip

    # Create a loop to log the user in despite making mistakes
    logged_in, connection, ip = login()
    while not logged_in:
        logged_in, connection, ip = login()

    print("Where would you like deep docking to be installed?")
    installation_path = input("Installation path: ").strip(" ")

    print("Would you like to create a conda virtual environment with all the python dependencies?")
    print("This requires you to have anaconda on your cluster. "
          "If you already have a virtual environment, you may skip this step.")
    if input("'y' to create or enter any other key to continue ") == 'y':
        # Create the venv on the cluster and save the activation command
        if not simulate:
            connection.create_venv()
        env_activation = "conda activate DeepDockingRemote"
        env_deactivation = "conda deactivate"
    else:
        # If we did not create a new conda env, we will
        print("Command to activate your virtual environment (ex: 'source activate my_env' or 'conda activate my_env')")
        env_activation = input("venv activation command: ")
        env_deactivation = input("venv deactivation command: ")

    # Save information
    docking_path = installation_path + "/DeepDocking/"
    remote_gui_path = docking_path + "/GUI/"
    local_dir = os.getcwd().strip('installation')

    # Grab the path to autodock
    path_to_autodock = input("Path to Autodock GPU: ")

    print("Installing...")
    if not simulate:
        connection.install(local_dir, installation_path, env_activation, env_deactivation)

    print("Finished Installing...")

    # Save installation information
    installation_information = {'remote_path': docking_path,
                                'local_dir': local_dir,
                                'ip': ip,
                                'docking_path': docking_path,
                                'remote_gui_path': remote_gui_path,
                                'env_activation_command': env_activation,
                                'path_to_autodock': path_to_autodock}

    json_info = json.dumps(installation_information)
    with open("installation_information.json", 'w') as file:
        file.write(json_info)

    # This is the information the backend of the gui will use
    # TODO check OS to specify the activation command (for now it just works for mac)
    local_activation_command = 'conda activate DeepDockingLocal'
    if platform == "linux" or platform == "linux2":
        # linux
        local_activation_command = 'conda activate DeepDockingLocal'
    elif platform == "darwin":
        # OS X
        local_activation_command = 'conda activate DeepDockingLocal'
    elif platform == "win32":
        # Windows...
        local_activation_command = 'conda activate DeepDockingLocal'

    installation_information['project_path'] = docking_path.replace("/DeepDocking/", "/DeepDockingProjects/")
    installation_information['env_deactivation_command'] = env_deactivation
    installation_information['local_env_activation_command'] = local_activation_command
    installation_information['username'] = connection.user
    json_info = json.dumps(installation_information)

    # Save the user information
    with open(local_dir + "/GUI/src/backend/db.json", 'w') as file:
        file.write(json_info)

    # Create a directory for the projects
    try:
        os.mkdir(local_dir + "/GUI/src/backend/projects")
    except FileExistsError:
        pass
    
    input("All done! You are good to go!")

def print_txt_message(text_file):
    txt_contents = open(text_file).readlines()
    welcome_message = ""
    for line in txt_contents:
        welcome_message += line
    print(welcome_message)


class InstallationAssistant:
    """ This class will automatically ssh into the host cluster. """

    def __init__(self, host):

        # The information that will allow for ssh
        self.host = host
        self.user = ""
        self.pwrd = ""
        self.ssh = None
        self.connection_exception = None

    def command(self, command):
        # Check if there is a connection
        assert self.ssh is not None, "Connect before using a command"

        # Send the command
        stdin, stdout, stderr = self.ssh.exec_command(command)
        return stdout

    def connect(self, username, password):
        import paramiko

        # Set the credentials
        self.user = username
        self.pwrd = password
        self.connection_exception = paramiko.SSHException

        # Connect to ssh and set out ssh object
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.host, username=self.user, password=self.pwrd)
        self.ssh = ssh

    def check_path(self, path):
        ftp_client = self.ssh.open_sftp()
        ftp_client.listdir(path)
        ftp_client.close()

    def create_venv(self):
        # TODO Create a bash script to install conda if the user does not have it yet

        # Build the commands to create the env
        creation_command = "conda create -n DeepDockingRemote -y python=3.6.8"
        specify = True if input("Specify library versions? (y/n) ") == 'y' else False
        install_tf = "pip install tensorflow-gpu"
        install_np = "pip install numpy"
        install_pd = "pip install pandas"
        install_skl = "pip install scikit-learn"
        while specify:
            print("Specify version or press enter to skip specification")
            # Specify tensorflow
            tf_version = input("- Tensorflow-GPU/Tensorflow version: ")
            if tf_version.strip(" ") != "":
                if int(tf_version.split(".")[0]) < 2:
                    install_tf = install_tf + "=={}".format(tf_version)
                else:
                    install_tf = "pip install tensorflow" + "=={}".format(tf_version)

            # Check if continue
            if input("Numpy, Pandas, and Scikit-Learn remain. Continue specifying (y/n)? ") == "n":
                break

            np_version = input("- Numpy version: ")
            if np_version.strip(" ") != "":
                install_np = install_np + "=={}".format(np_version)

            # Check if continue
            if input("Pandas and Scikit-Learn remain. Continue specifying (y/n)? ") == "n":
                break

            pd_version = input("- Pandas version: ")
            if pd_version.strip(" ") != "":
                install_pd = install_pd + "=={}".format(pd_version)

            # Check if continue
            if input("Scikit-Learn remains. Continue specifying (y/n)? ") == "n":
                break

            skl_version = input("- Scikit version: ")
            if pd_version.strip(" ") != "":
                install_skl = install_skl + "=={}".format(skl_version)
            break

        # Grab the cuda version
        cuda_version = input("Cuda driver version? cudatoolkit=")

        def write_to_out(addition):
            # create an output for the commands. This is useful for debugging issues with conda.
            with open("installation.out", "w") as output:
                for line in addition:
                    output.write(line)

        # Start creating the venv
        lines = []
        print("Creating Conda Environment.\nThis may take some time...")
        progress_bar = ProgressBar(11)
        progress_bar()

        # Create the conda env
        out = self.command(creation_command)
        lines += out.readlines()
        write_to_out(lines)
        progress_bar.current += 1
        progress_bar()

        # install tf
        out = self.command("conda activate DeepDockingRemote; " + install_tf)
        lines += out.readlines()
        write_to_out(lines)
        progress_bar.current += 1
        progress_bar()

        # install pybel
        out = self.command("conda activate DeepDockingRemote; pip install pybel")
        lines += out.readlines()
        write_to_out(lines)
        progress_bar.current += 1
        progress_bar()

        # install numpy
        out = self.command("conda activate DeepDockingRemote; " + install_np)
        lines += out.readlines()
        write_to_out(lines)
        progress_bar.current += 1
        progress_bar()

        # install pydot
        out = self.command("conda activate DeepDockingRemote; pip install pydot")
        lines += out.readlines()
        write_to_out(lines)
        progress_bar.current += 1
        progress_bar()

        # install openbabel
        out = self.command("conda activate DeepDockingRemote; conda install -c conda-forge openbabel")
        lines += out.readlines()
        write_to_out(lines)
        progress_bar.current += 1
        progress_bar()

        # install pandas
        out = self.command("conda activate DeepDockingRemote; " + install_pd)
        lines += out.readlines()
        write_to_out(lines)
        progress_bar.current += 1
        progress_bar()

        # install rdkit
        out = self.command("conda activate DeepDockingRemote; conda install -c conda-forge rdkit")
        lines += out.readlines()
        write_to_out(lines)
        progress_bar.current += 1
        progress_bar()

        # install sklearn
        out = self.command("conda activate DeepDockingRemote; " + install_skl)
        lines += out.readlines()
        write_to_out(lines)
        progress_bar.current += 1
        progress_bar()

        # install IPython
        out = self.command("conda activate DeepDockingRemote; pip install IPython")
        lines += out.readlines()
        write_to_out(lines)
        progress_bar.current += 1
        progress_bar()

        # install cuda tool kit
        out = self.command("conda activate DeepDockingRemote; conda install -c anaconda cudatoolkit={}".format(cuda_version))
        lines += out.readlines()
        write_to_out(lines)
        progress_bar.current += 1
        progress_bar()
        print()

    def install(self, local, remote, env_activation, env_deactivation):
        ftp_client = self.ssh.open_sftp()
        remote = remote + "/DeepDocking/"

        # Create the activation script
        with open(local + "/Docking/ProgressiveDocking/activation_script.sh", 'w') as activation_script:
            activation_script.write("echo Activating virtual environment\n")
            activation_script.write("source ~/.bashrc\n")
            activation_script.write(env_activation)

        # Create the deactivation script
        with open(local + "/Docking/ProgressiveDocking/deactivation_script.sh", 'w') as deactivation_script:
            deactivation_script.write("echo Deactivating virtual environment\n")
            deactivation_script.write("source ~/.bashrc\n")
            deactivation_script.write(env_deactivation)

        # Make the directories
        try:
            ftp_client.mkdir(remote)  # scripts dir
            ftp_client.mkdir(remote + "/ML")
            ftp_client.mkdir(remote + "/GUI")
            ftp_client.mkdir(remote + "/GUI/images")
            ftp_client.mkdir(remote + "/GUI/images/models")
        except OSError:
            print("The directory DeepDocking already exists at", remote)
            if input("Overwrite? If no, exit installation: y/n ").lower() in {'yes', 'y'}:
                # remove the dir (recursively) and make a new one
                stdin, stdout, stderr = self.ssh.exec_command("rm -rf "  + remote)
                while not stdout.channel.exit_status_ready():
                    time.sleep(5)
                ftp_client.mkdir(remote)  # scripts dir
                ftp_client.mkdir(remote + "/ML")
                ftp_client.mkdir(remote + "/GUI")
                ftp_client.mkdir(remote + "/GUI/images")
                ftp_client.mkdir(remote + "/GUI/images/models")
            else:
                exit()

        try:
            ftp_client.mkdir(remote.replace("/DeepDocking/", "/DeepDockingProjects/"))  # project dir
        except OSError:
            print("Project directory already exists.")

        # Start sending files to the cluster...
        docking_files = [x for x in os.walk(local + "/Docking/ProgressiveDocking/")][-1][-1]
        gui_files = [x for x in os.walk(local + "/Docking/GUI/")][-1][-1]
        ml_files = [x for x in os.walk(local + "/Docking/ML/")][-1][-1]
        total_files = len(docking_files) + len(gui_files) + len(ml_files)
        progress = ProgressBar(total_files, fmt=ProgressBar.FULL)

        # Installing docking files
        for fp in docking_files:
            file_path = local + "/Docking/ProgressiveDocking/" + fp
            ftp_client.put(file_path, remote + "/" + fp)
            progress.current += 1
            progress()

        # Installing GUI files
        for fp in gui_files:
            file_path = local + "/Docking/GUI/" + fp
            ftp_client.put(file_path, remote + "/GUI/" + fp)
            progress.current += 1
            progress()

        # Installing GUI files
        for fp in ml_files:
            file_path = local + "/Docking/ML/" + fp
            ftp_client.put(file_path, remote + "/ML/" + fp)
            progress.current += 1
            progress()

        progress.done()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-sim", required=False, default=False)
    parser.add_argument("--phase", required=True)
    args = parser.parse_args()
    phase = args.phase
    simulate = args.sim

    if phase == "install_local":
        # Start off by installing the local dependencies
        install_dependencies(simulate)

    if phase == "install_remote":
        # Now, install deep docking
        install_deep_docking(simulate)
