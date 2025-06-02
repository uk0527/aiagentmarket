from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging
import importlib
import inspect

from app.database import get_db
from app.auth import check_agent_access
from app.config import settings
from app.models import UserAgent, AgentUsage, AgentListing

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])

class AgentInfo(BaseModel):
    id: str
    name: str
    description: str
    subscription_tier: str
    enabled: bool

class AgentResponse(BaseModel):
    agent_id: str
    result: Dict[str, Any]

class AgentCreateRequest(BaseModel):
    name: str
    short_description: str
    category: str

# Agent endpoints - Dynamically create endpoints for all agents
AGENT_MODULES = {
    "portfolio_agent": {"module": "portfolio_agent", "class": "PortfolioAgent", "name": "Portfolio Analyzer"},
    "stockfinder": {"module": "stockfinder", "class": "StockFinder", "name": "Stock Finder"},
    "newsagent": {"module": "newsagent", "class": "NewsAgent", "name": "Financial News Analyzer"},
    "options_strategy_agent": {"module": "options_strategy_agent", "class": "OptionsStrategyAgent", "name": "Options Strategy Advisor"},
    "etf_screener_agent": {"module": "etf_screener_agent", "class": "ETFScreenerAgent", "name": "ETF Screener"},
    "social_sentiment_agent": {"module": "social_sentiment_agent", "class": "SocialSentimentAgent", "name": "Social Sentiment Analyzer"},
    "macro_sector_agent": {"module": "macro_sector_agent", "class": "MacroSectorAgent", "name": "Macro & Sector Analyzer"},
    "tradeagent": {"module": "tradeagent", "class": "TradeAgent", "name": "Trading Agent"},
    "portfolioadvisoragent": {"module": "portfolioadvisoragent", "class": "PortfolioAdvisorAgent", "name": "Portfolio Advisor"}
}

AGENT_DESCRIPTIONS = {
    "portfolio_agent": "Analyze and optimize investment portfolios with risk metrics and diversification analysis.",
    "stockfinder": "Discover and screen stocks based on financial metrics and market data.",
    "newsagent": "Analyze financial news and extract actionable insights for your investments.",
    "options_strategy_agent": "Get options trading strategies tailored to your market outlook.",
    "etf_screener_agent": "Screen and analyze ETFs based on various criteria.",
    "social_sentiment_agent": "Track social media sentiment for stocks and identify market trends.",
    "macro_sector_agent": "Analyze macroeconomic trends and sector performance.",
    "tradeagent": "Execute trades with smart order routing and timing strategies.",
    "portfolioadvisoragent": "Get personalized portfolio advice and recommendations."
}

# Agent module cache
agent_instances = {}

async def get_agent_instance(agent_id: str):
    """
    Get an instance of an agent by ID, with caching
    """
    if agent_id in agent_instances:
        return agent_instances[agent_id]
    
    agent_info = AGENT_MODULES.get(agent_id)
    if not agent_info:
        raise ValueError(f"Unknown agent ID: {agent_id}")
    
    try:
        module = importlib.import_module(agent_info["module"])
        agent_class = getattr(module, agent_info["class"])
        
        # Check if class has an __init__ that takes openrouter_api_key
        init_params = inspect.signature(agent_class.__init__).parameters
        if "api_key" in init_params:
            instance = agent_class(api_key=settings.OPENROUTER_API_KEY)
        else:
            instance = agent_class()
        
        agent_instances[agent_id] = instance
        return instance
    except Exception as e:
        logger.error(f"Error loading agent {agent_id}: {str(e)}")
        raise ValueError(f"Failed to load agent {agent_id}: {str(e)}")

@router.get("/")
def list_agents(db: Session = Depends(get_db)):
    agents = db.query(AgentListing).all()
    return agents

@router.post("/")
def create_agent(request: AgentCreateRequest, db: Session = Depends(get_db)):
    agent = AgentListing(
        name=request.name,
        short_description=request.short_description,
        category=request.category
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent

@router.get("/{agent_id}")
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(AgentListing).filter(AgentListing.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.get("/list", response_model=List[AgentInfo])
async def list_agents(user_data: Dict[str, Any] = Depends(check_agent_access), db: Session = Depends(get_db)):
    """
    List all available agents
    """
    user_id = user_data["user"].id
    tier = user_data["tier"]
    
    # Get user's enabled agents
    user_agents = {ua.agent_id: ua.is_enabled for ua in db.query(UserAgent).filter(UserAgent.user_id == user_id).all()}
    
    # Get available agents for user's tier
    available_agents = []
    for tier_id, tier_data in settings.SUBSCRIPTION_TIERS.items():
        for agent_id in tier_data["agents"]:
            if agent_id not in [a.id for a in available_agents]:
                # Determine which tier this agent first appears in
                for t_id, t_data in settings.SUBSCRIPTION_TIERS.items():
                    if agent_id in t_data["agents"]:
                        subscription_tier = t_id
                        break
                
                available_agents.append(AgentInfo(
                    id=agent_id,
                    name=AGENT_MODULES.get(agent_id, {}).get("name", agent_id),
                    description=AGENT_DESCRIPTIONS.get(agent_id, ""),
                    subscription_tier=subscription_tier,
                    enabled=user_agents.get(agent_id, agent_id in settings.SUBSCRIPTION_TIERS[tier]["agents"])
                ))
    
    return available_agents

@router.post("/{agent_id}/toggle", response_model=AgentInfo)
async def toggle_agent(
    agent_id: str,
    enabled: bool,
    user_data: Dict[str, Any] = Depends(check_agent_access),
    db: Session = Depends(get_db)
):
    """
    Enable or disable an agent for a user
    """
    user_id = user_data["user"].id
    tier = user_data["tier"]
    
    # Check if agent is available in user's tier
    available_agents = settings.SUBSCRIPTION_TIERS.get(tier, {}).get("agents", [])
    if agent_id not in available_agents:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your subscription tier does not include access to this agent"
        )
    
    # Get or create user agent
    user_agent = db.query(UserAgent).filter(
        UserAgent.user_id == user_id,
        UserAgent.agent_id == agent_id
    ).first()
    
    if not user_agent:
        user_agent = UserAgent(
            user_id=user_id,
            agent_id=agent_id,
            is_enabled=enabled
        )
        db.add(user_agent)
    else:
        user_agent.is_enabled = enabled
    
    db.commit()
    
    # Determine which tier this agent first appears in
    subscription_tier = "enterprise"
    for t_id, t_data in settings.SUBSCRIPTION_TIERS.items():
        if agent_id in t_data["agents"]:
            subscription_tier = t_id
            break
    
    return AgentInfo(
        id=agent_id,
        name=AGENT_MODULES.get(agent_id, {}).get("name", agent_id),
        description=AGENT_DESCRIPTIONS.get(agent_id, ""),
        subscription_tier=subscription_tier,
        enabled=enabled
    )

@router.get("/{agent_id}/usage")
async def get_agent_usage(
    agent_id: str,
    user_data: Dict[str, Any] = Depends(check_agent_access),
    db: Session = Depends(get_db)
):
    """
    Get usage statistics for an agent
    """
    user_id = user_data["user"].id
    user_agent = user_data["user_agent"]
    
    # Get usage records for this agent
    usage_records = db.query(AgentUsage).filter(
        AgentUsage.user_agent_id == user_agent.id
    ).order_by(AgentUsage.year.desc(), AgentUsage.month.desc()).all()
    
    return {
        "agent_id": agent_id,
        "total_requests": sum(u.request_count for u in usage_records),
        "total_tokens": sum(u.token_count for u in usage_records),
        "monthly_usage": [
            {
                "month": u.month,
                "year": u.year,
                "requests": u.request_count,
                "tokens": u.token_count
            } for u in usage_records
        ]
    }

# Function to track agent usage
async def track_agent_usage(
    user_agent_id: int,
    subscription_id: int,
    request_count: int = 1,
    token_count: int = 0,
    db: Session = None
):
    """
    Track usage of an agent
    """
    if not db:
        return
    
    # Get current month and year
    now = datetime.now()
    month = now.month
    year = now.year
    
    # Get or create usage record
    usage = db.query(AgentUsage).filter(
        AgentUsage.user_agent_id == user_agent_id,
        AgentUsage.subscription_id == subscription_id,
        AgentUsage.month == month,
        AgentUsage.year == year
    ).first()
    
    if not usage:
        usage = AgentUsage(
            user_agent_id=user_agent_id,
            subscription_id=subscription_id,
            month=month,
            year=year,
            request_count=0,
            token_count=0
        )
        db.add(usage)
    
    # Update usage counts
    usage.request_count += request_count
    usage.token_count += token_count
    usage.last_used = datetime.utcnow()
    
    db.commit() 