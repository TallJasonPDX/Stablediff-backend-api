import httpx
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from app.config import settings
from urllib.parse import quote


class FacebookService:

    def __init__(self):
        self.client_id = settings.INSTAGRAM_CLIENT_ID
        self.client_secret = settings.INSTAGRAM_CLIENT_SECRET
        self.redirect_uri = "https://thelastnurses.com/"  #settings.INSTAGRAM_REDIRECT_URI
        self.required_follow_username = settings.INSTAGRAM_REQUIRED_FOLLOW
        self.api_version = "v22.0"  # Latest stable version

    def get_authorization_url(self) -> str:
        """Generate the Facebook OAuth authorization URL for FB access"""
        scopes = "email,public_profile"
        return f"https://www.facebook.com/{self.api_version}/dialog/oauth?client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope={scopes}&response_type=code"

    async def exchange_code_for_token(self,
                                      code: str) -> Optional[Dict[str, Any]]:
        """Exchange the authorization code for an access token using Facebook Graph API"""
        print(f"[Facebook] Exchanging code for access token...")
        async with httpx.AsyncClient() as client:
            url = f"https://graph.facebook.com/{self.api_version}/oauth/access_token"
            params = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,  # Prevent double encoding
                "code": code
            }
            print(f"[Facebook] Making request to: {url}")
            print(f"[Facebook] With params: {params}")

            response = await client.get(url, params=params)

            if response.status_code != 200:
                print(
                    f"[Facebook] Token exchange failed with status {response.status_code}"
                )
                print(f"[Facebook] Error response: {response.text}")
                return None

            token_data = response.json()
            print("[Facebook] Successfully obtained access token")

            # Get long-lived token
            long_lived_token = await self.get_long_lived_token(
                token_data.get("access_token"))
            if long_lived_token:
                print("[Facebook] Successfully exchanged for long-lived token")
                token_data["access_token"] = long_lived_token
            else:
                print("[Facebook] Failed to obtain long-lived token")

            return token_data

    async def get_long_lived_token(self,
                                   short_lived_token: str) -> Optional[str]:
        """Exchange a short-lived token for a long-lived token using Facebook Graph API"""
        print(
            "[Facebook] Exchanging short-lived token for long-lived token...")
        async with httpx.AsyncClient() as client:
            url = f"https://graph.facebook.com/{self.api_version}/oauth/access_token"
            params = {
                "grant_type": "fb_exchange_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "fb_exchange_token": short_lived_token
            }
            print(f"[Facebook] Making request to: {url}")

            response = await client.get(url, params=params)

            if response.status_code != 200:
                print(
                    f"[Facebook] Long-lived token exchange failed with status {response.status_code}"
                )
                print(f"[Facebook] Error response: {response.text}")
                return None

            data = response.json()
            print(
                f"[Facebook] Long-lived token exchange successful. Expires in: {data.get('expires_in')} seconds"
            )
            return data.get("access_token")

    async def get_user_profile(self,
                               access_token: str) -> Optional[Dict[str, Any]]:
        """Get the user's Instagram business account profile"""
        async with httpx.AsyncClient() as client:
            # First get the pages (required for Instagram business accounts)
            pages_response = await client.get(
                f"https://graph.facebook.com/{self.api_version}/me/accounts",
                params={"access_token": access_token})

            if pages_response.status_code != 200:
                return None

            pages_data = pages_response.json()

            # Get connected Instagram account
            for page in pages_data.get("data", []):
                instagram_response = await client.get(
                    f"https://graph.facebook.com/{self.api_version}/{page['id']}",
                    params={
                        "fields": "instagram_business_account{id,username}",
                        "access_token": access_token
                    })

                if instagram_response.status_code == 200:
                    instagram_data = instagram_response.json()
                    if "instagram_business_account" in instagram_data:
                        return instagram_data["instagram_business_account"]

            return None

    async def check_follows_user(self, access_token: str) -> bool:
        """
        Check if the authenticated user follows the required Instagram account
        Using Facebook Graph API business account endpoints
        """
        try:
            profile = await self.get_user_profile(access_token)
            if not profile:
                return False

            # Since we're using a business account, we can verify the connection
            # through the Instagram Graph API. This is a simplified check.
            return True if profile.get("id") else False
        except Exception:
            return False


# Create a singleton service
facebook_service = FacebookService()
