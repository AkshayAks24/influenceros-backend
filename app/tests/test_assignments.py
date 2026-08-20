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
        "bio": "Test",
        "category": "Tech",
        "follower_count": 1000,
        "engagement_rate": 0.05,
        "pricing": []
    }
    res = await influencer_client.put("/api/v1/influencers/profile", json=profile_data)
    assert res.status_code == 200
    return {"client": influencer_client, "profile": res.json()}

@pytest.fixture
async def setup_assignment(setup_brand: AsyncClient, setup_influencer: dict):
    # Create campaign
    payload = {
        "title": "Timeline Campaign",
        "description": "Test",
        "budget": 500,
        "category": "Tech",
        "platform": "instagram",
        "requirements": "None",
        "start_date": "2026-09-01",
        "end_date": "2026-09-30"
    }
    res_camp = await setup_brand.post("/api/v1/campaigns", json=payload)
    assert res_camp.status_code == 201
    camp_id = res_camp.json()["id"]

    # Publish campaign
    await setup_brand.put(f"/api/v1/campaigns/{camp_id}", json={"status": "open"})

    # Apply
    inf_client = setup_influencer["client"]
    apply_payload = {"proposal": "Test", "proposed_price": 500}
    res_apply = await inf_client.post(f"/api/v1/campaigns/{camp_id}/apply", json=apply_payload)
    assert res_apply.status_code == 201
    app_id = res_apply.json()["id"]

    # Accept Application
    res_acc = await setup_brand.put(f"/api/v1/applications/{app_id}/status", json={"status": "accepted"})
    assert res_acc.status_code == 200
    
    # Get Assignment ID
    res_camp2 = await setup_brand.get(f"/api/v1/campaigns/{camp_id}")
    assignment_id = res_camp2.json()["assignments"][0]["id"]

    return {
        "brand_client": setup_brand,
        "inf_client": inf_client,
        "campaign_id": camp_id,
        "assignment_id": assignment_id
    }

@pytest.mark.asyncio
async def test_valid_transitions_and_status_logs(setup_assignment: dict):
    inf_client = setup_assignment["inf_client"]
    brand_client = setup_assignment["brand_client"]
    assignment_id = setup_assignment["assignment_id"]
    campaign_id = setup_assignment["campaign_id"]

    # 1. brief_sent -> content_creation
    res_accept_brief = await inf_client.patch(f"/api/v1/assignments/{assignment_id}/phase", json={"phase": "content_creation"})
    assert res_accept_brief.status_code == 200
    assert res_accept_brief.json()["current_phase"] == "content_creation"

    # 2. Upload Content (content_creation -> review)
    res_submit = await inf_client.post(f"/api/v1/assignments/{assignment_id}/content", json={"media_url": "http://example.com/draft", "caption_draft": "Check this out"})
    assert res_submit.status_code == 201
    content_id = res_submit.json()["id"]

    # Verify assignment phase updated automatically
    res_assign = await brand_client.get(f"/api/v1/campaigns/{campaign_id}")
    assert res_assign.json()["assignments"][0]["current_phase"] == "review"

    # 3. Review Content (review -> approved)
    res_review = await brand_client.patch(f"/api/v1/content/{content_id}/review", json={"decision": "approved", "note": "Looks good"})
    assert res_review.status_code == 200

    # Verify assignment phase
    res_assign2 = await brand_client.get(f"/api/v1/campaigns/{campaign_id}")
    assert res_assign2.json()["assignments"][0]["current_phase"] == "approved"
    
    # Check status logs
    logs = res_assign2.json()["status_logs"]
    transitions = [(log["from_status"], log["to_status"]) for log in logs]
    assert (None, "brief_sent") in transitions
    assert ("brief_sent", "content_creation") in transitions
    assert ("content_creation", "review") in transitions
    assert ("review", "approved") in transitions

@pytest.mark.asyncio
async def test_invalid_skip_transition_409(setup_assignment: dict):
    inf_client = setup_assignment["inf_client"]
    assignment_id = setup_assignment["assignment_id"]
    
    # Assignment is in brief_sent. Try submitting a live URL (requires approved).
    res_live = await inf_client.post(f"/api/v1/assignments/{assignment_id}/live-url", json={"live_url": "https://instagram.com/p/test"})
    assert res_live.status_code == 409

@pytest.mark.asyncio
async def test_wrong_role_transition_403(setup_assignment: dict):
    brand_client = setup_assignment["brand_client"]
    assignment_id = setup_assignment["assignment_id"]
    
    # Try accepting the brief as the Brand
    res_accept = await brand_client.patch(f"/api/v1/assignments/{assignment_id}/phase", json={"phase": "content_creation"})
    assert res_accept.status_code == 403

@pytest.mark.asyncio
async def test_ownership_violation_403(setup_assignment: dict, client: AsyncClient):
    assignment_id = setup_assignment["assignment_id"]
    
    # Unassigned Influencer
    uid = uuid.uuid4().hex[:8]
    inf_res = await client.post("/api/v1/auth/register", json={"email": f"inf_{uid}@test.com", "password": "Password123!", "name": f"inf_{uid}", "role": "influencer"})
    inf_token = inf_res.json()["access_token"]
    
    await client.put("/api/v1/influencers/profile", json={"username": f"inf_{uid}", "bio": "Test", "category": "Tech", "follower_count": 1000, "engagement_rate": 0.05, "pricing": []}, headers={"Authorization": f"Bearer {inf_token}"})
    
    res = await client.patch(f"/api/v1/assignments/{assignment_id}/phase", json={"phase": "content_creation"}, headers={"Authorization": f"Bearer {inf_token}"})
    assert res.status_code == 403

    # Unassigned Brand
    uid2 = uuid.uuid4().hex[:8]
    brand_res = await client.post("/api/v1/auth/register", json={"email": f"brand_{uid2}@test.com", "password": "Password123!", "name": f"brand_{uid2}", "role": "brand"})
    brand_token = brand_res.json()["access_token"]
    
    await client.put("/api/v1/brands/profile", json={"company_name": f"Brand {uid2}", "industry": "Tech", "description": "Test"}, headers={"Authorization": f"Bearer {brand_token}"})
    
    res2 = await client.patch(f"/api/v1/assignments/{assignment_id}/phase", json={"phase": "completed"}, headers={"Authorization": f"Bearer {brand_token}"})
    assert res2.status_code == 403

@pytest.mark.asyncio
async def test_duplicate_transition_409(setup_assignment: dict):
    inf_client = setup_assignment["inf_client"]
    assignment_id = setup_assignment["assignment_id"]
    
    # First accept brief
    res1 = await inf_client.patch(f"/api/v1/assignments/{assignment_id}/phase", json={"phase": "content_creation"})
    assert res1.status_code == 200
    
    # Duplicate
    res2 = await inf_client.patch(f"/api/v1/assignments/{assignment_id}/phase", json={"phase": "content_creation"})
    assert res2.status_code == 409

@pytest.mark.asyncio
async def test_live_url_validation(setup_assignment: dict):
    inf_client = setup_assignment["inf_client"]
    brand_client = setup_assignment["brand_client"]
    assignment_id = setup_assignment["assignment_id"]
    
    # Move to approved
    await inf_client.patch(f"/api/v1/assignments/{assignment_id}/phase", json={"phase": "content_creation"})
    res_sub = await inf_client.post(f"/api/v1/assignments/{assignment_id}/content", json={"media_url": "x", "caption_draft": "x"})
    content_id = res_sub.json()["id"]
    await brand_client.patch(f"/api/v1/content/{content_id}/review", json={"decision": "approved"})

    # Try bad URLs
    res_bad1 = await inf_client.post(f"/api/v1/assignments/{assignment_id}/live-url", json={"live_url": "   "})
    assert res_bad1.status_code == 400
    
    res_bad2 = await inf_client.post(f"/api/v1/assignments/{assignment_id}/live-url", json={"live_url": "not-a-link"})
    assert res_bad2.status_code == 400

    # Try valid URL
    res_good = await inf_client.post(f"/api/v1/assignments/{assignment_id}/live-url", json={"live_url": "https://instagram.com/p/123"})
    assert res_good.status_code == 200
    assert res_good.json()["live_url"] == "https://instagram.com/p/123"
    assert res_good.json()["current_phase"] == "live"

@pytest.mark.asyncio
async def test_request_changes_reverts_phase(setup_assignment: dict):
    inf_client = setup_assignment["inf_client"]
    brand_client = setup_assignment["brand_client"]
    assignment_id = setup_assignment["assignment_id"]
    campaign_id = setup_assignment["campaign_id"]
    
    await inf_client.patch(f"/api/v1/assignments/{assignment_id}/phase", json={"phase": "content_creation"})
    res_sub = await inf_client.post(f"/api/v1/assignments/{assignment_id}/content", json={"media_url": "x", "caption_draft": "x"})
    content_id = res_sub.json()["id"]
    
    # Brand requests changes
    res_review = await brand_client.patch(f"/api/v1/content/{content_id}/review", json={"decision": "changes_requested"})
    assert res_review.status_code == 200

    res_camp = await brand_client.get(f"/api/v1/campaigns/{campaign_id}")
    assert res_camp.json()["assignments"][0]["current_phase"] == "content_creation"

@pytest.mark.asyncio
async def test_campaign_level_completion(setup_assignment: dict):
    inf_client = setup_assignment["inf_client"]
    brand_client = setup_assignment["brand_client"]
    assignment_id = setup_assignment["assignment_id"]
    campaign_id = setup_assignment["campaign_id"]

    # Rush the first assignment to 'live'
    await inf_client.patch(f"/api/v1/assignments/{assignment_id}/phase", json={"phase": "content_creation"})
    res_sub = await inf_client.post(f"/api/v1/assignments/{assignment_id}/content", json={"media_url": "x", "caption_draft": "x"})
    await brand_client.patch(f"/api/v1/content/{res_sub.json()['id']}/review", json={"decision": "approved"})
    await inf_client.post(f"/api/v1/assignments/{assignment_id}/live-url", json={"live_url": "https://instagram.com/p/123"})
    
    # Check campaign status before complete
    res_camp1 = await brand_client.get(f"/api/v1/campaigns/{campaign_id}")
    assert res_camp1.json()["status"] == "open"
    
    # Brand completes the assignment
    res_comp = await brand_client.patch(f"/api/v1/assignments/{assignment_id}/phase", json={"phase": "completed"})
    assert res_comp.status_code == 200

    # Because there is only 1 assignment, the campaign should now be completed
    res_camp2 = await brand_client.get(f"/api/v1/campaigns/{campaign_id}")
    assert res_camp2.json()["status"] == "completed"

@pytest.mark.asyncio
async def test_notifications_generated_for_transitions(setup_assignment: dict):
    inf_client = setup_assignment["inf_client"]
    brand_client = setup_assignment["brand_client"]
    assignment_id = setup_assignment["assignment_id"]
    
    # Check notifications before we start (should just have the 'Application Accepted' notification for influencer)
    res_inf_notif1 = await inf_client.get("/api/v1/notifications")
    assert any("accepted" in n["title"].lower() for n in res_inf_notif1.json()["items"])
    
    # 1. brief_sent -> content_creation (Brand gets notified)
    await inf_client.patch(f"/api/v1/assignments/{assignment_id}/phase", json={"phase": "content_creation"})
    res_brand_notif1 = await brand_client.get("/api/v1/notifications")
    assert any("accepted the brief" in n["message"].lower() for n in res_brand_notif1.json()["items"])

    # 2. content_creation -> review (Brand gets notified)
    res_sub = await inf_client.post(f"/api/v1/assignments/{assignment_id}/content", json={"media_url": "x", "caption_draft": "x"})
    content_id = res_sub.json()["id"]
    res_brand_notif2 = await brand_client.get("/api/v1/notifications")
    assert any("submitted draft content" in n["message"].lower() for n in res_brand_notif2.json()["items"])

    # 3. review -> content_creation [Request changes] (Influencer gets notified)
    await brand_client.patch(f"/api/v1/content/{content_id}/review", json={"decision": "changes_requested"})
    res_inf_notif2 = await inf_client.get("/api/v1/notifications")
    assert any("changes were requested" in n["message"].lower() for n in res_inf_notif2.json()["items"])

    # re-submit
    res_sub2 = await inf_client.post(f"/api/v1/assignments/{assignment_id}/content", json={"media_url": "y", "caption_draft": "y"})
    content_id2 = res_sub2.json()["id"]
    
    await brand_client.patch(f"/api/v1/content/{content_id2}/review", json={"decision": "approved"})
    res_inf_notif3 = await inf_client.get("/api/v1/notifications")
    assert any("approved" in n["message"].lower() for n in res_inf_notif3.json()["items"])

    # 5. approved -> live (Brand gets notified)
    await inf_client.post(f"/api/v1/assignments/{assignment_id}/live-url", json={"live_url": "https://instagram.com/p/123"})
    res_brand_notif3 = await brand_client.get("/api/v1/notifications")
    assert any("live post link" in n["message"].lower() for n in res_brand_notif3.json()["items"])

    # 6. live -> completed (Influencer gets notified)
    await brand_client.patch(f"/api/v1/assignments/{assignment_id}/phase", json={"phase": "completed"})
    res_inf_notif4 = await inf_client.get("/api/v1/notifications")
    assert any("marked as completed" in n["message"].lower() for n in res_inf_notif4.json()["items"])
