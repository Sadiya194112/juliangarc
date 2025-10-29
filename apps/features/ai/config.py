"""
Configuration module for EV Charging Chatbot.
Loads environment variables and initializes API clients.
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class to manage API keys and settings."""
    
    def __init__(self):
        """Initialize configuration and validate required environment variables."""
        self.google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.default_radius = int(os.getenv("DEFAULT_SEARCH_RADIUS", "5000"))
        self.max_results = int(os.getenv("MAX_RESULTS", "5"))
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        self._validate()
    
    def _validate(self):
        """Validate that all required environment variables are set."""
        if not self.google_maps_api_key:
            raise ValueError(
                "🚨 Critical Error: GOOGLE_MAPS_API_KEY environment variable is not set.\n"
                "Get your API key from: https://console.cloud.google.com/google/maps-apis"
            )
        
        if not self.openai_api_key:
            raise ValueError(
                "🚨 Critical Error: OPENAI_API_KEY environment variable is not set.\n"
                "Get your API key from: https://platform.openai.com/account/api-keys"
            )
    
    def get_openai_client(self):
        """Return an initialized OpenAI client."""
        return OpenAI(api_key=self.openai_api_key)


# Global configuration instance
config = Config()
