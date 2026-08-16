import uuid
import pytest
from httpx import AsyncClient

@pytest.fixture
async def seeded_influencer(influencer_client: AsyncClient):
    uid = uuid.uuid4().hex[:8]
    username = f"inf_{uid}"
    profile_data = {
        "username": username,
        "bio": "Test bio",
        "category": "Tech",
        "follower_count": 1000,
        "engagement_rate": 0.05,
        "pricing": []
    }
    response = await influencer_client.post("/api/v1/influencers/profile", json=profile_data)
    assert response.status_code == 201
    return response.json()

@pytest.mark.asyncio
async def test_listing_influencers(client: AsyncClient, seeded_influencer):
    response = await client.get("/api/v1/influencers")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    usernames = [i["username"] for i in data["items"]]
    assert seeded_influencer["username"] in usernames

@pytest.mark.asyncio
async def test_filtering_by_category(client: AsyncClient, seeded_influencer):
    response_tech = await client.get("/api/v1/influencers?category=Tech")
    assert response_tech.status_code == 200
    tech_usernames = [i["username"] for i in response_tech.json()["items"]]
    assert seeded_influencer["username"] in tech_usernames
    
    response_fashion = await client.get("/api/v1/influencers?category=Fashion")
    assert response_fashion.status_code == 200
    fashion_usernames = [i["username"] for i in response_fashion.json()["items"]]
    assert seeded_influencer["username"] not in fashion_usernames

@pytest.mark.asyncio
async def test_fetching_single_influencer(client: AsyncClient, seeded_influencer):
    inf_id = seeded_influencer["id"]
    response = await client.get(f"/api/v1/influencers/{inf_id}")
    assert response.status_code == 200
    assert response.json()["username"] == seeded_influencer["username"]

@pytest.mark.asyncio
async def test_fetching_nonexistent_influencer(client: AsyncClient):
    response = await client.get("/api/v1/influencers/999999")
    assert response.status_code == 404
