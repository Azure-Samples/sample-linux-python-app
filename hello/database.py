"""
Module creates an instance of the SQLAlchemy database object.
In separate file to avoid circular dependencies.
"""

from flask_sqlalchemy import SQLAlchemy

# An instance of the SQLAlchemy ORM's database object.
# It will be used to call stored procedures and read/write to the database.
db = SQLAlchemy()
