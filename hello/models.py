# pylint: E1101
"""
    The model's module contains database models represented as classes inheriting from SQLAlchemy's db.Model object.

"""

import datetime

from hello.database import db

# pylint: disable=no-member
# Disabling no-member checking during testing as SQLAlchemy adds database members on the db object during runtime.

class Visitor(db.Model):
    """
        This class represents a database table for a website's Visitor session.
        The fields represent column names in the table.
        create_ creates an instance of the class to be used in adding a new row
        save_   saves a visitor instance using stored functions in the database
    """
    __tablename__ = 'visitor'

    # comments on class fields
    pk = db.Column(db.Integer, primary_key=True)
    
    country = db.Column(db.String(100), unique=False, nullable=True)
    browser = db.Column(db.Text, unique=False, nullable=True)
    operating_system = db.Column(db.Text, unique=False, nullable=True)
    date_visited = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, country: str = '', browser: str = '', operating_system: str = '') -> None:
        # Initializes a new visitor object using the properties defined in the model
        self.country = country
        self.browser = browser
        self.operating_system = operating_system

    @staticmethod
    def create_(country: str, browser: str, operating_system: str):
        """
            Creates an instance of a database visitor and returns the object.
        """

        return Visitor(
            country=country,
            browser=browser,
            operating_system=operating_system
        )

    @staticmethod
    def save_(visitor) -> None:
        """
            Saves a new database visitor.
            Calls a stored procedure created during deployment as seen in the functions.sql file.
        """
        
        # get the database connection and cursor
        connection = db.engine.raw_connection()
        cursor = connection.cursor()

        # call the stored procedure with the visitor objects properties to insert a new visitor row
        cursor.callproc(
            "insert_visitor", [
                visitor.country, visitor.browser, visitor.operating_system])
        connection.commit()



    def __repr__(self) -> str:
        # Return a string representation of the visitor model
        return "<Visitor: {}>".format(self.date_visited.ctime())


class AzureDocument(db.Model):
    """
        Model representing an Azure document resource.
        Calls a stored procedure created during deployment as seen in the functions.sql file.
    """
    __tablename__ = 'azure_document'

    pk = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=True)
    url = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)

    def __init__(self, title: str = '', url: str = '', category: str = ''):
        # Initializes the azure document model property values
        self.title = title
        self.url = url
        self.category = category

    @staticmethod
    def create_(title: str = '', url: str = '', category: str = ''):
        """
            Creates a new instance of AzureDocument and returns
        """
        return AzureDocument(
            title=title,
            url=url,
            category=category,
        )

    @staticmethod
    def save_(azure_document) -> None:
        """
            Stores an azure document using stored procedures.
        """
        # retrieve the database connection and cursor
        connection = db.engine.raw_connection()
        cursor = connection.cursor()

        # call the stored function to insert a new document row
        cursor.callproc(
            "insert_azure_document", [
                azure_document.title, azure_document.url, azure_document.category])
        connection.commit()

    @staticmethod
    def get_grouped_documents():
        """
            Returns all the documents stored in the database.
        """
        # query the database and returns all saved documents
        return AzureDocument.query.all()

    @property
    def category_class(self):
        """
            Gets a css class name based on the document category.
        """
        # Assign document categories a css class name
        classes = {
            "Azure Technical Overviews": "is-info",
            "Azure Whitepapers": "is-dark",
            "Azure Best Practices": "is-warning"
        }

        # return matching class name for category
        return classes.get(self.category, "is-light")

    def __repr__(self) -> str:
        # Returns a string representation of the Azure Document model
        return "<AzureDocument {}>".format(self.title)
