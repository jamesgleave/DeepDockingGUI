import sqlite3
from flask import Flask, request, render_template, send_from_directory, send_file, jsonify
from flask_cors import CORS, cross_origin
from flask import Flask

from rdkit import Chem
from rdkit.Chem.Draw import MolToImage
from rdkit.Chem.Scaffolds import MurckoScaffold

from io import StringIO, BytesIO
import paramiko
import time
import json
import os

from src.backend import *


# Ask user if they want to open the DD website automatically
# import webbrowser
# prompt = "\nOpen Website On Default Browser? \nEnter y to launch or any other key to open manually: "
# open_site = True if input(prompt).rstrip() == "y" else False
# if open_site:
#     webbrowser.open("http://127.0.0.1:5000/")
# else:
#     print("Enter the proved link into your browser.")


app = Flask(__name__, static_url_path='/', static_folder='/')
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


# Initalizing the ssh class for connections:
ssh = SSH() # Automatically gets ip address from db.json 
BACKEND = None

MODE_SCAFFOLD = None
PROJECTS_PATH = './src/backend/projects/'

def serve_pil_image(pil_img):
    img_io = BytesIO()
    pil_img.save(img_io, 'JPEG', quality=95) # Quality ranges from 1 to 95
    img_io.seek(0)
    return img_io

def smileToMurckoScaffoldImage(smile):
    # Returns a PIL image of the given smile.
    m1 = Chem.MolFromSmiles(smile)
    core = MurckoScaffold.GetScaffoldForMol(m1)
    return MolToImage(core, size=(700, 700)) # image

def getModeMurckoScaffoldImage(SMILES_list):
    """
    returns the most common murcko scaffold given a list of smiles as an rdkit image.
    """
    murckoScaffolds = []

    # Looping through and getting the scaffolds for each smile
    for smile in SMILES_list:
        m1 = Chem.MolFromSmiles(smile)
        core = MurckoScaffold.GetScaffoldForMol(m1)
        murckoScaffolds.append(core)

    # Finding the mode Scaffold:
    mode = max(set(murckoScaffolds), key=murckoScaffolds.count)
    PIL_img_mode = MolToImage(mode, size=(700, 700))
    return PIL_img_mode

@app.route('/')
@cross_origin()
def login():
    return render_template("login.html")

@app.route('/main')
def main():
    return render_template("mainPage.html")

@app.route('/sshConnect', methods=["POST"])
def connect():
    if (request.is_json):
        content = request.json
    else:
        raise Exception('Error format is not json')

    try:
        ssh.connect(content['user'], content['pwd'])
        print("Login Successful")
    except paramiko.ssh_exception.AuthenticationException:
        return "creds", 401  # incorrect creds
    except (ConnectionError, TimeoutError) as e:
        return  "vpn", 401  # VPN on?
    
    global BACKEND
    BACKEND = Backend(ssh)

    return {}, 200

@app.route('/getBasics', methods=['GET'])
def getBasics():
    global BACKEND
    data = {}
    try:
        update_rate_ms = BACKEND.core.update_rate * 1000
        data['update_rate_ms'] = update_rate_ms
    except AttributeError:
        print("USER IS NOT YET LOGGED IN")

    return jsonify(data), 200

@app.route('/topScoring', methods=['POST'])
def topScoring():
    param = request.get_json()
    sendImage = param['image'] == 'true'
    smile = param["smile"]

    global BACKEND, MODE_SCAFFOLD
    data = {}

    if sendImage and smile != "undefined":
        # Get the selected smile when given:
        img_io = serve_pil_image(smileToMurckoScaffoldImage(smile))
        return send_file(img_io, mimetype='text/plain'), 200
    elif sendImage and MODE_SCAFFOLD is not None:
        # displaying mode when not given a smile
        img_io = serve_pil_image(MODE_SCAFFOLD)
        return send_file(img_io, mimetype='text/plain'), 200
    else:
        # getting the list of molecules to return or extract the mode from
        DATA_HISTORY = BACKEND.pull()
        if DATA_HISTORY.final_phase == "finished": # different list for final phase
            try:
                SMILES_list = BACKEND.get_final_phase_results()
            except:
                SMILES_list = BACKEND.get_top_hits()
        else:
            SMILES_list = BACKEND.get_top_hits()

        if sendImage:
            # Getting most common murckoscaffold when none provided
            MODE_SCAFFOLD = getModeMurckoScaffoldImage(SMILES_list)
            img_io = serve_pil_image(MODE_SCAFFOLD)
            return send_file(img_io, mimetype='text/plain'), 200
        else:
            # getting only the smiles list
            data['top_hits'] = SMILES_list
            return data, 200

@app.route('/progressData', methods=['GET'])
def getProgressData():
    global BACKEND
    try:
        DATA_HISTORY = BACKEND.pull()
    except (KeyError, AttributeError):
        return {}, 404
    
    data = {}
    
    # Getting current iteration and phase data:
    iterNum = int(DATA_HISTORY.current_iteration[10:]) # Getting rid of 'iteration_'
    # Will always return at least 1
    phaseNum = DATA_HISTORY.current_phase 

    data['is_idle'] = DATA_HISTORY.is_idle  # tells us if anything is currently running
    data['pending'] = DATA_HISTORY.pending
    data['currentInfo'] = {'iter': iterNum, 'phase': phaseNum}

    ETAs = {
        "full": round(DATA_HISTORY.full_percent * 100, 2),
        "iter": round(DATA_HISTORY.itr_percent * 100, 2),
        "phase": DATA_HISTORY.current_phase_eta,
        "final_phase": DATA_HISTORY.final_phase
    }
    data['ETAs'] = ETAs

    # Getting x and y data for the molecules remaining chart:
    molec_remaining = DATA_HISTORY.molecules_remaining

    # Extracting as list for the chart:
    modelPred = []
    actual = []
    x_values = [x for x in range(1, int(iterNum)+1)]
    for x in x_values:
        item = molec_remaining['iteration_'+str(x)]
        # Making sure that we are not adding placeholder numbers(-1)
        if item['estimate'] != -1 and item['true'] != -1:
            modelPred.append(item['estimate'])
            actual.append(item['true'])
        else: # removing from list
            x_values.remove(x)

        
    # print("molec remaining: ", DATA_HISTORY.molecules_remaining)
    data['molecRemainingData'] = {'modelPred': {'x': x_values, 'y': modelPred},
                                    'actual': {'x': x_values, 'y': actual}}
    return jsonify(data), 200

@app.route('/modelData', methods=['GET'])
def getModelData():
    # Extracting arguments form url:
    selectedIter = 'iteration_' + request.args['iteration'] # starts at 1 (not zero indexed)
    selectedModel = int(request.args['model'])              # same ^
    averaged = request.args['averaged'] == 'true'
    carousel = int(request.args['carousel']) # The chosen chart to display in carousel

    # Getting data from cluster
    global BACKEND
    DATA_HISTORY = BACKEND.pull() 
    data = {}
    plots = DATA_HISTORY.averages[selectedIter] if averaged else DATA_HISTORY.plots[selectedIter][selectedModel-1]
    titles = [x for x in plots.keys()]
    titles.remove('Time Per Epoch')
    titles.remove('Estimate Time')
    titles = [t for t in titles if "Validation" not in t]

    if carousel >= len(titles):
        return {}, 404

    else:
        metric = titles[carousel]
        title = "Model " + metric
        train_label = "Training " + metric
        valid_label = "Validation " + metric

        train_key = metric
        valid_key = "Validation " + metric

        x_range = [x for x in range(1, len(plots[train_key]) + 1)]
        carouselData = {
            'title': title,
            'xAxis': "Epochs",
            'labels': x_range,
            'datasets': [{
                'label': train_label,
                'data': plots[train_key]
            }, {
                'label': valid_label,
                'data': plots[valid_key]
            }]
        }

        rightData = [
            {
                'title': 'Time Per Epoch',
                'xAxis': "Epochs",
                'yAxis': "Time (s)",
                'labels': [x for x in range(1, len(plots['Time Per Epoch']) + 1)],
                'datasets': [{
                    'label': 'Time (s)',
                    'data': plots['Time Per Epoch']
                }]
            }, {
                'title': "Estimated Time Remaining",
                'xAxis': "Epochs",
                'yAxis': "Time (s)",
                'labels': [x for x in range(1, len(plots['Estimate Time']) + 1)],
                'datasets': [{
                    'label': 'Time (s)',
                    'data': plots['Estimate Time']
                }]
            }
        ]
        print("Grouped data...")
        data['carouselData'] = carouselData
        data['rightData'] = rightData

        data['numCharts'] = len(titles) - 1  # The num options for charts that can be displayed in the carousel
        data['numIterations'] = int(DATA_HISTORY.current_iteration[10:])
        data['currentPhase'] = DATA_HISTORY.current_phase # this is needed so that we know when to show data
        data['numModels'] = len(DATA_HISTORY.plots[selectedIter])

        return jsonify(data), 200

@app.route('/modelArch', methods=['POST', 'GET']) # must be a post so that it can change the cached hyp.
def getModelArch():
    # Extracting arguments form url:
    selectedIter = int(request.args['iteration'])   # Starts at 1 not zero indexed
    selectedModel = int(request.args['model'])      # ^
    sendImage = request.args['image'] == 'true' # If true then we only return the image
    
    global BACKEND

    if sendImage:
        # Getting data from cluster
        image, _ = BACKEND.get_model_image(selectedIter, selectedModel)
        
        img_io = serve_pil_image(image)
        
        return send_file(img_io, mimetype='text/plain'), 200

    else: # If false then we only send the hyperparameters 
        # Must be done IN ORDER so that we grab the image first and 
        # then 'GET' request the hyperparameters:
        hyp = BACKEND.short_cache['hyperparameters']

        return jsonify(hyp), 200

@app.route('/loadProject', methods=['POST'])
def loadProject():
    project_name = request.args['projectName']
    BACKEND.load_project(project_name)
    BACKEND.start()

    while BACKEND.status() == "fetching":
        if BACKEND.core.num_updates > 1 and BACKEND.core.model_data == {}:
            BACKEND.reset()
            return {}, 404
        time.sleep(1)
    DATA_HISTORY = BACKEND.pull() # forces it to finish
    return {}, 200

@app.route('/newProject', methods=['POST'])
def newProject():
    arguments = request.get_json()

    global BACKEND

    BACKEND.create_new_project(project_name=arguments['project_name'],
                         specifications={"iteration": 1,
                                         "is_final_iteration": False,
                                         "licences": 280,
                                         "optimize_models": False,
                                         'num_cpu': arguments['num_cpu'], 
                                         'partition': arguments['partition'], 
                                         'total_iterations': arguments['total_iterations'], 
                                         'threshold': arguments['threshold'], 
                                         'percent_last_mol': arguments['percent_last_mol'], 
                                         'percent_first_mol': arguments['percent_first_mol'], 
                                         'sample_size':arguments['sample_size'], 
                                         'top_n': arguments['top_n'], 
                                         'num_energy_evaluations': arguments['num_energy_evaluations'], 
                                         'num_runs': arguments['num_runs'], 
                                         'num_chunks': arguments['num_chunks'], 
                                         'path_to_fld': arguments['path_to_fld'],
                                         'slurm_headers': arguments['slurm_headers']}, # extra parameters they might add.
                         log_file_contents={"project_name": arguments['project_name'], 
                                            "grid_file": 'NA', 
                                            "morgan_file": arguments['morgan_file'], 
                                            "smile_file": arguments['smile_file'], 
                                            "sdf_file": "NA", 
                                            "docking_software": arguments['docking_software'], # this will always be autodock 
                                            "n_hyperparameters": arguments['n_hyperparameters'], 
                                            "n_molecules": arguments['n_molecules'], 
                                            "glide_input": "NA"})
    BACKEND.start()

    # Loading that project:
    project_name = arguments['project_name']
    BACKEND.load_project(project_name)
    
    # Waiting for it to load
    while BACKEND.status() == "fetching":
        if BACKEND.core.num_updates > 1 and BACKEND.core.model_data == {}:
            BACKEND.reset()
            return {}, 404
        time.sleep(1)

    DATA_HISTORY = BACKEND.pull() # forces it to finish
    return {'project_name': project_name}, 200

@app.route('/getProjectInfo', methods=['GET'])
def getProjectInfo():
    project_name = request.args['projectName']
    
    global PROJECTS_PATH, BACKEND

    data = {}
    # When not logged in this will be null:
    data['logged_in'] = BACKEND is not None
    if data['logged_in']:
        data['b_status'] = BACKEND.status()

    with open('./src/backend/db.json') as f:
        data['db'] = json.load(f)

    # Gets the list of projects available
    projects = os.listdir(PROJECTS_PATH)
    data['projects_list'] = projects

    try:
        if project_name == 'undefined':
            # loading the current project if already selected
            if data['logged_in'] and BACKEND.loaded_project != '':
                project_file = BACKEND.loaded_project + '.json'
            else:  
                project_file = projects[0]

            # print('Getting project', project_file)
            # Get the first project in the projects folder (if available)
            with open(PROJECTS_PATH + project_file) as f:
                # Index error if no project exists.
                data['specs'] = json.load(f)
        else:
            # getting the specified project (filenotfound if invalid name WONT HAPPEN b/c dropdown)
            with open(PROJECTS_PATH+project_name+'.json') as f:
                data['specs'] = json.load(f)
        
        # Makes sure not to display ""
        if data['specs']['specifications']['partition'] == '""':
            data['specs']['specifications']['partition'] = ''

    except (FileNotFoundError, IndexError): 
        # returns None if there are no projects or invalid name
        data['specs'] = None
    

    return jsonify(data), 200

@app.route('/runScripts', methods=['POST'])
def runScripts():
    script = request.args['script']
    global BACKEND


    if script == 'phase_a':
        BACKEND.run_phase(0)
    elif script == 'phase_1':
        BACKEND.run_phase(1)
    elif script == 'phase_2':
        BACKEND.run_phase(2)
    elif script == 'phase_3':
        BACKEND.run_phase(3)
    elif script == 'phase_4':
        BACKEND.run_phase(4)
    elif script == 'phase_5':
        BACKEND.run_phase(5)
    elif script == 'phase_f':
        BACKEND.run_phase(-1)
    elif script == 'reset_phase':
        BACKEND.reset_phase()
    elif script == 'delete_project':
        BACKEND.delete_project()
    elif script == 'update_specs':
        specs = {}
        for k, v in request.args.items():
            if k != 'script':
                specs[k] = v
        BACKEND.update_specifications(specs)

    # # Waiting for the next update loop so that the GUI is loaded correctly:
    # start = BACKEND.core.num_updates
    
    # #TODO: is this needed? -> just disable the buttons temporarily.
    # while BACKEND.core.num_updates <= start:
    #     time.sleep(1)

    return {'script': script}, 200

@app.route('/test', methods=['GET'])
def test():
    return render_template("test.html")

