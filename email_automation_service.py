import smtplib
import os
from email.mime.text import MIMEText
import json
from pathlib import Path

import logging
from datetime import datetime


import requests
from requests.auth import HTTPBasicAuth

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RESPONSE_LOG_PATH = Path("sent_responses_log.json")

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

ZENDESK_DOMAIN = os.getenv("ZENDESK_DOMAIN")
EMAIL_ZENDESK = "epatlan1742@sdsu.edu" 

API_TOKEN = os.getenv("API_TOKEN")
API_USER = f"{EMAIL_ZENDESK}/token"



def send_email(email_id: str, recipient: str, subject: str, body: str):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "noreply@example.com"
    msg["To"] = recipient
    message = f"""\
    Subject: Hi Mailtrap
    To:  {msg["To"]}
    From: {msg["From"]}
    {body}"""

    try:
        with smtplib.SMTP("smtp.mailtrap.io", 2525) as server:
            server.ehlo()                  #  Initialize session
            server.starttls()              #  Secure the connection
            server.ehlo()                  #  Re-identify after STARTTLS
            server.login(EMAIL_USER, EMAIL_PASS)
            
            server.sendmail(msg["From"], msg["To"], msg.as_string())
            logger.info(f"Email sent to {msg["To"]} for email {email_id}")
    except Exception as e:
        logger.error(f"Failed to send email for {email_id}: {str(e)}")
        raise RuntimeError(f"Email sending failed for {email_id}") from e


def log_sent_response(entry: dict):
    """Append a sent email response to a local JSON file."""
    existing = []
    if RESPONSE_LOG_PATH.exists():
        with open(RESPONSE_LOG_PATH, "r") as f:
            existing = json.load(f)
    
    existing.append(entry)

    with open(RESPONSE_LOG_PATH, "w") as f:
        json.dump(existing, f, indent=2)


def log_response(email: dict, response: str, classification: str, status: str = "success") -> str:
    """Log the sent response to a local JSON file.
    
    Args:
        email (dict): Email object with 'id' and 'from' fields
        response (str): Generated response text (must be a string)
        classification (str): Classification of the response
    
    Returns:
        str: Formatted response with timestamp
    """
    # Ensure response is a string
    if response is None:
        response = "No response generated."
    elif not isinstance(response, str):
        response = str(response)
    
    # Fill in the email details
    email_id = email.get("id", "unknown")
    recipient = email.get("from", "unknown")
    
    # Generate timestamp
    timestamp = datetime.utcnow().isoformat() + "Z"
    full_response = f"{response}\n\n[Sent at {timestamp}]"

    # Log the response locally
    log_sent_response({
        "email_id": email_id,
        "recipient": recipient,
        "classification": classification,
        "timestamp": timestamp,
        "response": full_response,
        "status": status
    })
    
    # Log the send action with timestamp
    logger.info(f"{'Sending' if status == 'success' else 'Failed to send'} {classification} response for email {email_id} at {timestamp}")
    return full_response



def create_ticket(email_id: str, context: str, type: str, recipient: str):
    """Create a support ticket in Zendesk using the REST API"""
    # zendesk_domain = "sandiegostateuniversity-90923.zendesk.com"
    # email = "epatlan1742@sdsu.edu" 
    
    # api_token = "aEhBhjQaDOUJO3Pj1qeWHiZ3B2zXb73wu4MQMHTp"
    # api_user = f"{email}/token"

    url = f"https://{ZENDESK_DOMAIN}/api/v2/tickets.json"
    headers = {"Content-Type": "application/json"}

    payload = {
        "ticket": {
            "subject": f"Support Request - Email ID {email_id}",
            "comment": {"body": context},
            "priority": "normal",
            "status": "open",
            "requester": {
                "name": "Customer from Email",
                "email": f"{recipient}"  # Replace with real email if available
            },
            
            "tags": ["email_automation", type]
        }
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            auth=HTTPBasicAuth(API_USER, API_TOKEN)
        )
       
        if response.status_code == 201:
            ticket_id = response.json()["ticket"]["id"]
            logger.info(f"Successfully created Zendesk ticket ID {ticket_id} for email {email_id}")
        else:
            logger.error(f"Failed to create Zendesk ticket for email {email_id}: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Exception while creating support ticket for email {email_id}: {str(e)}")

