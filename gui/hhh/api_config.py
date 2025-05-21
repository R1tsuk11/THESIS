import os
import json

class ApiConfig:
    """API configuration that can be loaded from file or environment."""
    
    @staticmethod
    def get_api_url():
        """Get the API URL for speech recognition services"""
        # You can enhance this to load from a config file or environment variable
        return "http://localhost:8000"