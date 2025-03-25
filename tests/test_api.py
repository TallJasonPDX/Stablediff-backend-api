
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

def test_list_themes():
    response = client.get("/api/themes/list")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_database_connection():
    from app.utils.startup_validation import StartupValidator
    result = await StartupValidator.check_database_connection()
    assert result == True
