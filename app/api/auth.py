from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr, Field
import logging
import json
from passlib.context import CryptContext

from app.database import get_db
from app.models import User, Subscription
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = "demo-token"  # TODO: Implement proper JWT
    return encoded_jwt

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    # TODO: Implement proper JWT token validation
    # For now, just get the first user as a demo
    user = db.query(User).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_subscription_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.is_active == True
    ).order_by(Subscription.id.desc()).first()
    
    return {
        "user": current_user,
        "subscription": subscription
    }

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    subscription: Dict[str, Any]

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str = None
    last_name: str = None

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # Get subscription info
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.is_active == True
    ).order_by(Subscription.id.desc()).first()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "subscription": {
                "tier": subscription.tier if subscription else "basic",
                "is_active": subscription.is_active if subscription else True,
                "expires": subscription.ended_at.isoformat() if subscription and subscription.ended_at else None
            }
        }
    }

@router.post("/signup")
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(request.password)
    new_user = User(
        email=request.email,
        hashed_password=hashed_password,
        first_name=request.first_name,
        last_name=request.last_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(user_data: Dict[str, Any] = Depends(get_subscription_user)):
    user = user_data["user"]
    subscription = user_data["subscription"]
    
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "subscription": {
            "tier": subscription.tier if subscription else "basic",
            "is_active": subscription.is_active if subscription else True,
            "expires": subscription.ended_at.isoformat() if subscription and subscription.ended_at else None
        }
    }

@router.post("/password/reset", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    reset_data: PasswordReset, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Find user by email
    user = db.query(User).filter(User.email == reset_data.email).first()
    if not user:
        # Return success even if user doesn't exist to prevent email enumeration
        return {"message": "If your email is registered, you will receive a password reset link"}
    
    # TODO: Implement actual password reset email sending
    # For now, just log it
    logger.info(f"Password reset requested for user: {user.email}")
    
    return {"message": "If your email is registered, you will receive a password reset link"}

@router.post("/password/change", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"} 