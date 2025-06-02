from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AgentListing
from pydantic import BaseModel

router = APIRouter(prefix="/api/seller", tags=["seller"])

class AgentUpdateRequest(BaseModel):
    name: str = None
    short_description: str = None
    category: str = None

@router.get("/my-agents")
def list_my_agents(db: Session = Depends(get_db)):
    return db.query(AgentListing).filter(AgentListing.seller_id == 1).all()  # TODO: Use current user

@router.put("/agent/{agent_id}")
def update_agent(agent_id: int, request: AgentUpdateRequest, db: Session = Depends(get_db)):
    agent = db.query(AgentListing).filter(AgentListing.id == agent_id, AgentListing.seller_id == 1).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if request.name:
        agent.name = request.name
    if request.short_description:
        agent.short_description = request.short_description
    if request.category:
        agent.category = request.category
    db.commit()
    db.refresh(agent)
    return agent

@router.delete("/agent/{agent_id}")
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(AgentListing).filter(AgentListing.id == agent_id, AgentListing.seller_id == 1).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    db.delete(agent)
    db.commit()
    return {"deleted": True} 