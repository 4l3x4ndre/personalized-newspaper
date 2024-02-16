#!/bin/bash

# Navigate to your project directory (adjust the path as necessary)
#cd /path/to/your-flask-app

# Step 1: Update and Install Python3 & pip
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

# Step 2: Setup Python Virtual Environment
python3 -m venv venv

# Step 3: Activate the Virtual Environment
source venv/bin/activate

# Step 4: Install Requirements
pip install -r requirements.txt

# Optional: Setup Gunicorn to serve the app and Nginx as a reverse proxy
#pip install gunicorn
# For Nginx setup, you would need to configure it manually or add additional commands here

echo "Installation is complete. Your Flask app is ready to be served!"

# Additional commands to start your Flask application can go here
# For example, to start a development server:
# flask run --host=0.0.0.0
flask --app app.py  run 

# Or to start with Gunicorn:
# gunicorn -w 4 -b 0.0.0.0:8000 run:app

