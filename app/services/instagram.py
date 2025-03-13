
import httpx
from typing import Dict, Any, Optional

from app.config import settings

class InstagramService:
    def __init__(self):
        self.client_id = settings.INSTAGRAM_CLIENT_ID
        self.client_secret = settings.INSTAGRAM_CLIENT_SECRET
        self.redirect_uri = settings.INSTAGRAM_REDIRECT_URI
        
    def get_authorization_url(self) -> str:
        """Generate the Instagram OAuth authorization URL"""
        return (
            f"https://api.instagram.com/oauth/authorize"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope=user_profile,user_media"
            f"&response_type=code"
        )
    
    async def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange the authorization code for an access token"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
            "code": code
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.instagram.com/oauth/access_token",
                    data=data
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Error exchanging code: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            print(f"Error exchanging code for token: {str(e)}")
            return None
    
    async def get_user_profile(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get the user's Instagram profile"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://graph.instagram.com/me?fields=id,username&access_token={access_token}"
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Error getting profile: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            print(f"Error getting user profile: {str(e)}")
            return None

# Create a singleton service
instagram_service = InstagramService()
