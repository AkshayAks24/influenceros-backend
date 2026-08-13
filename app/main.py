from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

app = FastAPI(
    title="InfluencerOS API",
    description="Backend API for InfluencerOS platform.",
    version="0.1.0",
)

# CORS placeholder - to be configured later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Placeholder, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
