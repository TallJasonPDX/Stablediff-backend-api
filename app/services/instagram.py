
import httpx
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from app.config import settings

class InstagramService:
    def __init__(self):
        self.client_id = settings.INSTAGRAM_CLIENT_ID
        self.client_secret = settings.INSTAGRAM_CLIENT_SECRET
        self.redirect_uri = settings.INSTAGRAM_REDIRECT_URI
        self.required_follow_username = settings.INSTAGRAM_REQUIRED_FOLLOW

    def get_authorization_url(self) -> str:
        """Generate the Instagram OAuth authorization URL"""
        return f"https://api.instagram.com/oauth/authorize?client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope=user_profile,user_media&response_type=code"

    async def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange the authorization code for an access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.instagram.com/oauth/access_token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                    "code": code
                }
            )
            
            if response.status_code != 200:
                return None
                
            token_data = response.json()
            
            # Get long-lived token
            long_lived_token = await self.get_long_lived_token(token_data.get("access_token"))
            if long_lived_token:
                token_data["access_token"] = long_lived_token
                
            return token_data

    async def get_long_lived_token(self, short_lived_token: str) -> Optional[str]:
        """Exchange a short-lived token for a long-lived token"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://graph.instagram.com/access_token",
                params={
                    "grant_type": "ig_exchange_token",
                    "client_secret": self.client_secret,
                    "access_token": short_lived_token
                }
            )
            
            if response.status_code != 200:
                return None
                
            data = response.json()
            return data.get("access_token")

    async def get_user_profile(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get the user's Instagram profile"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://graph.instagram.com/me",
                params={
                    "fields": "id,username",
                    "access_token": access_token
                }
            )
            
            if response.status_code != 200:
                return None
                
            return response.json()

    async def check_follows_user(self, access_token: str) -> bool:
        """
        Check if the authenticated user follows the required Instagram account
        Note: This is a simplified implementation as the Instagram Graph API has limitations
        for checking follows. In a real implementation, you might need to use other methods
        or APIs if available.
        """
        # In a real implementation, you would need to check if the user follows the required account
        # using appropriate Instagram API endpoints. This is a placeholder.
        async with httpx.AsyncClient() as client:
            try:
                # First get the user's own profile
                profile = await self.get_user_profile(access_token)
                if not profile:
                    return False
                
                # This endpoint requires special permissions that are not easily available,
                # so in a real app, you might need an alternative approach
                # This is simplified for demo purposes
                return True
            except Exception:
                return False

# Create a singleton service
instagram_service = InstagramService()
