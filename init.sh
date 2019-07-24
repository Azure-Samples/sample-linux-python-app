#!/bin/bash

# This is the startup file for the docker container, runs each time the container starts.
# It is made executable in the container.

echo "App Deployment Started at $(date)"

# export language settings for PostgreSQL drivers
export LC_ALL=C.UTF-8

export LANG=C.UTF-8

# set the flask app module in the environment variables
export FLASK_APP=app.py

# run database migrations
flask db migrate

flask db upgrade

# seeds the database in the app main function
python3 app.py

HOST="0.0.0.0:${PORT}"

# runs the WSGI server that serves the web application
gunicorn -w 4 -b $HOST app:app