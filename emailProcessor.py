# Configuration and imports
import os
import json

from typing import Dict, Optional

from openai import OpenAI

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# class EmailProcessor 
class EmailProcessor:
    # Custom imports
    from processFunc import (
        _build_classification_prompt,
        _is_email_valid,
        handle_openai_error,
        _get_fallback_template,
        _build_prompt,
        _call_llm
    )
    # initialization of the class

    def __init__(self):
        """Initialize the email processor with OpenAI API key."""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Define valid categories - all lowercase for consistent comparison
        self.valid_classification = {
            "complaint", "inquiry", "feedback", 
            "support_request", "other"
        }
        
        # Create a case mapping for consistent output
        self.classification_case_mapping = {
            "complaint": "complaint",
            "inquiry": "inquiry",
            "feedback": "feedback",
            "support_request": "support_request",
            "other": "other"
        }
    # end of the __init__ function

    # Function to classify an email
    # using GPT with few-shot examples and generate a response
    def classify_email(self, email: Dict, temperature: float = 0.0) -> Optional[str]:
        """
        Classify an email using GPT with few-shot examples.
        Returns the classification or None if classification fails.
        """
        if not self._is_email_valid(email):
            return None

        prompt = self._build_classification_prompt(email)

        try:
            # Get raw response from LLM
            content = self._call_llm(prompt, email, temperature=temperature)
            
            if not content:
                logger.error("Empty response from LLM during classification")
                return None
                
            logger.info(f"Raw LLM output: {content}")

            # cleanup - just strip whitespace
            content = content.strip()
            
            # If content is wrapped in code blocks (triple backticks), remove them
            if content.startswith("```") and content.endswith("```"):
                content = content[3:-3].strip()
            
            # Parse the JSON response
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from LLM: {e}")
                logger.error(f"Content: '{content}'")
                return None
                
            # Validate result is a dictionary
            if not isinstance(result, dict):
                logger.error(f"Parsed result is not a dictionary: {type(result).__name__}")
                return None
                
            # Extract classification field (case-insensitive)
            classification = None
            
    
            # Check for common keys in the JSON response
            # that might contain the classification
            # This is a more flexible approach to handle different formats
            for key in ["classification", "Classification","category", "Category"]:
                if key in result:
                    classification = result[key]
                    break
            


            # If no classification found, return None
            if classification is None:
                logger.warning(f"No classification found in JSON response. Keys: {list(result.keys())}")
                return None

                
            # Ensure classification is a string
            if not isinstance(classification, str):
                logger.warning(f"Classification is not a string: {classification}")
                classification = str(classification)
                
            # Store original classification
            original_classification = classification.strip()
            # Clean up the classification for comparison
            classification_lower = original_classification.lower()
            logger.info(f"Extracted classification: '{original_classification}' (normalized: '{classification_lower}')")
            
            # Check if classification is in valid set (case-insensitive)
            if classification_lower in self.valid_classification:
                
                normalized_classification = self.classification_case_mapping[classification_lower]
                logger.info(f"✓ Valid classification found: '{normalized_classification}' (from '{original_classification}')")
                return normalized_classification
            else:
                logger.warning(f"✗ Invalid classification '{original_classification}' not in valid set: {self.valid_classification}")
                # Return None for invalid classification instead of defaulting to "other"
                return None
        # Handle OpenAI API errors and other exceptions
        except Exception as e:
            logger.error(f"Error during classification: {str(e)}")
            self.handle_openai_error(e, email)
            return None

    # end of the classify_email function

    # Function to generate a response using GPT based on the classification of the email
    # and the content of the email
    def generate_response(self, email: Dict, classification: str) -> Optional[str]:
        """
        Generate an automated email reply using LLM (GPT).
        Returns a fallback template if the model fails or input is invalid.
        """
        # Check if the email is valid and classification is valid
        if not self._is_email_valid(email):
            return None
        # create build prompt and a fallback template
        base_prompt = self._build_prompt(email, classification)
        fallback = self._get_fallback_template(classification)
        
        # try to call the LLM and generate a response
        # If the LLM fails to generate a response, use the fallback template
        try:
            content = self._call_llm(base_prompt, email)

            if not content:
                logger.info(
                    f"The AI didn't return any content for email {email['id']}. A fallback reply was used instead."
                )
                return fallback

            logger.info(f"A custom AI response was successfully generated for email {email['id']}.")
            return content
        # Handle OpenAI API errors and other exceptions
        except Exception as e:
            self.handle_openai_error(e, email)
            logger.info("To keep things running smoothly, a standard reply was used instead.")
            return fallback

    # end of the generate_response function