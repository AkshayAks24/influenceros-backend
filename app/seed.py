import asyncio
import random
from datetime import datetime, timedelta, timezone, date
from sqlalchemy import select, func

from app.db.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.brand import BrandProfile
from app.models.favorite import Favorite
from app.models.influencer import InfluencerProfile
from app.models.portfolio import Portfolio
from app.models.campaign import Campaign, CampaignStatus
from app.models.deliverable import Deliverable
from app.models.application import CampaignApplication, ApplicationStatus, CampaignAssignment, AssignmentPhase
from app.models.content import SubmittedContent, ContentStatus, ContentComment, StatusLog
from app.models.review import Review
from app.models.notification import Notification, NotificationType
from app.models.message import Message
from app.models.pricing_plan import PricingPlan, BillingCycle
from app.models.metric_snapshot import MetricSnapshot, OwnerType
from app.core.security import hash_password

random.seed(42)

async def run_seed():
    async with AsyncSessionLocal() as db:
        # Safety Check
        existing_users = (await db.execute(select(func.count(User.id)))).scalar()
        if existing_users is not None and existing_users > 0:
            print("Database is not empty — refusing to seed. Wipe it first if you want a fresh seed.")
            return

        try:
            print("Starting database seed...")
            password_hash = hash_password("Password123!")
            credentials_list = []

            # 1. PRICING PLANS
            print("Seeding Pricing Plans...")
            plans = [
                PricingPlan(name="Starter", price=49.0, billing_cycle=BillingCycle.monthly, features=["Basic search", "5 Campaigns/mo"], is_highlighted=False),
                PricingPlan(name="Growth", price=149.0, billing_cycle=BillingCycle.monthly, features=["Advanced AI matching", "Unlimited Campaigns", "Analytics"], is_highlighted=True),
                PricingPlan(name="Enterprise", price=499.0, billing_cycle=BillingCycle.monthly, features=["White-label reporting", "Dedicated Account Manager", "API Access"], is_highlighted=False)
            ]
            db.add_all(plans)

            # 2. BRANDS
            print("Seeding Brands...")
            brand_companies = ["Lumina Tech", "Aura Beauty", "Peak Fitness", "Craze Fashion", "Fresh Foodies"]
            brand_profiles = []
            brands = []
            for i, company in enumerate(brand_companies):
                email = f"brand{i+1}@example.com"
                user = User(email=email, name=company, password_hash=password_hash, role=UserRole.brand)
                db.add(user)
                await db.flush()
                credentials_list.append((email, "Password123!", "Brand"))

                profile = BrandProfile(
                    user_id=user.id, company_name=company, industry=company.split()[1],
                    website=f"https://{company.lower().replace(' ', '')}.com", description=f"Leading the industry in {company.split()[1]}."
                )
                db.add(profile)
                await db.flush()
                brand_profiles.append(profile)
                brands.append({"user": user, "profile": profile})

            # 3. INFLUENCERS
            print("Seeding Influencers...")
            influencer_categories = ["Fashion", "Tech", "Fitness", "Beauty", "Food"]
            influencer_profiles = []
            influencers = []
            for i in range(15):
                name = f"Influencer {i+1}"
                username = f"influencer{i+1}"
                email = f"influencer{i+1}@example.com"
                user = User(email=email, name=name, password_hash=password_hash, role=UserRole.influencer)
                db.add(user)
                await db.flush()
                credentials_list.append((email, "Password123!", "Influencer"))

                category = influencer_categories[i % len(influencer_categories)]
                follower_count = random.randint(10000, 2000000)
                profile = InfluencerProfile(
                    user_id=user.id, username=username, bio=f"I love making content about {category}.",
                    category=category, platforms={"instagram": f"@inf_{i+1}", "tiktok": f"@inf_{i+1}"},
                    follower_count=follower_count, engagement_rate=random.uniform(0.015, 0.085),
                    trust_score=random.randint(75, 98),
                    trust_score_breakdown={"authenticity": random.randint(80, 100), "consistency": random.randint(70, 95)},
                    pricing=[{"type": "instagram_post", "price": random.randint(100, 1500)}, {"type": "tiktok_video", "price": random.randint(200, 2000)}]
                )
                db.add(profile)
                await db.flush()
                influencer_profiles.append(profile)
                influencers.append({"user": user, "profile": profile})

                # Portfolios
                for j in range(random.randint(2, 3)):
                    pf = Portfolio(influencer_id=profile.id, title=f"{category} Campaign {j+1}", description="Great results.", media_url=f"https://example.com/portfolio_{i}_{j}.jpg")
                    db.add(pf)

            # 4. FAVORITES
            print("Seeding Favorites...")
            for brand in brands:
                favs = random.sample(influencer_profiles, random.randint(1, 3))
                for fav in favs:
                    db.add(Favorite(brand_id=brand["profile"].id, influencer_id=fav.id))

            # 5. METRIC SNAPSHOTS
            print("Seeding Metric Snapshots...")
            today = datetime.now(timezone.utc).date()
            for inf in influencer_profiles:
                for month_idx in range(6):
                    rec_date = today - timedelta(days=30 * (5 - month_idx))
                    trend_multiplier = 1.0 + (month_idx * 0.05)
                    db.add(MetricSnapshot(owner_type=OwnerType.influencer, owner_id=inf.id, metric_name="followers", value=inf.follower_count * trend_multiplier, recorded_at=rec_date))
                    db.add(MetricSnapshot(owner_type=OwnerType.influencer, owner_id=inf.id, metric_name="earnings", value=random.randint(500, 2000) * trend_multiplier, recorded_at=rec_date))
            
            for brand in brand_profiles:
                for month_idx in range(6):
                    rec_date = today - timedelta(days=30 * (5 - month_idx))
                    trend_multiplier = 1.0 + (month_idx * 0.1)
                    db.add(MetricSnapshot(owner_type=OwnerType.brand, owner_id=brand.id, metric_name="reach", value=random.randint(50000, 200000) * trend_multiplier, recorded_at=rec_date))
                    db.add(MetricSnapshot(owner_type=OwnerType.brand, owner_id=brand.id, metric_name="roi", value=random.uniform(1.2, 3.5) * trend_multiplier, recorded_at=rec_date))

            # 6. CAMPAIGNS & RELATED DATA
            print("Seeding Campaigns & Deliverables...")
            
            # Setup specific campaign statuses
            campaign_configs = [
                {"status": CampaignStatus.draft, "assignments": 0},
                {"status": CampaignStatus.cancelled, "assignments": 1, "assignment_phase": AssignmentPhase.content_creation},
                {"status": CampaignStatus.open, "assignments": 0},
                {"status": CampaignStatus.in_progress, "assignments": 1, "assignment_phase": AssignmentPhase.review, "content": True},
                {"status": CampaignStatus.completed, "assignments": 1, "assignment_phase": AssignmentPhase.completed},
                {"status": CampaignStatus.completed, "assignments": 1, "assignment_phase": AssignmentPhase.completed},
                {"status": CampaignStatus.in_progress, "assignments": 2, "assignment_phase": AssignmentPhase.brief_sent}, # 2+ assignments
                {"status": CampaignStatus.in_review, "assignments": 1, "assignment_phase": AssignmentPhase.review, "content": True},
                {"status": CampaignStatus.open, "assignments": 0},
                {"status": CampaignStatus.completed, "assignments": 1, "assignment_phase": AssignmentPhase.completed}
            ]

            campaigns_list = []
            for i, config in enumerate(campaign_configs):
                brand = brands[i % len(brands)]
                status = config["status"]
                
                campaign = Campaign(
                    brand_id=brand["profile"].id, title=f"Campaign {status} {i}",
                    description=f"Description for {status} campaign.",
                    budget=random.randint(2000, 10000), category=influencer_categories[i % len(influencer_categories)],
                    platform="instagram", requirements="Need good lighting.",
                    status=status,
                    start_date=today,
                    end_date=today + timedelta(days=30)
                )
                db.add(campaign)
                await db.flush()
                campaigns_list.append(campaign)

                # Deliverables
                for d in range(random.randint(2, 4)):
                    db.add(Deliverable(campaign_id=campaign.id, description=f"Deliverable {d+1} for Campaign {i}"))

                # Applications & Assignments
                if status != CampaignStatus.draft:
                    # Random pending applications
                    pending_applicants = random.sample(influencer_profiles, 2)
                    for p in pending_applicants:
                        app = CampaignApplication(campaign_id=campaign.id, influencer_id=p.id, proposal="I can do this!", proposed_price=500.0, status=ApplicationStatus.pending)
                        db.add(app)
                        
                    # Random rejected applications
                    rejected_applicant = random.choice([inf for inf in influencer_profiles if inf not in pending_applicants])
                    rej_app = CampaignApplication(campaign_id=campaign.id, influencer_id=rejected_applicant.id, proposal="Too expensive", proposed_price=5000.0, status=ApplicationStatus.rejected)
                    db.add(rej_app)
                    
                    db.add(Notification(user_id=rejected_applicant.user_id, title="Application Rejected", message=f"Application to {campaign.title} was rejected.", type=NotificationType.campaign_update))

                    # Assignments
                    num_assignments = config["assignments"]
                    if isinstance(num_assignments, int) and num_assignments > 0:
                        chosen_infs = random.sample([inf for inf in influencer_profiles if inf not in pending_applicants and inf != rejected_applicant], num_assignments)
                        for inf in chosen_infs:
                            # Accepted App
                            acc_app = CampaignApplication(campaign_id=campaign.id, influencer_id=inf.id, proposal="Perfect fit", proposed_price=1000.0, status=ApplicationStatus.accepted)
                            db.add(acc_app)
                            await db.flush()
                            
                            db.add(Notification(user_id=inf.user_id, title="Application Accepted", message=f"Application to {campaign.title} was accepted!", type=NotificationType.campaign_update))

                            phase = config["assignment_phase"]
                            assignment = CampaignAssignment(campaign_id=campaign.id, influencer_id=inf.id, application_id=acc_app.id, current_phase=phase)
                            db.add(assignment)
                            await db.flush()
                            
                            db.add(StatusLog(campaign_id=campaign.id, actor_id=brand["user"].id, from_status="draft", to_status=status, note="Initial setup"))
                            db.add(StatusLog(campaign_id=campaign.id, actor_id=brand["user"].id, from_status="draft", to_status=phase, note="Phase moved"))

                            # Messages
                            msg = Message(sender_id=brand["user"].id, receiver_id=inf.user_id, message="Welcome to the campaign!")
                            db.add(msg)
                            db.add(Notification(user_id=inf.user_id, title="New Message", message="You have a new message.", type=NotificationType.message))

                            # Content
                            if config.get("content") or phase in (AssignmentPhase.review, AssignmentPhase.approved, AssignmentPhase.completed):
                                content_status = ContentStatus.approved if phase in (AssignmentPhase.approved, AssignmentPhase.completed) else ContentStatus.pending_review
                                content = SubmittedContent(assignment_id=assignment.id, media_url="https://example.com/content.jpg", caption="Check this out", status=content_status)
                                db.add(content)
                                await db.flush()
                                
                                # Comments
                                comment = ContentComment(content_id=content.id, author_id=brand["user"].id, comment="Looks great!")
                                db.add(comment)

                                if content_status == ContentStatus.approved:
                                    db.add(Notification(user_id=inf.user_id, title="Content Review", message="Your content was approved!", type=NotificationType.campaign_update))

                            # Reviews (Only if completed)
                            if status == CampaignStatus.completed:
                                review = Review(brand_id=brand["profile"].id, influencer_id=inf.id, campaign_id=campaign.id, rating=random.randint(4, 5), comment="Amazing work!")
                                db.add(review)

            await db.commit()
            
            print("\n[SUCCESS] Seeding complete! Here are your test accounts:\n")
            print(f"{'Role':<15} | {'Email':<30} | {'Password'}")
            print("-" * 65)
            for email, pwd, role in credentials_list:
                print(f"{role:<15} | {email:<30} | {pwd}")
                
        except Exception as e:
            await db.rollback()
            print(f"\n[ERROR] Seeding failed with error: {e}")
            print("Transaction rolled back.")

if __name__ == "__main__":
    asyncio.run(run_seed())
