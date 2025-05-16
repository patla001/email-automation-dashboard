import unittest
from unittest.mock import patch
from emailProcessor import EmailProcessor
from emailAutomationSystem import EmailAutomationSystem

class TestEmailAutomationSystem(unittest.TestCase):
    # Mocking the EmailProcessor class
    def setUp(self):
        self.processor = EmailProcessor()
        self.system = EmailAutomationSystem(self.processor)
        self.test_email = {
            "id": "test001",
            "from": "test@example.com",
            "subject": "Need refund now!",
            "body": "I want a refund. This is unacceptable.",
            "timestamp": "2025-03-15T10:00:00Z"
        }
    # end of the setUp function

    # Mocking the classify_email method
    @patch.object(EmailProcessor, 'classify_email', return_value='complaint')
    @patch.object(EmailProcessor, 'generate_response', return_value='We apologize for the inconvenience...')
    @patch('emailAutomationSystem.send_email')
    def test_process_email_success(self, mock_send_email, mock_generate_response, mock_classify):
        mock_send_email.return_value = None
        result = self.system.process_email(self.test_email)

        self.assertEqual(result["email_id"], "test001")
        self.assertEqual(result["classification"], "complaint")
        self.assertTrue(result["response_sent"])
        self.assertEqual(result["status"], "success")
        print("-- Test Email Processed Successfully --")
    # end of the test_process_email_success function

    # Mocking the send_email method
    # Replaces the classify_email method of the EmailProcessor class with a mock that always returns 'complaint'.
    # To control the classification result and ensure the test behavior is consistent, regardless of the actual implementation or input.
    @patch.object(EmailProcessor, 'classify_email', return_value='complaint')
    @patch.object(EmailProcessor, 'generate_response', return_value='We apologize for the inconvenience...')
    @patch('emailAutomationSystem.send_email')
    def test_process_email_send_failure(self, mock_send_email, mock_generate_response, mock_classify):
        mock_send_email.side_effect = Exception("Simulated SMTP error")

        result = self.system.process_email(self.test_email)

        self.assertEqual(result["email_id"], "test001")
        self.assertEqual(result["classification"], "complaint")
        self.assertFalse(result["response_sent"])
        self.assertEqual(result["status"], "error")
        print("-- Test Email Processed with Send Failure --")
    # end of the test_process_email_send_failure function

    # Mocking the classify_email method to simulate classification failure
    @patch.object(EmailProcessor, 'classify_email', return_value=None)
    def test_classification_failure(self, mock_classify):
        result = self.system.process_email(self.test_email)

        self.assertEqual(result["email_id"], "test001")
        self.assertIsNone(result["classification"])
        self.assertFalse(result["response_sent"])
        self.assertEqual(result["status"], "error")
        print("-- Test Email Processed with Classification Failure --")
    # end of the test_classification_failure function

    # test missing email body function
    def test_missing_email_body(self):
        incomplete_email = {
            "id": "test002",
            "from": "user@example.com",
            "subject": "No body",
            "timestamp": "2025-03-15T10:00:00Z"
        }

        result = self.system.process_email(incomplete_email)

        self.assertEqual(result["email_id"], "test002")
        self.assertIsNone(result["classification"])
        self.assertFalse(result["response_sent"])
        self.assertEqual(result["status"], "error")
        self.assertIn("missing or empty 'body'", result.get("error_message", ""))
        print("-- Test Email Processed with Missing Body --")
    # end of the test_missing_email_body function


if __name__ == '__main__':
    unittest.main()
