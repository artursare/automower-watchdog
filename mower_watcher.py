import requests, time, os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
MOWER_ID = os.getenv('MOWER_ID')

def build_headers(token, include_content_type=False):
    headers = {
        'Authorization': f'Bearer {token}',
        'X-Api-Key': CLIENT_ID,
        'Authorization-Provider': 'husqvarna',
        'Accept': 'application/vnd.api+json'
    }
    if include_content_type:
        headers['Content-Type'] = 'application/vnd.api+json'
    return headers

def get_token():
    url = 'https://api.authentication.husqvarnagroup.dev/v1/oauth2/token'
    data = {
        'grant_type': 'client_credentials',
        'scope': 'iam:read amc:control'
    }
    response = requests.post(url, auth=(CLIENT_ID, CLIENT_SECRET), data=data)
    try:
        token_data = response.json()
        token = token_data['access_token']
        expires_in = token_data.get('expires_in', 3600)
        expiry_time = time.time() + expires_in - 60  # refresh 1 minute before expiration
        logging.info("Token acquired successfully.")
        return token, expiry_time
    except KeyError:
        logging.error("Token acquisition failed, 'access_token' not in response.")
        raise

def get_mower_status(token, mower_id):
    headers = build_headers(token)
    url = f'https://api.amc.husqvarna.dev/v1/mowers/{mower_id}'
    r = requests.get(url, headers=headers)
    try:
        data = r.json()['data']
    except (KeyError, ValueError) as e:
        logging.error(f"Error parsing mower status response: {e}, Raw response: {r.text}")
        raise
    logging.info(f"Retrieved status for mower {mower_id}.")
    return data

def resume_mower(token, mower_id):
    headers = build_headers(token, include_content_type=True)
    data = {
        'data': {
            'type': 'ResumeSchedule'
        }
    }
    url = f'https://api.amc.husqvarna.dev/v1/mowers/{mower_id}/actions'
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 204:
        logging.info(f"Mower {mower_id} resumed successfully.")
    else:
        logging.warning(f"Failed to resume mower {mower_id}. Status: {response.status_code}, Response: {response.text}")

def confirm_error(token, mower_id):
    headers = build_headers(token)
    url = f'https://api.amc.husqvarna.dev/v1/mowers/{mower_id}/errors/confirm'
    response = requests.post(url, headers=headers)
    if response.status_code == 202:
        logging.info(f"Error confirmed for mower {mower_id}.")
    else:
        logging.warning(f"Failed to confirm error for mower {mower_id}. Status: {response.status_code}, Response: {response.text}")

def handle_mower_error(token, mower):
    mower_id = mower['id']
    mower_attrs = mower['attributes']['mower']
    error_code = mower_attrs.get('errorCode', 'N/A')
    is_confirmable = mower_attrs.get('isErrorConfirmable', False)
    work_area_id = mower_attrs.get('workAreaId')
    work_areas = mower['attributes'].get('workAreas', [])
    work_area_name = next((wa['name'] for wa in work_areas if wa.get('workAreaId') == work_area_id), 'Unknown')

    logging.warning(f"Mower {mower_id} in state {mower_attrs.get('state')}, error {error_code}, area {work_area_name} ({work_area_id}).")

    if is_confirmable:
        for attempt in range(5):
            confirm_error(token, mower_id)
            logging.info(f"Waiting for mower to transition to PAUSED state... (attempt {attempt+1}/5)")
            for _ in range(10):
                time.sleep(6)
                mower = get_mower_status(token, mower_id)
                new_state = mower['attributes']['mower'].get('state')
                logging.info(f"Rechecked mower state: {new_state}")
                if new_state == 'PAUSED':
                    resume_mower(token, mower_id)
                    logging.info("Waiting to confirm mower resumed...")
                    for _ in range(10):
                        time.sleep(6)
                        mower = get_mower_status(token, mower_id)
                        confirm_state = mower['attributes']['mower'].get('state')
                        logging.info(f"Post-resume check state: {confirm_state}")
                        if confirm_state in ['IN_OPERATION', 'RESTRICTED']:
                            logging.info("Mower resumed successfully.")
                            return
                    logging.warning("Mower did not resume after PAUSED state.")
                    return
            logging.warning("Mower did not enter PAUSED after confirming error. Retrying...")

def loop():
    token, expiry = get_token()
    while True:
        if time.time() >= expiry:
            logging.info("Refreshing expired token...")
            token, expiry = get_token()
        logging.debug("Starting new iteration of mower check loop.")
        try:
            mower = get_mower_status(token, MOWER_ID)
            mower_id = mower['id']
            mower_attrs = mower['attributes']['mower']
            state = mower_attrs.get('state')
            logging.info(f"Mower {mower_id} state: {state}")

            if state in ['ERROR', 'FATAL_ERROR', 'ERROR_AT_POWER_UP']:
                handle_mower_error(token, mower)
        except Exception as e:
            logging.error(f"Error: {e}")
        time.sleep(180)

if __name__ == "__main__":
    try:
        loop()
    except Exception as e:
        logging.exception("Unexpected error occurred:")
