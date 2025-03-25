
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from main import app
from app.database import engine, Base
from app.config import settings

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "ok"

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_invalid_login():
    response = client.post("/api/auth/token", 
        data={"username": "invalid", "password": "invalid"})
    assert response.status_code == 401

def test_list_workflows():
    # First create a test user and get token
    test_user = {"username": "testuser", "email": "test@example.com", "password": "testpass"}
    client.post("/api/auth/register", json=test_user)
    
    response = client.post("/api/auth/token", 
        data={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Now test workflows endpoint with auth
    response = client.get("/api/workflows/list", 
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_database_connection():
    from app.utils.startup_validation import StartupValidator
    result = await StartupValidator.check_database_connection()
    assert result == True
