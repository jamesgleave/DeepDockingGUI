#!/bin/bash

# Create the local env
python3 install.py --phase install_local
# Activate the env
conda activate DeepDockingLocal 2> conda.out
# Install remote files and create remote env
python3 install.py --phase install_remote
