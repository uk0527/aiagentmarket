from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging

from app.database import get_db
from app.auth import get_current_active_user, get_subscription_user
from app.stripe import (
    create_stripe_customer,
    create_subscription,
    cancel_subscription,
    get_subscription_details,
    get_stripe_publishable_key,
    get_subscription_plans
)
from app.models import User, Subscription, SubscriptionTier

logger = logging.getLogger(__name__)

router = APIRouter()

class PaymentMethodCreate(BaseModel):
    payment_method_id: str

class SubscriptionCreate(BaseModel):
    payment_method_id: str
    price_id: str

class SubscriptionResponse(BaseModel):
    id: Optional[int] = None
    tier: str
    is_active: bool
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    auto_renew: Optional[bool] = None
    stripe_subscription_id: Optional[str] = None
    client_secret: Optional[str] = None

class SubscriptionPlan(BaseModel):
    id: str
    name: str
    price: float
    features: List[str]
    agents: List[str]
    price_id: Optional[str] = None

@router.get("/plans", response_model=List[SubscriptionPlan])
async def get_plans():
    """
    Get all available subscription plans
    """
    return await get_subscription_plans()

@router.get("/config")
async def get_subscription_config():
    """
    Get subscription configuration for client-side use
    """
    return {
        "publishable_key": await get_stripe_publishable_key()
    }

@router.get("/my", response_model=SubscriptionResponse)
async def get_my_subscription(user_data: Dict[str, Any] = Depends(get_subscription_user)):
    """
    Get current user's subscription
    """
    subscription = user_data["subscription"]
    
    if not subscription:
        # Return basic subscription details
        return {
            "tier": SubscriptionTier.BASIC.value,
            "is_active": True,
            "auto_renew": False
        }
    
    return {
        "id": subscription.id,
        "tier": subscription.tier,
        "is_active": subscription.is_active,
        "started_at": subscription.started_at.isoformat() if subscription.started_at else None,
        "ended_at": subscription.ended_at.isoformat() if subscription.ended_at else None,
        "auto_renew": subscription.auto_renew,
        "stripe_subscription_id": subscription.stripe_subscription_id
    }

@router.post("/create", response_model=SubscriptionResponse)
async def create_new_subscription(
    subscription_data: SubscriptionCreate,
    user_data: Dict[str, Any] = Depends(get_subscription_user),
    db: Session = Depends(get_db)
):
    """
    Create a new subscription for the current user
    """
    user = user_data["user"]
    current_subscription = user_data["subscription"]
    
    # Check if user already has an active paid subscription
    if current_subscription and current_subscription.is_active and current_subscription.tier != SubscriptionTier.BASIC.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active subscription. Cancel the current subscription first."
        )
    
    try:
        # Create or get Stripe customer
        if current_subscription and current_subscription.stripe_customer_id:
            customer_id = current_subscription.stripe_customer_id
        else:
            customer = await create_stripe_customer(user, subscription_data.payment_method_id)
            customer_id = customer["customer_id"]
        
        # Create subscription in Stripe
        stripe_subscription = await create_subscription(
            customer_id,
            subscription_data.price_id,
            subscription_data.payment_method_id
        )
        
        # Determine subscription tier from price ID
        tier = SubscriptionTier.PROFESSIONAL.value  # Default
        for tier_id, tier_data in settings.SUBSCRIPTION_TIERS.items():
            if tier_data.get("price_id") == subscription_data.price_id:
                tier = tier_id
                break
        
        # Create or update subscription in database
        if current_subscription:
            # Update existing subscription
            current_subscription.tier = tier
            current_subscription.stripe_subscription_id = stripe_subscription["subscription_id"]
            current_subscription.is_active = stripe_subscription["status"] in ["active", "trialing"]
            current_subscription.auto_renew = True
            current_subscription.stripe_customer_id = customer_id
            current_subscription.ended_at = None
            db_subscription = current_subscription
        else:
            # Create new subscription
            db_subscription = Subscription(
                user_id=user.id,
                tier=tier,
                stripe_customer_id=customer_id,
                stripe_subscription_id=stripe_subscription["subscription_id"],
                is_active=stripe_subscription["status"] in ["active", "trialing"],
                auto_renew=True
            )
            db.add(db_subscription)
        
        db.commit()
        db.refresh(db_subscription)
        
        # Enable agents for the new tier
        available_agents = settings.SUBSCRIPTION_TIERS.get(tier, {}).get("agents", [])
        for agent_id in available_agents:
            # Check if user has this agent
            user_agent = db.query(UserAgent).filter(
                UserAgent.user_id == user.id,
                UserAgent.agent_id == agent_id
            ).first()
            
            if not user_agent:
                # Create user agent
                user_agent = UserAgent(
                    user_id=user.id,
                    agent_id=agent_id,
                    is_enabled=True
                )
                db.add(user_agent)
        
        db.commit()
        
        return {
            "id": db_subscription.id,
            "tier": db_subscription.tier,
            "is_active": db_subscription.is_active,
            "started_at": db_subscription.started_at.isoformat() if db_subscription.started_at else None,
            "ended_at": db_subscription.ended_at.isoformat() if db_subscription.ended_at else None,
            "auto_renew": db_subscription.auto_renew,
            "stripe_subscription_id": db_subscription.stripe_subscription_id,
            "client_secret": stripe_subscription.get("client_secret")
        }
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subscription: {str(e)}"
        )

@router.post("/cancel", response_model=SubscriptionResponse)
async def cancel_current_subscription(
    user_data: Dict[str, Any] = Depends(get_subscription_user),
    db: Session = Depends(get_db)
):
    """
    Cancel the current user's subscription
    """
    subscription = user_data["subscription"]
    
    if not subscription or subscription.tier == SubscriptionTier.BASIC.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active paid subscription to cancel"
        )
    
    try:
        # Cancel subscription in Stripe
        if subscription.stripe_subscription_id:
            await cancel_subscription(subscription.stripe_subscription_id)
        
        # Update subscription in database
        subscription.auto_renew = False
        db.commit()
        
        # Create a new basic subscription (will be activated once current one expires)
        basic_subscription = Subscription(
            user_id=user_data["user"].id,
            tier=SubscriptionTier.BASIC.value,
            is_active=False,  # Will be activated when current one expires
            auto_renew=False
        )
        db.add(basic_subscription)
        db.commit()
        
        # Get updated subscription details
        db.refresh(subscription)
        
        return {
            "id": subscription.id,
            "tier": subscription.tier,
            "is_active": subscription.is_active,
            "started_at": subscription.started_at.isoformat() if subscription.started_at else None,
            "ended_at": subscription.ended_at.isoformat() if subscription.ended_at else None,
            "auto_renew": subscription.auto_renew,
            "stripe_subscription_id": subscription.stripe_subscription_id
        }
    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel subscription: {str(e)}"
        ) 