from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.routers import auth, influencers, brands, portfolio, reviews, campaigns, deliverables, applications, content, assignments

app = FastAPI(
    title="InfluencerOS API",
    description="Backend API for InfluencerOS platform.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register global exception handlers
setup_exception_handlers(app)

# Include Routers
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(influencers.router, prefix="/api/v1/influencers")
app.include_router(brands.router, prefix="/api/v1/brands")
app.include_router(campaigns.router, prefix="/api/v1/campaigns")
app.include_router(deliverables.router, prefix="/api/v1/deliverables")
app.include_router(applications.router, prefix="/api/v1/applications")
app.include_router(assignments.router, prefix="/api/v1/assignments")
app.include_router(portfolio.router, prefix="/api/v1/influencers/portfolio")
app.include_router(content.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")

@app.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint that redirects to the API documentation.
    """
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint to verify the system is running.
    """
    return {"status": "ok"}
