# DeepDockingGUI - Beta v2.2.4

## Deep Docking - Democratize Drug Development
Deep docking (DD) is a deep learning-based tool developed to accelerate docking-based virtual screening. Using NVIDIA's own Autodock-GPU,  one can screen extensive chemical libraries like ZINC15 (containing > 1.3 billion molecules) 50 times faster than typical docking. For further details into the processes behind DD, please refer to our paper (https://doi.org/10.1021/acscentsci.0c00229). 

## Prerequisites
#### Remote Computer (cloud, cluster, ...):
* Autodock GPU installed
* Slurm workload manager installed.
* A program to create 3D conformations from SMILES
* Anaconda/Conda (optional)
  * Anaconda must be configured to allow for environment activation/deactivation using bash scripting.

#### Local Computer (laptop, desktop, ...)
* Node.js (https://nodejs.org/en/download/)
* Anaconda/Conda
* Python version >= 3

## Installation
To get started, clone or download the Deep-Docking repository to your local computer. Once downloaded, navigate to the installation directory and run 
```bash 
bash install-linux.sh or source install-linux.sh
```
for mac and linux users and
```bash 
install-windows
```
for windows users.

Upon running install-{linux/windows}, you will be prompted with straightforward questions, streamlining the installation process. When installation is complete, the application is ready to use. 


## Usage
The installation process will automatically create a new Conda environment on your local device called "DeepDockingLocal". To start DD, activate "DeepDockingLocal," navigate to Deep-Docking/GUI and run:
```bash 
npm run start-lin
```


for mac and linux users and
```bash 
npm run start-win
```
for windows users. 


After running the above, you should see something similar to the following: 
```bash 
> dd_gui@2.0.0 start-{lin/win} 
> export FLASK_APP=server.py && export FLASK_ENV=local_host && flask run
  * Serving Flask app "server.py" 
  * Environment: local_host 
  * Debug mode: off 
  * Running on http://123.4.5.6:7890/ (Press CTRL+C to quit)
 ```

Go to the web address provided, log in to your cluster, and you are ready to start a DD run.



## Common Issues + Fixes:
```python
  File "[...]/site-packages/tensorflow/python/keras/saving/hdf5_format.py", line 210, in load_model_from_hdf5
    model_config = json.loads(model_config.decode('utf-8'))
AttributeError: 'str' Object has no attribute 'decode'
```
  >This error is followed by an `IndexError` on line 264 of `get_model_image` and is most likely a dependancy issue with keras, make sure you have version 2.10.0 of `h5py` (versions 3.0+ cause issues) installed on the cluster side in the `DeepDockingRemote` conda environment. You can check the version by first activating the conda environment and then typing `pip show h5py`.<br>
  >You can install/downgrade it using pip: `pip install h5py==2.10.0` 

```bash
> dd_gui@2.0.0 start-lin /path/to/Deep-Docking/GUI
> export FLASK_APP=server.py && export FLASK_ENV=local_host && flask run
 sh: flask: command not found
 npm ERR! code ELIFECYCLE
```
 > If you had recently updated the version of GUI you might get this issue. This is an issue with your browser and not the scripts. You need to refresh the cache on the page that you get this error on (see https://bit.ly/3evFrJF for how to refresh cache on your system/browser).
