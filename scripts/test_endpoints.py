
import httpx
import json
from typing import Any, Dict

BASE_URL = "http://0.0.0.0:8000"

async def test_endpoint(client: httpx.AsyncClient, path: str, method: str = "GET", data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> None:
    print(f"\nTesting {method} {path}")
    try:
        if method == "GET":
            response = await client.get(f"{BASE_URL}{path}", headers=headers)
        elif method == "POST":
            response = await client.post(f"{BASE_URL}{path}", json=data, headers=headers)
            
        print(f"Status: {response.status_code}")
        print("Response:", json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")

async def main():
    async with httpx.AsyncClient() as client:
        # Test basic endpoints
        await test_endpoint(client, "/health")
        
        # Create test user
        await test_endpoint(client, "/api/auth/register", "POST", {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass"
        })
        
        # Get auth token
        response = await client.post(f"{BASE_URL}/api/auth/token", 
            data={"username": "testuser", "password": "testpass"})
        token = response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        # Test authenticated endpoints
        await test_endpoint(client, "/api/workflows/list", headers=auth_headers)
        await test_endpoint(client, "/api/user/me", headers=auth_headers)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
