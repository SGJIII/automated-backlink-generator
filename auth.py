import os
from flask import Blueprint, redirect, url_for, session, request, jsonify
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
import google.auth.transport.requests
from pip._vendor import cachecontrol
import requests

auth_bp = Blueprint('auth', __name__)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
client_secrets_file = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:5000/auth/callback"]
    }
}

@auth_bp.route('/login')
def login():
    flow = Flow.from_client_config(
        client_secrets_file,
        scopes=['https://www.googleapis.com/auth/userinfo.email', 'openid'],
        redirect_uri=url_for('auth.callback', _external=True)
    )
    auth_url, state = flow.authorization_url()
    session['state'] = state
    return redirect(auth_url)

@auth_bp.route('/auth/callback')
def callback():
    flow = Flow.from_client_config(
        client_secrets_file,
        scopes=['https://www.googleapis.com/auth/userinfo.email', 'openid'],
        state=session['state'],
        redirect_uri=url_for('auth.callback', _external=True)
    )
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)
    id_info = id_token.verify_oauth2_token(
        credentials._id_token,
        token_request,
        GOOGLE_CLIENT_ID
    )
    session['email'] = id_info.get('email')
    print("Session set in callback:", session)  # Debug print
    return redirect(url_for('dashboard'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
