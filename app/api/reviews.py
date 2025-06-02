from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AgentReview
from pydantic import BaseModel

router = APIRouter(prefix="/api/reviews", tags=["reviews"])

class ReviewRequest(BaseModel):
    agent_id: int
    purchase_id: int
    rating: int
    title: str = None
    content: str = None

@router.post("/")
def create_review(request: ReviewRequest, db: Session = Depends(get_db)):
    review = AgentReview(
        agent_id=request.agent_id,
        purchase_id=request.purchase_id,
        rating=request.rating,
        title=request.title,
        content=request.content,
        reviewer_id=1  # TODO: Use current user
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review

@router.get("/by-agent/{agent_id}")
def list_reviews_by_agent(agent_id: int, db: Session = Depends(get_db)):
    return db.query(AgentReview).filter(AgentReview.agent_id == agent_id).all() 