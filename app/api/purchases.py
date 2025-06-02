from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AgentPurchase
from pydantic import BaseModel

router = APIRouter(prefix="/api/purchases", tags=["purchases"])

class PurchaseRequest(BaseModel):
    agent_id: int
    pricing_tier_id: int = None
    amount: float
    currency: str = "USD"

@router.post("/")
def purchase_agent(request: PurchaseRequest, db: Session = Depends(get_db)):
    purchase = AgentPurchase(
        agent_id=request.agent_id,
        pricing_tier_id=request.pricing_tier_id,
        amount=request.amount,
        currency=request.currency,
        transaction_id="demo-txid"
    )
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase

@router.get("/")
def list_purchases(db: Session = Depends(get_db)):
    return db.query(AgentPurchase).all() 