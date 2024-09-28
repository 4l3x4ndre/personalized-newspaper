#!/bin/bash

# Step 1: Update and Install Python3 & pip
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

# Step 2: Setup Python Virtual Environment
python3 -m venv venv

# Step 3: Activate the Virtual Environment
source venv/bin/activate

# Step 4: Install Requirements
pip3 install -r utils/requirements.txt

python -m pip install -U --pre 'urllib3>=2.0.0a1'

echo "Installation is complete. Your Flask app is ready to be served!"

# Step 5: Run the Flask App
flask --app app.py  run 
