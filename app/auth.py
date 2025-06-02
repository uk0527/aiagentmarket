from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models import User, Subscription, SubscriptionTier, UserAgent
import logging
import secrets
import string

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that a plain password matches a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password for storage"""
    return pwd_context.hash(password)

def generate_api_key() -> str:
    """Generate a secure API key"""
    # 32 characters from letters, digits, and safe special chars
    alphabet = string.ascii_letters + string.digits + "-_"
    return ''.join(secrets.choice(alphabet) for _ in range(32))

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email"""
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password"""
    user = get_user_by_email(db, email)
    if not user or not user.hashed_password:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_user(db: Session, email: str, password: Optional[str] = None, 
                first_name: Optional[str] = None, last_name: Optional[str] = None,
                google_id: Optional[str] = None) -> User:
    """Create a new user"""
    # Check if user already exists
    existing_user = get_user_by_email(db, email)
    if existing_user:
        if google_id and not existing_user.google_id:
            # Update existing user with Google ID
            existing_user.google_id = google_id
            existing_user.last_login = datetime.utcnow()
            db.commit()
            return existing_user
        return existing_user
    
    # Create new user
    hashed_password = get_password_hash(password) if password else None
    user = User(
        email=email,
        hashed_password=hashed_password,
        google_id=google_id,
        first_name=first_name,
        last_name=last_name,
        last_login=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create basic subscription
    create_subscription(db, user.id, SubscriptionTier.BASIC.value)
    
    # Enable basic agents
    for agent_id in settings.SUBSCRIPTION_TIERS["basic"]["agents"]:
        user_agent = UserAgent(
            user_id=user.id,
            agent_id=agent_id,
            is_enabled=True
        )
        db.add(user_agent)
    
    db.commit()
    return user

def create_subscription(db: Session, user_id: int, tier: str = SubscriptionTier.BASIC.value, 
                        stripe_customer_id: Optional[str] = None, 
                        stripe_subscription_id: Optional[str] = None) -> Subscription:
    """Create a new subscription for a user"""
    subscription = Subscription(
        user_id=user_id,
        tier=tier,
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=stripe_subscription_id,
        is_active=True if tier == SubscriptionTier.BASIC.value else False,
        auto_renew=False if tier == SubscriptionTier.BASIC.value else True
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Get the current user from a JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Check that the current user is active"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_subscription_user(current_user: User = Depends(get_current_active_user), 
                              db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get user with active subscription information"""
    # Get active subscription
    subscription = db.query(Subscription)\
        .filter(Subscription.user_id == current_user.id, Subscription.is_active == True)\
        .order_by(Subscription.id.desc())\
        .first()
    
    return {
        "user": current_user,
        "subscription": subscription,
        "tier": subscription.tier if subscription else SubscriptionTier.BASIC.value
    }

async def check_agent_access(user_data: Dict[str, Any] = Depends(get_subscription_user), 
                           agent_id: str = None, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Check if the user has access to a specific agent"""
    if not agent_id:
        raise HTTPException(status_code=400, detail="Agent ID not specified")
    
    # Get user's subscription tier
    tier = user_data["tier"]
    user_id = user_data["user"].id
    
    # Check if agent is available in tier
    available_agents = settings.SUBSCRIPTION_TIERS.get(tier, {}).get("agents", [])
    if agent_id not in available_agents:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your subscription tier does not include access to this agent. Please upgrade to access {agent_id}."
        )
    
    # Check if user has agent enabled
    user_agent = db.query(UserAgent)\
        .filter(UserAgent.user_id == user_id, UserAgent.agent_id == agent_id)\
        .first()
    
    if not user_agent:
        # Create user agent if it doesn't exist
        user_agent = UserAgent(
            user_id=user_id,
            agent_id=agent_id,
            is_enabled=True
        )
        db.add(user_agent)
        db.commit()
        db.refresh(user_agent)
    elif not user_agent.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This agent is disabled for your account. Please enable it in your settings."
        )
    
    # All checks passed
    return {
        "user": user_data["user"],
        "subscription": user_data["subscription"],
        "tier": tier,
        "user_agent": user_agent
    }

# Admin-only dependency
async def get_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Check that the current user is an admin"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user 