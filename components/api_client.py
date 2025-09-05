"""
API Client Module
Handles AI API integrations (OpenAI and Anthropic)
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class APIClient:
    """Manages AI API interactions"""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY', '')
        self.preferred_api = self.determine_preferred_api()
    
    def determine_preferred_api(self):
        """Determine which API to use based on available keys"""
        if self.anthropic_api_key:
            return 'anthropic'
        elif self.openai_api_key:
            return 'openai'
        else:
            return None
    
    def get_api_status(self):
        """Get a user-friendly API status message"""
        if self.anthropic_api_key:
            return "Claude (Anthropic) - Ready"
        elif self.openai_api_key:
            return "OpenAI - Ready" 
        else:
            return "No API Key - Add to .env file"
    
    def perform_anthropic_analysis(self, content, custom_prompt):
        """Perform Claude analysis"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                temperature=0.7,
                system="You are a code analysis assistant. Analyze the provided code files based on the user's specific requirements.",
                messages=[
                    {
                        "role": "user",
                        "content": f"{custom_prompt}\n\nHere are the changed files to analyze:\n\n{content}"
                    }
                ]
            )
            
            return message.content[0].text, None
            
        except Exception as e:
            error_str = str(e)
            if "credit" in error_str.lower() or "quota" in error_str.lower():
                return None, "Quota Issue: Please check your Anthropic account credits."
            elif "401" in error_str or "authentication" in error_str.lower():
                return None, "Invalid API Key: Please check your Anthropic API key in the .env file."
            elif "rate" in error_str.lower():
                return None, "Rate limited: Please wait a moment and try again."
            else:
                return None, f"Error: {error_str}"
    
    def perform_openai_analysis(self, content, custom_prompt):
        """Perform OpenAI analysis"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a code analysis assistant. Analyze the provided code files based on the user\'s specific requirements.'
                    },
                    {
                        'role': 'user',
                        'content': f'{custom_prompt}\n\nHere are the changed files to analyze:\n\n{content}'
                    }
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content, None
            
        except Exception as e:
            error_str = str(e)
            if "insufficient_quota" in error_str:
                return None, "Quota Exceeded: Please add credits to your OpenAI account."
            elif "401" in error_str or "invalid" in error_str.lower():
                return None, "Invalid API Key: Please check your OpenAI API key in the .env file."
            elif "rate_limit" in error_str.lower():
                return None, "Rate limited: Please wait a moment and try again."
            else:
                return None, f"Error: {error_str}"