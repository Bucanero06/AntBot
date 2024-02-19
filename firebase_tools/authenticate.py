
import json
import os
from pprint import pprint

import dotenv
import requests
from fastapi import Depends

from shared.config import Oauth2_scheme

dotenv.load_dotenv(dotenv.find_dotenv())

FIREBASE_CONFIG = {
    "apiKey": os.environ.get("FIREBASE_API_KEY"),
}

assert FIREBASE_CONFIG["apiKey"], "FIREBASE_API_KEY environment variable not set!"


async def authenticate_with_firebase(email, password):
    """Authenticate with Firebase and return token if successful, or an error message."""
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


async def check_token_validity(token: str = Depends(Oauth2_scheme)):
    """Check if a Firebase token is valid."""
    endpoint = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_CONFIG['apiKey']}"
    data = {"idToken": token}
    response = requests.post(endpoint, data=json.dumps(data))

    return (response.status_code == 200)


async def check_str_token_validity(idToken):
    """Check if a Firebase token is valid."""
    endpoint = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_CONFIG['apiKey']}"
    data = {"idToken": idToken}
    response = requests.post(endpoint, data=json.dumps(data))
    return (response.status_code == 200)


