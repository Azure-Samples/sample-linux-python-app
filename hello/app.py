"""
    The main file for the sample application.
    Contains functions that create the application service.
    The web app is written in and serves a HTML template file stored in the templates folder.
"""

import html
import uuid
from timeit import default_timer
from random import shuffle

import adal
import requests
from flask import  Flask, Response, render_template, request, url_for, session, redirect
from geolite2 import geolite2

from hello.database import db
from hello.models import Visitor, AzureDocument
from hello.insights import get_telemetry_client
import hello.config as config

class User:
    """
        Class that represents a graph user, storing graph API properties
    """
    def __init__(self, **properties):
        self.__dict__.update(properties)

    def profile(self):
        return self.__dict__



def graphcall():
    """
        Fetch the users profile after successful authentication via Azure AD
        Receives the token from the session and hits the graph resource endpoint
    """
    http_headers = {'Authorization': 'Bearer ' + session.get('access_token'),
                    'User-Agent': 'adal-python-sample',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'client-request-id': str(uuid.uuid4())}

    graph_data = requests.get(config.RESOURCE_ENDPOINT, headers=http_headers, stream=False).json()
    return graph_data


def get_country_from_ip(ip_address: str) -> str:
    """
        Gets a visitors country name from their ip address.
        Looks up the country using geolite2's API.
    """
    reader = geolite2.reader()
    country_data = reader.get(ip_address)
    country = "N/A"
    if country_data:
        country = country_data.get('country', {}).get('names', {}).get('en', '')
    return country


def register_extensions(flask_app):
    """
        Initializes all extensions the application depends on.
        Add more extension initialization calls here.
        SQLAlchemy is initialized here.
    """
    db.init_app(flask_app)


def create_app(config_file):
    """
        Creates a default app and configure's it using the object in the config.py file.
        Registers any external extensions the app uses.
    """
    flask_app = Flask(__name__, static_folder=config.STATIC_FOLDER)
    flask_app.config.from_object(config_file)
    register_extensions(flask_app)
    return flask_app


# The main FLASK Application instance that runs the web app
app = create_app(config)


# Add header directives that improve the security posture
@app.after_request
def add_headers(response):
    """
        This function adds headers to outbound requests to increase the security posture in the browser
    """
    response.headers["Cache-Control"] = "public, max-age=31536000"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.route("/", methods=['GET'])
def index():
    """
        The index route of the application.
        Serves the home page with the documentation articles that are fetched from the database.
        Errors and metrics are tracked using application insights.
    """
    if not session.get('access_token'):
        resp = Response(status=307)
        resp.headers['location'] = f"{config.BASE_URI}/login"
        return resp

    user_json = graphcall()
    user = User(**user_json)
    # capture the request start time
    start = default_timer()

    # retrieve an application insights telemetry client
    telemetry_client = get_telemetry_client()

    # capture a website visitor's request details
    try:
        with app.app_context():
            # get the request origin country
            ip_address = request.remote_addr
            country = get_country_from_ip(ip_address)

            # get the operating system and browser version
            browser = "N/A"
            if request.user_agent.browser and request.user_agent.version:
                browser = request.user_agent.browser + request.user_agent.version
            operating_system = request.user_agent.platform if request.user_agent.platform else "N/A"

            # escape data going to be stored in the database
            country, browser, operating_system = (
                html.escape(country), html.escape(browser), html.escape(operating_system))

            # store the database write time
            db_write_start = default_timer()

            # create a visitor,use stored procedures called in the Visitor.save_ method
            visitor = Visitor.create_(country, browser, operating_system)
            Visitor.save_(visitor)

            db_write_end = default_timer()

            if telemetry_client:
                telemetry_client.track_metric(
                    'PostgreSQL Database Write Time', int(db_write_start - db_write_end))
                telemetry_client.flush()

    except Exception:
        # capture exception's when they occur and send telemetry to application insights
        if telemetry_client:
            telemetry_client.track_exception()
            telemetry_client.flush()

    # retrieve stored list of articles and randomize their order
    # store the database fetch time
    db_fetch_start = default_timer()

    documents = AzureDocument.get_grouped_documents()

    db_fetch_end = default_timer()

    shuffle(documents)

    # capture request end time
    end = default_timer()

    # log metrics and flush application insights
    if telemetry_client:
        telemetry_client.track_metric(
            'Request Response Time', int(end - start))
        telemetry_client.track_metric(
            'PostgreSQL Database Read Time', int(db_fetch_start - db_fetch_end))
        telemetry_client.flush()


    # render the basic web page template
    return render_template("index.html", documents=documents, user=user)


@app.route("/login")
def login():
    """
        Logs in a user via Azure AD Authentication by building an
        OAuth request to the authorization url using the
        clients configuration.
    """
    auth_state = str(uuid.uuid4())
    session['state'] = auth_state
    authorization_url = config.TEMPLATE_AUTHZ_URL.format(
        config.TENANT,
        config.CLIENT_ID,
        config.REDIRECT_URI,
        auth_state,
        config.RESOURCE)
    resp = Response(status=307)
    resp.headers['location'] = authorization_url
    return resp


@app.route("/token")
def token():
    """
        This endpoint receives the authentication code and state from 
        the OAuth initialization step, this code is then used to acquire
        the user's access token that has access to graph information.
    """
    code = request.args['code']
    state = request.args['state']

    if session.get('state') and session.get('state') != state:
        raise ValueError("State does not match")

    auth_context = adal.AuthenticationContext(config.AUTHORITY_URL)
    try:
        token_response = auth_context.acquire_token_with_authorization_code(
            code,
            config.REDIRECT_URI,
            config.RESOURCE,
            config.CLIENT_ID,
            config.CLIENT_SECRET
        )
        session['access_token'] = token_response['accessToken']
    except adal.adal_error.AdalError:
        session.pop('access_token')
        session.clear()
        return redirect(config.BASE_URI)

    return redirect(config.BASE_URI)

@app.route("/logout")
def logout():
    """
        Logs out the user by clearing the current session
    """
    session.clear()
    return render_template("intermediate.html")


@app.route("/hello", methods=['GET'])
def hello():
    """
        Returns hello world.
        Endpoint used by the HTTP probes in the application gateway for service health monitoring
    """
    return "Hello World Security App"
