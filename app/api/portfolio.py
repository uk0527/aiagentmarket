from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging
from datetime import datetime

from app.database import get_db
from app.auth import check_agent_access
from app.models import PortfolioRecord, AnalysisResult
from app.api.agents import get_agent_instance, track_agent_usage

logger = logging.getLogger(__name__)

router = APIRouter()

# Re-export models from portfolio_agent
from portfolio_agent import Position, PortfolioAnalysisRequest, PortfolioOptimizeRequest, RiskAnalysisRequest

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    positions: List[Dict[str, Any]]
    is_public: bool = False

class PortfolioResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    positions: List[Dict[str, Any]]
    created_at: str
    updated_at: str
    is_public: bool

class AnalysisResponse(BaseModel):
    id: Optional[int] = None
    user_id: int
    agent_id: str
    created_at: str
    result_type: str
    input_data: Optional[Dict[str, Any]] = None
    result_data: Dict[str, Any]
    is_saved: bool = False
    name: Optional[str] = None

@router.post("/", response_model=PortfolioResponse)
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    user_data: Dict[str, Any] = Depends(check_agent_access),
    db: Session = Depends(get_db)
):
    """
    Create a new portfolio
    """
    user_id = user_data["user"].id
    
    # Create portfolio record
    portfolio = PortfolioRecord(
        user_id=user_id,
        name=portfolio_data.name,
        description=portfolio_data.description,
        data={"positions": portfolio_data.positions},
        is_public=portfolio_data.is_public
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    
    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "description": portfolio.description,
        "positions": portfolio.data["positions"],
        "created_at": portfolio.created_at.isoformat(),
        "updated_at": portfolio.updated_at.isoformat(),
        "is_public": portfolio.is_public
    }

@router.get("/", response_model=List[PortfolioResponse])
async def list_portfolios(
    user_data: Dict[str, Any] = Depends(check_agent_access),
    db: Session = Depends(get_db)
):
    """
    List all portfolios for the current user
    """
    user_id = user_data["user"].id
    
    portfolios = db.query(PortfolioRecord).filter(
        PortfolioRecord.user_id == user_id
    ).order_by(PortfolioRecord.updated_at.desc()).all()
    
    return [
        {
            "id": portfolio.id,
            "name": portfolio.name,
            "description": portfolio.description,
            "positions": portfolio.data["positions"],
            "created_at": portfolio.created_at.isoformat(),
            "updated_at": portfolio.updated_at.isoformat(),
            "is_public": portfolio.is_public
        } for portfolio in portfolios
    ]

@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: int,
    user_data: Dict[str, Any] = Depends(check_agent_access),
    db: Session = Depends(get_db)
):
    """
    Get a portfolio by ID
    """
    user_id = user_data["user"].id
    
    portfolio = db.query(PortfolioRecord).filter(
        PortfolioRecord.id == portfolio_id,
        PortfolioRecord.user_id == user_id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "description": portfolio.description,
        "positions": portfolio.data["positions"],
        "created_at": portfolio.created_at.isoformat(),
        "updated_at": portfolio.updated_at.isoformat(),
        "is_public": portfolio.is_public
    }

@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: int,
    portfolio_data: PortfolioCreate,
    user_data: Dict[str, Any] = Depends(check_agent_access),
    db: Session = Depends(get_db)
):
    """
    Update a portfolio
    """
    user_id = user_data["user"].id
    
    portfolio = db.query(PortfolioRecord).filter(
        PortfolioRecord.id == portfolio_id,
        PortfolioRecord.user_id == user_id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Update portfolio
    portfolio.name = portfolio_data.name
    portfolio.description = portfolio_data.description
    portfolio.data = {"positions": portfolio_data.positions}
    portfolio.is_public = portfolio_data.is_public
    portfolio.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(portfolio)
    
    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "description": portfolio.description,
        "positions": portfolio.data["positions"],
        "created_at": portfolio.created_at.isoformat(),
        "updated_at": portfolio.updated_at.isoformat(),
        "is_public": portfolio.is_public
    }

@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: int,
    user_data: Dict[str, Any] = Depends(check_agent_access),
    db: Session = Depends(get_db)
):
    """
    Delete a portfolio
    """
    user_id = user_data["user"].id
    
    portfolio = db.query(PortfolioRecord).filter(
        PortfolioRecord.id == portfolio_id,
        PortfolioRecord.user_id == user_id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    db.delete(portfolio)
    db.commit()
    
    return None

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_portfolio(
    analysis_request: PortfolioAnalysisRequest,
    background_tasks: BackgroundTasks,
    user_data: Dict[str, Any] = Depends(check_agent_access),
    db: Session = Depends(get_db)
):
    """
    Analyze a portfolio
    """
    user_id = user_data["user"].id
    user_agent = user_data["user_agent"]
    subscription = user_data["subscription"]
    
    try:
        # Get portfolio agent instance
        agent = await get_agent_instance("portfolio_agent")
        
        # Convert positions to the expected format
        positions = []
        for pos in analysis_request.positions:
            positions.append(Position(
                symbol=pos.symbol,
                quantity=pos.quantity,
                cost_basis=pos.cost_basis,
                purchase_date=pos.purchase_date
            ))
        
        # Call the agent
        result = await agent.analyze_portfolio(
            positions=positions,
            benchmark=analysis_request.benchmark,
            risk_tolerance=analysis_request.risk_tolerance
        )
        
        # Generate insights
        insights = await agent.generate_insights(result)
        result["insights"] = insights
        
        # Store analysis result
        analysis = AnalysisResult(
            user_id=user_id,
            agent_id="portfolio_agent",
            result_type="portfolio_analysis",
            input_data=analysis_request.dict(),
            result_data=result,
            is_saved=False
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        # Track usage
        background_tasks.add_task(
            track_agent_usage,
            user_agent_id=user_agent.id,
            subscription_id=subscription.id if subscription else None,
            request_count=1,
            token_count=len(str(result)) // 4,  # Rough estimate of token count
            db=db
        )
        
        return {
            "id": analysis.id,
            "user_id": analysis.user_id,
            "agent_id": analysis.agent_id,
            "created_at": analysis.created_at.isoformat(),
            "result_type": analysis.result_type,
            "input_data": analysis.input_data,
            "result_data": analysis.result_data,
            "is_saved": analysis.is_saved,
            "name": analysis.name
        }
    except Exception as e:
        logger.error(f"Error analyzing portfolio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze portfolio: {str(e)}"
        )

@router.post("/optimize", response_model=AnalysisResponse)
async def optimize_portfolio(
    optimize_request: PortfolioOptimizeRequest,
    background_tasks: BackgroundTasks,
    user_data: Dict[str, Any] = Depends(check_agent_access),
    db: Session = Depends(get_db)
):
    """
    Optimize a portfolio
    """
    user_id = user_data["user"].id
    user_agent = user_data["user_agent"]
    subscription = user_data["subscription"]
    
    try:
        # Get portfolio agent instance
        agent = await get_agent_instance("portfolio_agent")
        
        # Convert positions to the expected format
        positions = []
        for pos in optimize_request.positions:
            positions.append(Position(
                symbol=pos.symbol,
                quantity=pos.quantity,
                cost_basis=pos.cost_basis,
                purchase_date=pos.purchase_date
            ))
        
        # Call the agent
        result = await agent.optimize_portfolio(
            positions=positions,
            risk_tolerance=optimize_request.risk_tolerance,
            investment_horizon=optimize_request.investment_horizon,
            additional_capital=optimize_request.additional_capital,
            constraints=optimize_request.constraints
        )
        
        # Store analysis result
        analysis = AnalysisResult(
            user_id=user_id,
            agent_id="portfolio_agent",
            result_type="portfolio_optimization",
            input_data=optimize_request.dict(),
            result_data=result,
            is_saved=False
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        # Track usage
        background_tasks.add_task(
            track_agent_usage,
            user_agent_id=user_agent.id,
            subscription_id=subscription.id if subscription else None,
            request_count=1,
            token_count=len(str(result)) // 4,  # Rough estimate of token count
            db=db
        )
        
        return {
            "id": analysis.id,
            "user_id": analysis.user_id,
            "agent_id": analysis.agent_id,
            "created_at": analysis.created_at.isoformat(),
            "result_type": analysis.result_type,
            "input_data": analysis.input_data,
            "result_data": analysis.result_data,
            "is_saved": analysis.is_saved,
            "name": analysis.name
        }
    except Exception as e:
        logger.error(f"Error optimizing portfolio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize portfolio: {str(e)}"
        )

@router.post("/risk", response_model=AnalysisResponse)
async def analyze_risk(
    risk_request: RiskAnalysisRequest,
    background_tasks: BackgroundTasks,
    user_data: Dict[str, Any] = Depends(check_agent_access),
    db: Session = Depends(get_db)
):
    """
    Analyze portfolio risk
    """
    user_id = user_data["user"].id
    user_agent = user_data["user_agent"]
    subscription = user_data["subscription"]
    
    try:
        # Get portfolio agent instance
        agent = await get_agent_instance("portfolio_agent")
        
        # Convert positions to the expected format
        positions = []
        for pos in risk_request.positions:
            positions.append(Position(
                symbol=pos.symbol,
                quantity=pos.quantity,
                cost_basis=pos.cost_basis,
                purchase_date=pos.purchase_date
            ))
        
        # Call the agent
        result = await agent.analyze_risk(
            positions=positions,
            var_confidence=risk_request.var_confidence,
            stress_test=risk_request.stress_test
        )
        
        # Store analysis result
        analysis = AnalysisResult(
            user_id=user_id,
            agent_id="portfolio_agent",
            result_type="risk_analysis",
            input_data=risk_request.dict(),
            result_data=result,
            is_saved=False
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        # Track usage
        background_tasks.add_task(
            track_agent_usage,
            user_agent_id=user_agent.id,
            subscription_id=subscription.id if subscription else None,
            request_count=1,
            token_count=len(str(result)) // 4,  # Rough estimate of token count
            db=db
        )
        
        return {
            "id": analysis.id,
            "user_id": analysis.user_id,
            "agent_id": analysis.agent_id,
            "created_at": analysis.created_at.isoformat(),
            "result_type": analysis.result_type,
            "input_data": analysis.input_data,
            "result_data": analysis.result_data,
            "is_saved": analysis.is_saved,
            "name": analysis.name
        }
    except Exception as e:
        logger.error(f"Error analyzing portfolio risk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze portfolio risk: {str(e)}"
        )

@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: int,
    user_data: Dict[str, Any] = Depends(check_agent_access),
    db: Session = Depends(get_db)
):
    """
    Get an analysis result by ID
    """
    user_id = user_data["user"].id
    
    analysis = db.query(AnalysisResult).filter(
        AnalysisResult.id == analysis_id,
        AnalysisResult.user_id == user_id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    return {
        "id": analysis.id,
        "user_id": analysis.user_id,
        "agent_id": analysis.agent_id,
        "created_at": analysis.created_at.isoformat(),
        "result_type": analysis.result_type,
        "input_data": analysis.input_data,
        "result_data": analysis.result_data,
        "is_saved": analysis.is_saved,
        "name": analysis.name
    }

@router.get("/analysis", response_model=List[AnalysisResponse])
async def list_analyses(
    user_data: Dict[str, Any] = Depends(check_agent_access),
    db: Session = Depends(get_db),
    limit: int = 10,
    offset: int = 0,
    agent_id: Optional[str] = None,
    result_type: Optional[str] = None
):
    """
    List analysis results for the current user
    """
    user_id = user_data["user"].id
    
    query = db.query(AnalysisResult).filter(AnalysisResult.user_id == user_id)
    
    if agent_id:
        query = query.filter(AnalysisResult.agent_id == agent_id)
    
    if result_type:
        query = query.filter(AnalysisResult.result_type == result_type)
    
    analyses = query.order_by(AnalysisResult.created_at.desc()).offset(offset).limit(limit).all()
    
    return [
        {
            "id": analysis.id,
            "user_id": analysis.user_id,
            "agent_id": analysis.agent_id,
            "created_at": analysis.created_at.isoformat(),
            "result_type": analysis.result_type,
            "input_data": analysis.input_data,
            "result_data": analysis.result_data,
            "is_saved": analysis.is_saved,
            "name": analysis.name
        } for analysis in analyses
    ] 