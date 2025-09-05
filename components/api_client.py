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
        self.selected_model = "gpt-5"  # Default model
        
        # Available OpenAI models
        self.available_models = {
            "GPT-5 (Latest)": "gpt-5",
            "GPT-5 Mini": "gpt-5-mini", 
            "GPT-4.1": "gpt-4.1",
            "GPT-4o": "gpt-4o",
            "GPT-4o Mini": "gpt-4o-mini"
        }
    
    def determine_preferred_api(self):
        """Determine which API to use based on available keys"""
        if self.anthropic_api_key:
            return 'anthropic'
        elif self.openai_api_key:
            return 'openai'
        else:
            return None
    
    def set_model(self, model_name):
        """Set the selected OpenAI model"""
        if model_name in self.available_models.values():
            self.selected_model = model_name
        elif model_name in self.available_models.keys():
            self.selected_model = self.available_models[model_name]
    
    def get_current_model_display_name(self):
        """Get the display name of the current model"""
        for display_name, model_id in self.available_models.items():
            if model_id == self.selected_model:
                return display_name
        return f"Custom: {self.selected_model}"
    
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
            
            # GPT-5 uses different API endpoint (Responses API)
            if self.selected_model.startswith('gpt-5'):
                response = client.responses.create(
                    model=self.selected_model,
                    input=f'{custom_prompt}\n\nHere are the changed files to analyze:\n\n{content}',
                    reasoning={'effort': 'medium'},
                    text={'verbosity': 'medium'}
                )
                return response.output_text, None
            
            # GPT-4 and older models use Chat Completions API
            else:
                response = client.chat.completions.create(
                    model=self.selected_model,
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
                    max_tokens=4000,
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
            elif "model" in error_str.lower() and "does not exist" in error_str.lower():
                return None, f"Model Error: {error_str}\n\nNote: GPT-5 models may not be available in all regions or accounts yet.\nTry: gpt-4o, gpt-4.1, or contact OpenAI support."
            elif "responses" in error_str.lower() or "endpoint" in error_str.lower():
                return None, f"API Error: {error_str}\n\nGPT-5 requires the Responses API which may not be available yet.\nPlease use GPT-4o or GPT-4.1 instead."
            else:
                return None, f"Error: {error_str}"