import os
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional

# Load environment variables from .env file
load_dotenv()

class Settings:
    # App settings
    APP_NAME = "FinTech AI Suite"
    API_PREFIX = "/api"
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "changethiskeyinproduction!")
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fintech.db")
    
    # Stripe integration
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    
    # OpenRouter API (for LLM capabilities)
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
    
    # OAuth providers
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    # Subscription tiers
    SUBSCRIPTION_TIERS: Dict[str, Dict[str, Any]] = {
        "basic": {
            "name": "Basic",
            "monthly_price": 0.00,
            "features": [
                "Access to Portfolio Analysis",
                "Limited API calls",
                "Single portfolio"
            ],
            "agents": ["portfolio_agent"],
            "price_id": None  # No price for free tier
        },
        "professional": {
            "name": "Professional",
            "monthly_price": 29.99,
            "features": [
                "Everything in Basic",
                "Access to Stock Finder",
                "Access to Options Strategy Advisor",
                "Access to ETF Screener",
                "Access to Financial News Analyzer",
                "API access",
                "Up to 5 portfolios"
            ],
            "agents": [
                "portfolio_agent",
                "stockfinder",
                "newsagent",
                "options_strategy_agent",
                "etf_screener_agent",
            ],
            "price_id": os.getenv("STRIPE_PRICE_ID_PRO")
        },
        "enterprise": {
            "name": "Enterprise",
            "monthly_price": 99.99,
            "features": [
                "Everything in Professional",
                "Access to Social Sentiment Analyzer",
                "Access to Macro & Sector Analyzer",
                "Access to Trading Agent",
                "Access to Portfolio Advisor",
                "Unlimited portfolios",
                "Priority support"
            ],
            "agents": [
                "portfolio_agent",
                "stockfinder",
                "newsagent",
                "options_strategy_agent",
                "etf_screener_agent",
                "social_sentiment_agent",
                "macro_sector_agent",
                "tradeagent",
                "portfolioadvisoragent"
            ],
            "price_id": os.getenv("STRIPE_PRICE_ID_ENTERPRISE")
        }
    }

settings = Settings() 