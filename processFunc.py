#!/bin/python
import logging
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# build_classification_prompt function
def _build_classification_prompt(self, email: Dict) -> str:
            return f"""
                    You are a smart and reliable assistant tasked with classifying customer emails into one of five categories:
                    - complaint: expressing dissatisfaction, anger, or frustration with a product, service, or experience.
                    - inquiry: requesting specific information or asking a question about a product, service, or policy.
                    - feedback: offering praise, general impressions, or constructive criticism without a request.
                    - support_request: seeking help with a technical issue, error, or usage problem.
                    - other: everything else that does not fit the above, including proposals, marketing, etc.

                    Use only the content of the email to determine its intent — tone and language are important.

                    Here are examples:

                    ---
                    Subject: Delayed order and poor packaging  
                    Body: I'm extremely disappointed. My package arrived a week late and the box was crushed. I expect better.  
                    Output: {{ "category": "complaint" }}

                    ---
                    Subject: Clarification on billing cycle  
                    Body: Hi, could you explain how often I'm billed for the premium subscription? Monthly or yearly?  
                    Output: {{ "category": "inquiry" }}

                    ---
                    Subject: Great experience with your chat support  
                    Body: Just wanted to say your support rep was amazing. Fast, friendly, and fixed everything!  
                    Output: {{ "category": "feedback" }}

                    ---
                    Subject: Can't reset my password  
                    Body: I tried resetting my password but I’m not receiving any reset email. Can you help?  
                    Output: {{ "category": "support_request" }}

                    ---
                    Subject: Collaboration proposal  
                    Body: We’d love to discuss a strategic partnership with your company. Is next week good for a meeting?  
                    Output: {{ "category": "other" }}

                    ---
                    Now classify the following email.

                    Subject: {email.get('subject')}  
                    Body: {email.get('body')}  

                    Respond only with:
                    {{ "category": "<complaint|inquiry|feedback|support_request|other>" }}
                    """
# end of the _build_classification_prompt function

# is email valid function, check if the email has a subject and body
# and is not empty
def _is_email_valid(self, email: Dict) -> bool:
        if not email.get("subject") or not email.get("body"):
            logger.warning(f"Email {email.get('id', '[Unknown ID]')} is missing a subject or body. Skipping classification.")
            return False
        return True

# get_fallback_template function
# Function to get a fallback template based on classification
# and return a default response
def _get_fallback_template(self, classification: str) -> str:
        templates = {
            "complaint": "We're sorry to hear about the issue. We've shared your message with our team and will follow up soon.",
            "inquiry": "Thanks for reaching out! We'll get back to you shortly with more information.",
            "feedback": "We truly appreciate your kind words. Thank you for letting us know!",
            "support_request": "Thanks for contacting us. Our team is looking into your issue and will follow up shortly.",
            "other": "Thanks for your message. We'll review it and respond if needed."
        }
        return templates.get(classification, templates["other"])
# end of the _get_fallback_template function

# build_prompt function
# Function to build the prompt for the LLM
# based on the classification and email content
def _build_prompt(self, email: Dict, classification: str) -> str:
        return f"""
        You are a professional customer service assistant. Based on the classification of the email, generate a short and polite response.

        Classification: {classification}

        Email content:
        Subject: {email.get('subject')}
        Body: {email.get('body')}

        Guidelines:
        - Keep the tone friendly and professional
        - Address the user's concern based on the classification
        - Reply directly to the customer (no AI disclaimers)
        - Keep it under 4 sentences
        - Do not repeat the original message
        - end polite closing with name of title services such as "Customer Service Team"
        - Use proper grammar, spelling, and punctuation
        
        Only output the message body as plain text.
        """
# end of the _build_prompt function

# call_llm function: function to call the OpenAI API and get a response using the prompt and email content
def _call_llm(self, prompt: str, email: Dict, temperature: float = 0.0) -> Optional[str]:
    """
    Call the OpenAI API to generate a response.
    
    Args:
        prompt: The prompt to send to the API
        email: The email object being processed
        temperature: Temperature setting for the LLM (higher = more creative)
        
    Returns:
        The generated text or None if an error occurred
    """
    try:
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        
        # Check if we have a valid response with choices
        if response and hasattr(response, 'choices') and len(response.choices) > 0:
            # Access the content from the first choice's message
            if hasattr(response.choices[0], 'message') and hasattr(response.choices[0].message, 'content'):
                return response.choices[0].message.content.strip()
        
        logger.warning(f"Received empty or invalid response from OpenAI API for email {email.get('id', 'unknown')}")
        return None
    except Exception as e:
        logger.error(f"Error in OpenAI API call: {str(e)}")
        return None

# end of the _call_llm function

# handle_openai_error function: Function to handle OpenAI API errors and log them
# and provide user-friendly messages
@staticmethod
def handle_openai_error(e: Exception, email: Dict) -> None:
    """Handle different OpenAI errors with user-friendly messages."""
    from openai import RateLimitError, APIConnectionError, AuthenticationError, APITimeoutError
    
    email_id = email.get('id', '[Unknown ID]')
    subject = email.get('subject', '[No Subject]')
    # Define a mapping of error types to user-friendly messages
    # and log the error
    error_messages = {
        RateLimitError: f"Rate limit exceeded while processing email {email_id}. Consider retrying after delay.",
        APIConnectionError: f"Network error while connecting to OpenAI for email {email_id}. Check your connection.",
        AuthenticationError: f"Authentication failed while accessing OpenAI API. Check your API key.",
        APITimeoutError: f"The OpenAI request timed out for email {email_id}. Consider retrying."
    }
    # Check if the error is one of the known types
    for error_type, message in error_messages.items():
        if isinstance(e, error_type):
            logger.error(message)
            return
    # If the error type is not recognized, log a generic error message
    # and provide a fallback response
    logger.error(
        f"Oops! Something unexpected happened while generating a response for email {email_id} "
        f"(Subject: '{subject}'). The error was: {e}"
    )

