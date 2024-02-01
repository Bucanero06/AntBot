# Copyright (c) 2024 Carbonyl LLC & Carbonyl R&D
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import json
import os
from pprint import pprint

import dotenv
import requests
from fastapi import Depends

from shared.config import Oauth2_scheme

dotenv.load_dotenv()

FIREBASE_CONFIG = {
    "apiKey": os.environ.get("FIREBASE_API_KEY"),
    "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
    "databaseURL": os.environ.get("FIREBASE_DATABASE_URL"),
    "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
    "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.environ.get("FIREBASE_APP_ID"),
    "measurementId": os.environ.get("FIREBASE_MEASUREMENT_ID"),
}
def authenticate_with_firebase(email, password):
    """Authenticate with Firebase and return token if successful, or an error message."""
    print(f'{FIREBASE_CONFIG["apiKey"] = }')
    endpoint = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_CONFIG['apiKey']}"
    data = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    try:
        response = requests.post(endpoint, data=json.dumps(data))
        response_data = response.json()

        if "idToken" in response_data:
            return {
                'status': 'success',
                'error_message': None,
                'token': response_data.get('idToken'),
                'refresh_token': response_data.get('refreshToken'),
                'user_id': response_data.get('localId'),
                'email': response_data.get('email'),
                'expires_in': response_data.get('expiresIn'),
            }

        elif "error" in response_data:
            return {
                'status': 'error',
                'error_message': f"Authentication failed: {response_data['error'].get('message', 'Unknown error.')}",
                'token': None,
                'refresh_token': None,
                'user_id': None,
                'email': None,
                'expires_in': None,
            }
    except requests.RequestException as e:
        return {
            'status': 'error',
            'error_message': f"Authentication failed: {e}",
            'token': None,
            'refresh_token': None,
            'user_id': None,
            'email': None,
            'expires_in': None,
        }
    return {
        'status': 'error',
        'error_message': f"Authentication failed: Unknown error.",
        'token': None,
        'refresh_token': None,
        'user_id': None,
        'email': None,
        'expires_in': None,
    }


def check_token_validity(token: str = Depends(Oauth2_scheme)):
    """Check if a Firebase token is valid."""
    endpoint = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_CONFIG['apiKey']}"
    data = {"idToken": token}
    response = requests.post(endpoint, data=json.dumps(data))
    return (response.status_code == 200)

