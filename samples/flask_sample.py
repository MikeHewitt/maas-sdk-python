from __future__ import unicode_literals

from flask import Flask, redirect, session, request, render_template, flash
from miracl_api import MiraclClient

import logging
import json

# Configure built-in logging template and level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')


def read_configuration():
    """
    :return: Dictionary representing configuration file
    """
    config_file = open("miracl.json")
    config = json.load(config_file)
    config_file.close()
    return config

# Initialize Flask application
app = Flask(__name__)

# Initialize MiraclClient
miracl = MiraclClient(**read_configuration())


@app.route("/")
def hello():
    """
    Default route that displays user information for logged in user and login
    button for user not yet logged in
    """
    # Check if user is authorized
    authorized = miracl.is_authorized(session)

    # Prepare model for template
    context = {
        'is_authorized': authorized
    }

    if authorized:
        # Fill model with user data
        context['email'] = miracl.get_email(session)
        context['user_id'] = miracl.get_user_id(session)
    else:
        # Fill model with auth url for login button
        context['auth_url'] = miracl.get_authorization_request_url(session)
    # Render and display template
    return render_template('index.html', **context)


@app.route("/c2id")
def c2id():
    """
    Callback route called after user interaction with login button
    """

    # Validate authorization data
    if miracl.validate_authorization(session,
                                     request.query_string.decode()) is not None:
        # If authorization is successful, set message for user and redirect
        # back to default route
        flash('Successfully logged in!', 'success')
        return redirect("/")

    # If authorization fails, notify user
    flash('Login failed!', 'danger')
    # and render template with "retry" section
    return render_template('index.html', retry=True,
                           auth_url=miracl.get_authorization_request_url(
                               session))


@app.route("/refresh")
def refresh():
    """
    Refresh route - clear user data and redirect back to default route
    """
    miracl.clear_user_info(session)
    return redirect("/")


@app.route("/logout")
def logout():
    """
    Logout route - clear user data and auth info, notify user and redirect
         bacl to default route
    """
    miracl.clear_user_info(session, including_auth=True)
    flash('User logged out!', 'info')
    return redirect("/")

# Flask app configuration - secret key used to sign cookies for session storage
app.secret_key = "ReplaceWithValidSecret"

# If this is startup file
if __name__ == "__main__":
    # Set debug flag for Flask app
    app.debug = True
    # and launch it on specified port
    app.run(host='0.0.0.0',port=5000)
