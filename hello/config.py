"""
    Configuration module for the application.
    All Flask configuration will be stored here and configured using app.config.from_object
"""
import os
from urllib.parse import urlsplit

from hello.secrets import get_key_vault_secret

# Debug mode for the application, for production set it to False
DEBUG = False


# Connection string for the database
SQLALCHEMY_DATABASE_URI = get_key_vault_secret('PGCONNECTIONSTRING')


# Track modifications to model changes, set to False for performance
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Folder for app static files e.g. images, stylesheets
STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'static')

SECRET_KEY = get_key_vault_secret('FLASKSECRETKEY')

API_VERSION = 'v1.0'
RESOURCE = "https://graph.microsoft.com"
RESOURCE_ENDPOINT = f"{RESOURCE}/{API_VERSION}/me/"
AUTHORITY_HOST_URL = "https://login.microsoftonline.com"


TENANT = get_key_vault_secret('TENANT')

CLIENT_ID = get_key_vault_secret('CLIENTID')

CLIENT_SECRET = get_key_vault_secret('CLIENTSECRET')

AUTHORITY_URL = f"{AUTHORITY_HOST_URL}/{TENANT}"

REDIRECT_URI = get_key_vault_secret('REDIRECTURI')

path = urlsplit(REDIRECT_URI)
BASE_URI = f"{path.scheme}://{path.netloc}"

TEMPLATE_AUTHZ_URL = ('https://login.microsoftonline.com/{}/oauth2/authorize?' +
                      'response_type=code&client_id={}&redirect_uri={}&' +
                      'state={}&resource={}')

TEMPLATE_LOGOUT_URL = ('https://login.microsoftonline.com/{0}/oauth2/logout?' +
                       'post_logout_redirect_uri={1}')
