import functions_framework
import json
from firebase_admin import firestore, initialize_app, credentials
import logging

# Initialize Firebase
cred = credentials.Certificate('serviceAccountKey.json')
initialize_app(cred)

# Initialize Firestore
db = firestore.client()

@functions_framework.http
def handle_webhook(request):
    # Handle preflight request for CORS
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
        return '', 204, headers
    
    # Validate the Reveniu-Secret-Key header
    secret_key = request.headers.get('Reveniu-Secret-Key')
    if secret_key != "REVENIU_API":  # Replace with your actual secret key
        return "Unauthorized", 401, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }

    # Parse the request body
    event_data = request.get_json()

    # Log the entire event data received from Reveniu
    print(f"Received event data: {json.dumps(event_data, indent=2)}")

    event_type = event_data.get('data', {}).get('event')
    print(f"Event type received: {event_type}")

    # Process the event based on its type
    if event_type == "subscription_activated":
        # The correct path to subscription_external_id
        subscription_data = event_data.get('data', {}).get('data', {})
        print(f"Data field content: {subscription_data}")

        subscription_external_id = subscription_data.get('subscription_external_id')
        print(f"Subscription activated for External ID: {subscription_external_id}")

        if subscription_external_id:
            try:
                # Update the user's type to "premium" in Firestore
                user_doc_ref = db.collection('users').document(subscription_external_id)
                user_doc_ref.update({
                    'info.type': 'premium'
                })
                logging.info(f"Updated user {subscription_external_id} to premium.")
            except Exception as e:
                logging.error(f"Error updating Firestore: {str(e)}")
                return json.dumps({"error": "Error updating Firestore."}), 500, {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                }

    elif event_type == "subscription_deactivated":
        subscription_data = event_data.get('data', {}).get('data', {})
        print(f"Data field content: {subscription_data}")

        subscription_external_id = subscription_data.get('subscription_external_id')
        print(f"Subscription deactivated for External ID: {subscription_external_id}")

        if subscription_external_id:
            try:
                # Update the user's type to "regular" in Firestore
                user_doc_ref = db.collection('users').document(subscription_external_id)
                user_doc_ref.update({
                    'info.type': 'regular'
                })
                logging.info(f"Updated user {subscription_external_id} to regular.")
            except Exception as e:
                logging.error(f"Error updating Firestore: {str(e)}")
                return json.dumps({"error": "Error updating Firestore."}), 500, {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                }

    # Store the payment event in Firestore
    try:
        payment_event_ref = db.collection('payment_events').document()
        payment_event_ref.set(subscription_data)
        logging.info(f"Stored payment event: {subscription_data}")
    except Exception as e:
        logging.error(f"Error storing payment event in Firestore: {str(e)}")
        return json.dumps({"error": "Error storing payment event in Firestore."}), 500, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }

    # Respond to Reveniu
    return "Event received", 200, {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }
