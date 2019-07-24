"""
    Exposes the app to be run by gunicorn via WSGI.
    Flask Migrate is linked here by creating a migrate instance.
    Seeding the database occurs when the file is run from the command line.
"""

from flask_migrate import Migrate

from hello.app import app
from hello.database import db
from hello.utils import seed_db

# attach Flask Migrate to the Flask application
migrate = Migrate(app, db)

# when app is run from the command line seed the database
if __name__ == '__main__':
    seed_db()