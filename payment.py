import functions_framework
import requests
import json
from firebase_admin import auth, firestore, initialize_app, credentials
import logging

# Initialize Firebase
cred = credentials.Certificate('serviceAccountKey.json')
initialize_app(cred)

# Initialize Firestore
db = firestore.client()

@functions_framework.http
def unified_function(request):
    # Handle preflight request for CORS
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
        return '', 204, headers

    try:
        # Get the Firebase ID token from the Authorization header
        id_token = request.headers.get('Authorization').split('Bearer ')[1]
        logging.info(f"Received ID token: {id_token}")

        # Verify the token and get user info
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        email = decoded_token.get('email')
        name = decoded_token.get('name')
        logging.info(f"Decoded token: UID={uid}, Email={email}, Name={name}")

        # API Endpoint and Secret Key
        url = "https://integration.reveniu.com/api/v1/subscriptions/"
        secret_key = "REVENIU_API_KEY"

        # Payload for the API request
        payload = {
            "plan_id": "4060",
            "external_id": uid,  # Use Firebase UID as external_id
            "field_values": {
                "email": email,
                "name": name,
                "amount": 4999
            }
        }
        
        # Log the payload
        print(f"Payload being sent to Reveniu: {json.dumps(payload, indent=2)}")
        
        # Headers for the API request
        headers = {
            "Content-Type": "application/json",
            "Reveniu-Secret-Key": secret_key
        }

        print(f"Sending request to Reveniu: URL={url}")
        
        # Make the API request to Reveniu
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        print(f"Reveniu response status: {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()
            print(f"Reveniu response data: {response_data}")

            return json.dumps({
                "completion_url": response_data['completion_url'],
                "security_token": response_data['security_token']
            }), 200, {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            }
        else:
            logging.error(f"Error from Reveniu: {response.status_code} - {response.text}")
            return json.dumps({"error": f"Error: {response.status_code} - {response.text}"}), 400, {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            }
    except Exception as e:
        logging.error(f"Exception during subscription process: {str(e)}")
        return json.dumps({"error": "An error occurred during the subscription process."}), 500, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
