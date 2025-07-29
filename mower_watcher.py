import requests, time, os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

def get_token():
    url = 'https://api.authentication.husqvarnagroup.dev/v1/oauth2/token'
    data = {
        'grant_type': 'client_credentials',
        'scope': 'iam:read amc:control'
    }
    response = requests.post(url, auth=(CLIENT_ID, CLIENT_SECRET), data=data)
    try:
        token = response.json()['access_token']
        logging.info("Token acquired successfully.")
        return token
    except KeyError:
        logging.error("Token acquisition failed, 'access_token' not in response.")
        raise

def get_mower_status(token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.api+json'
    }
    r = requests.get('https://api.amc.husqvarnagroup.dev/v1/mowers', headers=headers)
    data = r.json()['data']
    logging.info(f"Retrieved status for {len(data)} mower(s).")
    return data

def resume_mower(token, mower_id):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/vnd.api+json'
    }
    data = {
        'data': {
            'type': 'mower-control',
            'attributes': { 'command': 'START_RESUME_SCHEDULE' }
        }
    }
    url = f'https://api.amc.husqvarnagroup.dev/v1/mowers/{mower_id}/actions'
    requests.post(url, headers=headers, json=data)

def loop():
    token = get_token()
    while True:
        try:
            mowers = get_mower_status(token)
            for mower in mowers:
                state = mower['attributes']['mower']['state']
                mower_id = mower['id']
                logging.info(f"Mower {mower_id} state: {state}")
                if state == 'TRAPPED':
                    logging.warning(f"Mower {mower_id} is trapped, attempting to resume.")
                    resume_mower(token, mower_id)
        except Exception as e:
            logging.error(f"Error: {e}")
        time.sleep(60)

if __name__ == "__main__":
    try:
        loop()
    except Exception as e:
        logging.exception("Unexpected error occurred:")