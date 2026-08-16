import uuid
import pytest
from httpx import AsyncClient

@pytest.fixture
async def setup_brand(brand_client: AsyncClient):
    uid = uuid.uuid4().hex[:8]
    profile_data = {
        "company_name": f"Brand {uid}",
        "industry": "Tech",
        "description": "Test"
    }
    res = await brand_client.put("/api/v1/brands/profile", json=profile_data)
    assert res.status_code == 200
    return brand_client

@pytest.fixture
async def setup_influencer(influencer_client: AsyncClient):
    uid = uuid.uuid4().hex[:8]
    profile_data = {
        "username": f"inf_{uid}",
        "bio": "Test bio",
        "category": "Tech",
        "follower_count": 1000,
        "engagement_rate": 0.05,
        "pricing": []
    }
    res = await influencer_client.post("/api/v1/influencers/profile", json=profile_data)
    assert res.status_code == 201
    return {"client": influencer_client, "profile": res.json()}

@pytest.mark.asyncio
async def test_brand_can_create_campaign(setup_brand: AsyncClient):
    payload = {
        "title": "Test Campaign",
        "description": "Desc",
        "budget": 500,
        "category": "Tech",
        "platform": "instagram",
        "requirements": "None",
        "start_date": "2026-09-01",
        "end_date": "2026-09-30"
    }
    res = await setup_brand.post("/api/v1/campaigns", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Test Campaign"
    assert data["status"] == "draft"

@pytest.mark.asyncio
async def test_influencer_can_apply(setup_brand: AsyncClient, setup_influencer: dict):
    # 1. Create campaign
    payload = {
        "title": "Test Campaign Apply",
        "description": "Desc",
        "budget": 500,
        "category": "Tech",
        "platform": "instagram",
        "requirements": "None",
        "start_date": "2026-09-01",
        "end_date": "2026-09-30"
    }
    res_camp = await setup_brand.post("/api/v1/campaigns", json=payload)
    camp_id = res_camp.json()["id"]

    # 1b. Publish campaign
    res_pub = await setup_brand.put(f"/api/v1/campaigns/{camp_id}", json={"status": "open"})
    assert res_pub.status_code == 200

    # 2. Apply
    inf_client = setup_influencer["client"]
    apply_payload = {
        "proposal": "I am great",
        "proposed_price": 500
    }
    res_apply = await inf_client.post(f"/api/v1/campaigns/{camp_id}/apply", json=apply_payload)
    assert res_apply.status_code == 201
    assert res_apply.json()["status"] == "pending"

@pytest.mark.asyncio
async def test_brand_can_accept_application(setup_brand: AsyncClient, setup_influencer: dict):
    # 1. Create campaign
    payload = {
        "title": "Test Campaign Accept",
        "description": "Desc",
        "budget": 500,
        "category": "Tech",
        "platform": "instagram",
        "requirements": "None",
        "start_date": "2026-09-01",
        "end_date": "2026-09-30"
    }
    res_camp = await setup_brand.post("/api/v1/campaigns", json=payload)
    camp_id = res_camp.json()["id"]

    # 1b. Publish campaign
    res_pub = await setup_brand.put(f"/api/v1/campaigns/{camp_id}", json={"status": "open"})
    assert res_pub.status_code == 200

    # 2. Apply
    inf_client = setup_influencer["client"]
    apply_payload = {
        "proposal": "I am great",
        "proposed_price": 500
    }
    res_apply = await inf_client.post(f"/api/v1/campaigns/{camp_id}/apply", json=apply_payload)
    app_id = res_apply.json()["id"]

    # 3. Accept application
    res_accept = await setup_brand.put(f"/api/v1/applications/{app_id}/status", json={"status": "accepted"})
    assert res_accept.status_code == 200
    assert res_accept.json()["status"] == "accepted"

    # Verify assignment is created
    res_camp2 = await setup_brand.get(f"/api/v1/campaigns/{camp_id}")
    assert res_camp2.status_code == 200
    assignments = res_camp2.json().get("assignments", [])
    assert len(assignments) == 1
    assert assignments[0]["influencer"]["id"] == setup_influencer["profile"]["id"]

@pytest.mark.asyncio
async def test_influencer_cannot_create_campaign(setup_influencer: dict):
    inf_client = setup_influencer["client"]
    payload = {
        "title": "Test",
        "description": "Desc",
        "budget": 500,
        "category": "Tech",
        "platform": "instagram",
        "requirements": "None"
    }
    res = await inf_client.post("/api/v1/campaigns", json=payload)
    assert res.status_code == 403
