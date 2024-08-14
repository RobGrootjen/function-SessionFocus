import functions_framework
import requests
from firebase_admin import firestore, initialize_app, credentials
import logging

# Initialize Firebase
cred = credentials.Certificate('serviceAccountKey.json')
initialize_app(cred)

# Initialize Firestore
db = firestore.client()

@functions_framework.http
def unsubscribe_user(request):
    # Handle preflight request for CORS
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
        return '', 204, headers

    # Parse the request body to get the user ID
    request_data = request.get_json()
    user_id = request_data.get('user_id')  # The user ID passed from the front-end
    print(f"Received user_id: {user_id}")

    if not user_id:
        return "User ID is required", 400, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }

    try:
        # Query Firestore to get the subscription ID
        subscription_ref = db.collection('payment_events').where('data.data.subscription_external_id', '==', user_id).get()
        print(f"Subscription query result: {[doc.to_dict() for doc in subscription_ref]}")

        if subscription_ref:
            subscription_data = subscription_ref[0].to_dict()
            subscription_id = subscription_data['data']['data']['subscription_id']
            print(f"Found subscription_id: {subscription_id}")
        else:
            print("No subscription found for the given user_id")
            return "Subscription not found", 404, {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            }

        # Define the unsubscribe API endpoint
        url = f"https://integration.reveniu.com/api/v1/subscriptions/{subscription_id}/disablerenew/"
        print(url)
        api_key = "REVENIU-API-KEY"
        headers = {
            "Reveniu-Secret-Key": api_key,
            "Content-Type": "application/json"
        }

        # Make the POST request to disable subscription renewal
        response = requests.post(url, headers=headers)

        if response.status_code == 200:
            return "Successfully unsubscribed", 200, {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            }
        else:
            print(f"Failed to unsubscribe: {response.status_code}")
            return f"Failed to unsubscribe: {response.status_code}", 400, {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            }

    except Exception as e:
        logging.error(f"Error during unsubscribe process: {str(e)}")
        return "Internal Server Error", 500, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
