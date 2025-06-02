from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AgentWishlist
from pydantic import BaseModel

router = APIRouter(prefix="/api/wishlist", tags=["wishlist"])

class WishlistRequest(BaseModel):
    agent_id: int

@router.post("/add")
def add_to_wishlist(request: WishlistRequest, db: Session = Depends(get_db)):
    wishlist = AgentWishlist(user_id=1, agent_id=request.agent_id)  # TODO: Use current user
    db.add(wishlist)
    db.commit()
    db.refresh(wishlist)
    return wishlist

@router.post("/remove")
def remove_from_wishlist(request: WishlistRequest, db: Session = Depends(get_db)):
    wishlist = db.query(AgentWishlist).filter(AgentWishlist.user_id == 1, AgentWishlist.agent_id == request.agent_id).first()
    if wishlist:
        db.delete(wishlist)
        db.commit()
    return {"removed": True}

@router.get("/")
def list_wishlist(db: Session = Depends(get_db)):
    return db.query(AgentWishlist).filter(AgentWishlist.user_id == 1).all() 