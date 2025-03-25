
import httpx
import json
from typing import Any, Dict

BASE_URL = "http://0.0.0.0:8000"

async def test_endpoint(client: httpx.AsyncClient, path: str, method: str = "GET", data: Dict[str, Any] = None) -> None:
    print(f"\nTesting {method} {path}")
    try:
        if method == "GET":
            response = await client.get(f"{BASE_URL}{path}")
        elif method == "POST":
            response = await client.post(f"{BASE_URL}{path}", json=data)
            
        print(f"Status: {response.status_code}")
        print("Response:", json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")

async def main():
    async with httpx.AsyncClient() as client:
        # Test basic endpoints
        await test_endpoint(client, "/health")
        await test_endpoint(client, "/api/themes/list")
        
        # Test authentication
        await test_endpoint(client, "/api/auth/token", "POST", {
            "username": "test",
            "password": "test"
        })

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
