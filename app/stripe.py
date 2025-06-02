import stripe
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.config import settings
from app.models import User, Subscription, SubscriptionTier
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe with API key
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY
else:
    logger.warning("Stripe API key not set. Stripe functionality will not work.")

async def create_stripe_customer(user: User, payment_method_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a Stripe customer for a user
    """
    try:
        customer_data = {
            "email": user.email,
            "name": f"{user.first_name or ''} {user.last_name or ''}".strip() or None,
            "metadata": {
                "user_id": str(user.id)
            }
        }
        
        if payment_method_id:
            customer_data["payment_method"] = payment_method_id
        
        customer = stripe.Customer.create(**customer_data)
        
        return {
            "customer_id": customer.id,
            "email": customer.email,
            "name": customer.name
        }
    except Exception as e:
        logger.error(f"Error creating Stripe customer: {str(e)}")
        raise

async def create_subscription(
    customer_id: str, 
    price_id: str,
    payment_method_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a Stripe subscription
    """
    try:
        # Attach payment method to customer if provided
        if payment_method_id:
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
            # Set as default payment method
            stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    "default_payment_method": payment_method_id
                }
            )
        
        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            expand=["latest_invoice.payment_intent"],
            payment_behavior="default_incomplete",
            payment_settings={"save_default_payment_method": "on_subscription"},
            metadata={"price_id": price_id}
        )
        
        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
            "customer_id": customer_id,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret if hasattr(subscription, 'latest_invoice') and subscription.latest_invoice else None,
        }
    except Exception as e:
        logger.error(f"Error creating Stripe subscription: {str(e)}")
        raise

async def cancel_subscription(subscription_id: str) -> Dict[str, Any]:
    """
    Cancel a Stripe subscription
    """
    try:
        subscription = stripe.Subscription.delete(subscription_id)
        
        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "canceled_at": datetime.fromtimestamp(subscription.canceled_at) if subscription.canceled_at else None
        }
    except Exception as e:
        logger.error(f"Error canceling Stripe subscription: {str(e)}")
        raise

async def get_subscription_details(subscription_id: str) -> Dict[str, Any]:
    """
    Get details of a Stripe subscription
    """
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
            "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "customer_id": subscription.customer,
            "price_id": subscription.items.data[0].price.id if subscription.items.data else None,
            "amount": subscription.items.data[0].price.unit_amount / 100 if subscription.items.data and subscription.items.data[0].price.unit_amount else 0,
            "currency": subscription.items.data[0].price.currency if subscription.items.data else None
        }
    except Exception as e:
        logger.error(f"Error getting Stripe subscription details: {str(e)}")
        raise

async def update_subscription_in_db(db: Session, subscription_id: str) -> Optional[Subscription]:
    """
    Update subscription details in database from Stripe
    """
    try:
        # Find subscription in DB
        db_subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()
        
        if not db_subscription:
            logger.error(f"Subscription {subscription_id} not found in database")
            return None
        
        # Get subscription details from Stripe
        subscription_details = await get_subscription_details(subscription_id)
        
        # Update subscription in DB
        db_subscription.is_active = subscription_details["status"] in ["active", "trialing"]
        db_subscription.ended_at = subscription_details["current_period_end"] if subscription_details["cancel_at_period_end"] else None
        
        db.commit()
        return db_subscription
    except Exception as e:
        logger.error(f"Error updating subscription in database: {str(e)}")
        db.rollback()
        return None

async def process_stripe_webhook(event_data: Dict[str, Any], db: Session) -> bool:
    """
    Process a Stripe webhook event
    """
    try:
        event_type = event_data.get("type")
        
        if event_type == "customer.subscription.created":
            # New subscription created
            subscription = event_data.get("data", {}).get("object", {})
            customer_id = subscription.get("customer")
            subscription_id = subscription.get("id")
            
            # Find user by customer ID
            db_subscription = db.query(Subscription).filter(
                Subscription.stripe_customer_id == customer_id
            ).first()
            
            if db_subscription:
                # Update subscription details
                db_subscription.stripe_subscription_id = subscription_id
                db_subscription.is_active = subscription.get("status") in ["active", "trialing"]
                db_subscription.started_at = datetime.fromtimestamp(subscription.get("start_date"))
                db_subscription.ended_at = None
                
                # Determine tier from price ID
                items = subscription.get("items", {}).get("data", [])
                if items:
                    price_id = items[0].get("price", {}).get("id")
                    # Map price ID to tier
                    for tier, tier_data in settings.SUBSCRIPTION_TIERS.items():
                        if tier_data.get("price_id") == price_id:
                            db_subscription.tier = tier
                            break
                
                db.commit()
                return True
        
        elif event_type == "customer.subscription.updated":
            # Subscription updated
            subscription = event_data.get("data", {}).get("object", {})
            subscription_id = subscription.get("id")
            
            # Find subscription by ID
            db_subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_id
            ).first()
            
            if db_subscription:
                # Update subscription details
                db_subscription.is_active = subscription.get("status") in ["active", "trialing"]
                
                # Check if canceled
                if subscription.get("cancel_at_period_end"):
                    db_subscription.auto_renew = False
                    db_subscription.ended_at = datetime.fromtimestamp(subscription.get("current_period_end"))
                else:
                    db_subscription.auto_renew = True
                    db_subscription.ended_at = None
                
                db.commit()
                return True
        
        elif event_type == "customer.subscription.deleted":
            # Subscription canceled
            subscription = event_data.get("data", {}).get("object", {})
            subscription_id = subscription.get("id")
            
            # Find subscription by ID
            db_subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_id
            ).first()
            
            if db_subscription:
                # Mark subscription as inactive and set end date
                db_subscription.is_active = False
                db_subscription.auto_renew = False
                db_subscription.ended_at = datetime.fromtimestamp(subscription.get("canceled_at") or subscription.get("current_period_end"))
                
                # Create new basic subscription
                user_id = db_subscription.user_id
                new_subscription = Subscription(
                    user_id=user_id,
                    tier=SubscriptionTier.BASIC.value,
                    is_active=True,
                    auto_renew=False
                )
                db.add(new_subscription)
                
                db.commit()
                return True
        
        # Other events not handled
        return True
    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {str(e)}")
        db.rollback()
        return False

async def get_stripe_publishable_key() -> str:
    """
    Get Stripe publishable key for client-side usage
    """
    return settings.STRIPE_PUBLISHABLE_KEY

async def get_subscription_plans() -> List[Dict[str, Any]]:
    """
    Get subscription plan details from settings
    """
    plans = []
    for tier_id, tier_data in settings.SUBSCRIPTION_TIERS.items():
        plans.append({
            "id": tier_id,
            "name": tier_data["name"],
            "price": tier_data["monthly_price"],
            "features": tier_data["features"],
            "agents": tier_data["agents"],
            "price_id": tier_data["price_id"]
        })
    
    return sorted(plans, key=lambda x: x["price"]) 