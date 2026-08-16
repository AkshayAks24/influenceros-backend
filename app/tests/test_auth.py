import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_successful_registration(client: AsyncClient):
    payload = {
        "email": "testreg@example.com",
        "password": "Password123!",
        "name": "Test Reg",
        "role": "brand"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "testreg@example.com"

@pytest.mark.asyncio
async def test_duplicate_email_registration(client: AsyncClient):
    payload = {
        "email": "dup@example.com",
        "password": "Password123!",
        "name": "Test Dup",
        "role": "brand"
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_successful_login(client: AsyncClient):
    payload = {
        "email": "login@example.com",
        "password": "Password123!",
        "name": "Test Login",
        "role": "influencer"
    }
    await client.post("/api/v1/auth/register", json=payload)
    
    login_data = {
        "email": payload["email"],
        "password": payload["password"]
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    payload = {
        "email": "wrongpass@example.com",
        "password": "Password123!",
        "name": "Test Wrong",
        "role": "brand"
    }
    await client.post("/api/v1/auth/register", json=payload)
    
    login_data = {
        "email": payload["email"],
        "password": "WrongPassword!"
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401
