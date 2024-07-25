import os
import smtplib
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

logging.basicConfig(level=logging.DEBUG)

@app.route('/submit', methods=['POST', 'OPTIONS'])
@cross_origin()  # Enable CORS for this route
def submit():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    try:
        data = request.json
        logging.debug(f"Received data: {data}")
        
        if not data:
            logging.error("Invalid JSON format")
            return jsonify({'error': 'Invalid JSON format'}), 400

        name = data.get('name')
        email = data.get('email')
        message = data.get('message')
        
        if not all([name, email, message]):
            logging.error("Missing required fields")
            return jsonify({'error': 'Name, email, and message are required.'}), 400
        
        sender_email = os.getenv("SENDER_EMAIL")
        receiver_email = os.getenv("RECEIVER_EMAIL")
        password = os.getenv("EMAIL_PASSWORD")

        logging.debug(f"SENDER_EMAIL: {sender_email}")
        logging.debug(f"RECEIVER_EMAIL: {receiver_email}")
        logging.debug(f"EMAIL_PASSWORD: {'set' if password else 'not set'}")

        if not all([sender_email, receiver_email, password]):
            logging.error("Email configuration is missing")
            return jsonify({'error': 'Email configuration is missing'}), 500

        msg = MIMEText(f"Name: {name}\nEmail: {email}\nMessage: {message}")
        msg['Subject'] = "Contact Form Submission"
        msg['From'] = sender_email
        msg['To'] = receiver_email

        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", 465))

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        
        logging.info("Email sent successfully")
        return jsonify({'success': 'Your message has been sent!'})
    
    except smtplib.SMTPAuthenticationError as auth_err:
        logging.error(f"SMTP Authentication Error: {auth_err}")
        return jsonify({'error': 'SMTP Authentication Error: ' + str(auth_err)}), 500
    except smtplib.SMTPConnectError as conn_err:
        logging.error(f"SMTP Connection Error: {conn_err}")
        return jsonify({'error': 'SMTP Connection Error: ' + str(conn_err)}), 500
    except Exception as e:
        logging.error(f"SMTP Error: {e}")
        return jsonify({'error': 'SMTP Error: ' + str(e)}), 500

def _build_cors_preflight_response():
    response = jsonify()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

def submit_request(request):
    return submit()

if __name__ == '__main__':
    app.run(debug=True)
