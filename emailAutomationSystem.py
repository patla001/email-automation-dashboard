#!/bin/python

from emailProcessor import EmailProcessor

from typing import Dict, Optional, Tuple
import logging
import uuid

import numpy as np

from email_automation_service import send_email, log_response, create_ticket

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailAutomationSystem:
    def __init__(self, processor: EmailProcessor):
        """Initialize the automation system with an EmailProcessor."""
        self.processor = processor
        self.response_handlers = {
            "complaint": self._handle_complaint,
            "inquiry": self._handle_inquiry,
            "feedback": self._handle_feedback,
            "support_request": self._handle_support_request,
            "other": self._handle_other
        }

    def process_email(self, email) -> Dict:
        """
        Process a single email through the complete pipeline.
        Returns a dictionary with the processing results.
        """
        if not isinstance(email, dict):
            logger.error(f"Invalid email format: expected dictionary, got {type(email).__name__}")
            return {
                "email_id": "unknown",
                "original_email": str(email)[:100] + "..." if len(str(email)) > 100 else str(email),
                "classification": None,
                "response_sent": None,
                "status": "error",
                "error_message": f"Invalid email format: expected dictionary, got {type(email).__name__}"
            }

        email_id = email.get("id")
        if not isinstance(email_id, str) or not any(char.isdigit() for char in email_id):
            email_id = self._generate_numeric_id()
            email["id"] = email_id  

        try:
            if "body" not in email:
                raise ValueError(f"Email {email_id}: missing required 'body' field")

            logger.info(f"Processing email {email_id}...")

            classification = self.processor.classify_email(email)
            handler = self.response_handlers.get(classification, self._handle_other)
            response_sent, status = handler(email)

            return {
                "email_id": email_id,
                "original_email": email,
                "classification": classification,
                "response_sent": response_sent,
                "status": status
            }

        except Exception as e:
            logger.error(f"Error processing email {email_id}: {str(e)}")
            return {
                "email_id": email_id,
                "original_email": email,
                "classification": None,
                "response_sent": None,
                "status": status,
                "error_message": str(e)
            }

    def _generate_numeric_id(self) -> str:
        """Generate a fallback numeric ID using NumPy (last 6 digits of UUID-based random int)."""
        # Generate a UUID, convert to bytes, and use it to seed NumPy's RNG
        uid = uuid.uuid4()
        seed = int(uid.int % (2**32))  # Truncate to 32-bit seed
        rng = np.random.default_rng(seed)
        return str(rng.integers(0, 1_000_000))  # 6-digit numeric ID

    def _generic_handler(self, email: Dict, classification: str, fallback_response: str,
        send_fn: Optional[callable] = None,
        extra_action: Optional[callable] = None
    ) -> Tuple[bool, str]:
        try:
            if not isinstance(email, dict):
                raise ValueError(
                    f"Invalid email format in _handle_{classification}: expected dictionary, got {type(email).__name__}"
                )

            response = self.processor.generate_response(email, classification) or fallback_response
            status = "success"

            try:
                if send_fn:
                    send_fn(email.get("id", "unknown"), response, email.get("from", "no-reply@example.com"))
            except Exception as send_error:
                logger.error(f"Failed to send email for {email.get('id', 'unknown')}: {send_error}")
                response = f"Email sending failed due to an error: {send_error}"
                status = "error"

            # Perform extra action regardless of send result
            if extra_action:
                extra_action(email)

            log_response(email, response, classification, status)
            return (status == "success", status)

        except Exception as e:
            logger.error(f"Error handling {classification} email {email.get('id', 'unknown')}: {str(e)}")
            log_response(email, f"Error processing {classification}: {str(e)}", classification, "error")
            return (False, "error")


    def _handle_complaint(self, email: Dict) -> Tuple[bool, str]:
        return self._generic_handler(
            email,
            "complaint",
            "We apologize, but we could not process your complaint at this time. Our team has been notified and will address this issue promptly.",
            self._send_complaint_response,
            lambda e: self._create_urgent_ticket(
                e.get("id", "unknown"), "complaint", e.get("from", "no-reply@example.com")
            )
        )

    def _handle_inquiry(self, email: Dict) -> Tuple[bool, str]:
        return self._generic_handler(
            email,
            "inquiry",
            "Thank you for your inquiry. We're currently experiencing technical difficulties. Our team will get back to you shortly.",
            self._send_standard_response
        )

    def _handle_feedback(self, email: Dict) -> Tuple[bool, str]:
        return self._generic_handler(
            email,
            "feedback",
            "Thank you for your feedback. We appreciate you taking the time to share your thoughts with us.",
            self._send_standard_response,
            lambda e: self._log_customer_feedback(
                e.get("id", "unknown"), e.get("body", ""), e.get("from", "no-reply@example.com")
            )
        )

    def _handle_support_request(self, email: Dict) -> Tuple[bool, str]:
        return self._generic_handler(
            email,
            "support_request",
            "Thank you for contacting our support team. We've created a ticket for your issue and will respond as soon as possible.",
            self._send_standard_response,
            lambda e: self._create_support_ticket(
                e.get("id", "unknown"), e.get("body", ""), e.get("from", "no-reply@example.com")
            )
        )

    def _handle_other(self, email: Dict) -> Tuple[bool, str]:
        return self._generic_handler(
            email,
            "other",
            "Thank you for your message. We've received your email and will review it promptly.",
            self._send_standard_response
        )

    def _send_complaint_response(self, email_id: str, response: str, recipient_email: str) -> None:
        try: 
            logger.info(f"Sending complaint response for email {email_id}")
            subject = "Regarding Your Complaint"
            send_email(email_id, recipient_email, subject, response)
        except Exception as e:
            logger.error(f"Failed to send complaint response for email {email_id}: {str(e)}")
            raise RuntimeError(f"Email sending failed for {email_id}") from e

    def _send_standard_response(self, email_id: str, response: str, recipient_email: str) -> None:
        try:
            logger.info(f"Sending standard response for email {email_id}")
            subject = "Regarding Your Standard Inquiry"
            send_email(email_id, recipient_email, subject, response)
        except Exception as e:
            logger.error(f"Failed to send standard response for email {email_id}: {str(e)}")
            raise RuntimeError(f"Email sending failed for {email_id}") from e

    def _create_urgent_ticket(self, email_id: str, ticket_type: str, recipient_email: str) -> None:
        logger.info(f"Creating urgent ticket for email {email_id}")
        logger.info(f"Ticket type: {ticket_type}")
        logger.info(f"Customer email: {recipient_email}")
        create_ticket(email_id, f"Urgent ticket for {ticket_type} issue", ticket_type, recipient_email)

    def _create_support_ticket(self, email_id: str, issue_description: str, recipient_email: str) -> None:
        logger.info(f"Creating support ticket for email {email_id}")
        logger.info(f"Issue description: {issue_description[:50]}..." if len(issue_description) > 50 else f"Issue description: {issue_description}")
        logger.info(f"Customer email: {recipient_email}")
        create_ticket(email_id, issue_description, "support_request",recipient_email)

    def _log_customer_feedback(self, email_id: str, feedback: str, recipient_email: str) -> None:
        logger.info(f"Logging feedback for email {email_id}")
        logger.info(f"Feedback content: {feedback[:50]}..." if len(feedback) > 50 else f"Feedback content: {feedback}")
        logger.info(f"Customer email: {recipient_email}")
        create_ticket(email_id, feedback, "feedback",recipient_email)