from auto_ssh import SSH
from backend import Backend
import time
import json


def check_backend():
    json_str = open('src/backend/db.json').read()  # TODO: Sibling files not recognizing each other when called from another file path.
    db_dict = json.loads(json_str)
    ip = db_dict['ip']

    user = input("cluster username: ")
    password = input("cluster password: ")
    ssh_connection = SSH(host=ip)
    ssh_connection.connect(username=user, password=password)
    backend = Backend(ssh=ssh_connection)
    return backend


def check_load_project():
    b = check_backend()
    b.load_project(input("Project Name: "))
    return b


def check_run_phase_5():
    b = check_backend()
    b.load_project(path_to_project=input("Path to project: "))
    b.run_phase(5, debug=True)


def check_run_phase_4():
    b = check_backend()
    b.load_project(path_to_project=input("Path to project: "))
    b.run_phase(4, debug=True)


def check_venv():
    b = check_backend()
    b.send_command("python venv_sanity_check.py", debug=True)
    b.send_command("conda list >> test_check.txt", debug=True)


def check_backend_functionality():
    b = check_backend()
    p = input("Project Name: ")
    b.load_project(project_name=p)
    b.start()

    while b.status() == "fetching":
        pass

    hist = b.pull()
    print(hist.current_phase_eta)


def check_run_phase():
    b = check_backend()
    b.load_project(path_to_project=input("Path to project: "))
    b.start()
    while b.status() == "fetching":
        pass

    while True:
        phase = int(input("Which phase to run? "))
        if input("Debug? y or n ") == "n":
            b.run_phase(phase, False)


def check_model_image():
    b = check_load_project()
    b.get_model_image(1, 3)


def check_final_phase():
    b = check_backend()
    project_name = input("Project Name: ")
    b.load_project(project_name)
    b.start()
    while b.status() == "fetching":
        pass
    b.run_phase(phase=-1, debug=True)


def check_read_final():
    b = check_backend()
    project_name = input("Project Name: ")
    b.load_project(project_name)
    b.start()
    while b.status() == "fetching":
        pass

    print(b.get_final_phase_results())


def check_except():
    b = check_backend()
    project_name = input("Project Name: ")
    b.load_project(project_name)
    b.start()
    while b.status() == "fetching":
        pass

    print(b.core.model_data.keys())
    print(b.core.model_data["iteration_1"]['itr']['crash_report'])


def check_update_specs():
    b = check_backend()
    project_name = input("Project Name: ")
    b.load_project(project_name)
    specs = {"num_cpu": 24}
    b.update_specifications(specs)


def check_itr_percent():
    b = check_backend()
    project_name = input("Project Name: ")
    b.load_project(project_name)
    print(b.pull())
