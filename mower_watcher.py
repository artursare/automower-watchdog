import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

def get_token():
    url = 'https://api.authentication.husqvarnagroup.dev/v1/oauth2/token'
    data = {
        'grant_type': 'client_credentials',
        'scope': 'iam:read amc:control'
    }
    response = requests.post(url, auth=(CLIENT_ID, CLIENT_SECRET), data=data)
    response.raise_for_status()
    return response.json()['access_token']

def get_mower_status(token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.api+json'
    }
    response = requests.get('https://api.amc.husqvarnagroup.dev/v1/mowers', headers=headers)
    response.raise_for_status()
    return response.json()['data']

def resume_mower(token, mower_id):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/vnd.api+json'
    }
    data = {
        'data': {
            'type': 'mower-control',
            'attributes': {
                'command': 'START_RESUME_SCHEDULE'
            }
        }
    }
    url = f'https://api.amc.husqvarnagroup.dev/v1/mowers/{mower_id}/actions'
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

def loop():
    token = get_token()
    while True:
        try:
            mowers = get_mower_status(token)
            for mower in mowers:
                state = mower['attributes']['mower']['state']
                mower_id = mower['id']
                print(f"Mower {mower_id} state: {state}")
                if state == 'TRAPPED':
                    print("Resuming mower...")
                    resume_mower(token, mower_id)
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(60)

if __name__ == "__main__":
    loop()