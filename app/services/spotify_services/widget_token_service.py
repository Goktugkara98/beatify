import secrets
import base64
import json
import time
from datetime import datetime, timedelta

class WidgetTokenService:
    def __init__(self):
        self.token_validity_days = 30  # Token validity period in days
    
    def generate_widget_token(self, username, widget_config):
        """
        Generate a secure token for widget access
        
        Parameters:
        - username: The username of the user
        - widget_config: Dictionary containing widget configuration
            {
                'type': 'spotify-nowplaying',  # Widget type identifier
                'design': 'default',           # Design variant
                'other_params': 'value'        # Any other config parameters
            }
            
        Returns:
        - token: Base64 encoded token containing user and widget info
        """
        # Create token payload
        payload = {
            'username': username,
            'created_at': int(time.time()),
            'expires_at': int((datetime.now() + timedelta(days=self.token_validity_days)).timestamp()),
            'widget_config': widget_config
        }
        
        # Add a random component for security
        payload['nonce'] = secrets.token_hex(8)
        
        # Serialize and encode
        serialized = json.dumps(payload)
        encoded = base64.urlsafe_b64encode(serialized.encode()).decode()
        
        return encoded
    
    def validate_widget_token(self, token):
        """
        Validate a widget token and extract its information
        
        Parameters:
        - token: The encoded token string
        
        Returns:
        - (is_valid, payload): Tuple with validity status and payload (if valid)
        """
        try:
            # Decode token
            decoded = base64.urlsafe_b64decode(token.encode()).decode()
            payload = json.loads(decoded)
            
            # Check expiration
            current_time = int(time.time())
            if current_time > payload.get('expires_at', 0):
                return False, None
                
            return True, payload
        except Exception as e:
            print(f"Error validating widget token: {str(e)}")
            return False, None
    
    def get_widget_config_from_token(self, token):
        """
        Extract widget configuration from a token
        
        Parameters:
        - token: The encoded token string
        
        Returns:
        - widget_config: The widget configuration or None if invalid
        """
        is_valid, payload = self.validate_widget_token(token)
        if not is_valid or not payload:
            return None
            
        return payload.get('widget_config')
    
    def get_username_from_token(self, token):
        """
        Extract username from a token
        
        Parameters:
        - token: The encoded token string
        
        Returns:
        - username: The username or None if invalid
        """
        is_valid, payload = self.validate_widget_token(token)
        if not is_valid or not payload:
            return None
            
        return payload.get('username')