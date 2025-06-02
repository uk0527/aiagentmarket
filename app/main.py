from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import auth_router

app = FastAPI(
    title="AI Agent Marketplace",
    description="A platform for buying and selling AI agents",
    version="1.0.0"
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth_router)

@app.get("/")
async def root():
    return {"message": "Welcome to AI Agent Marketplace API"} 