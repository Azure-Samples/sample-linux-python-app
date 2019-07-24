"""
    Module contains some utility functions for the sample application.
    Utility functions live here.
"""

import csv
import html

from hello.app import app
from hello.models import AzureDocument


def seed_db() -> None:
    """
        Seeds the database with Azure Document articles that'll be served by the application.
    """
    with app.app_context():
        # check if the database has been seeded by inquiring how many documents are there
        if not AzureDocument.query.count():

            # load the sample CSV file and populate the database
            with open('seed-data/asis-content.csv', 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for row in reader:
                    title, url, category = [field.strip() for field in row]
                    title, url, category = html.escape(
                        title), html.escape(url), html.escape(category)
                    document = AzureDocument.create_(
                        title=title, url=url, category=category)
                    AzureDocument.save_(document)
        else:
            print('Database Already Populated...')
