import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.models.database import get_db, DBHolding
from backend.models.schemas import PortfolioSummaryResponse, HoldingCreate, HoldingUpdate, HoldingAnalysis
from backend.services.portfolio.portfolio_engine import portfolio_engine

logger = logging.getLogger("portfolio_routes")

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio Intelligence"])

@router.get("", response_model=PortfolioSummaryResponse)
async def get_portfolio(db: Session = Depends(get_db)):
    """
    Returns complete portfolio overview, P&L, holdings analysis, and thesis statuses.
    """
    try:
        return await portfolio_engine.get_portfolio_summary(db)
    except Exception as e:
        logger.exception(f"Error getting portfolio: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load portfolio metrics: {str(e)}")

@router.post("/holdings", response_model=HoldingAnalysis)
async def add_holding(payload: HoldingCreate, db: Session = Depends(get_db)):
    """
    Adds a new stock holding to monitor.
    """
    try:
        clean_symbol = payload.symbol.upper().strip()
        if not clean_symbol:
            raise HTTPException(status_code=400, detail="Stock symbol cannot be empty")
            
        db_holding = DBHolding(
            symbol=clean_symbol,
            quantity=int(payload.quantity),
            buy_price=float(payload.buy_price),
            purchase_date=payload.purchase_date,
            notes=payload.notes
        )
        db.add(db_holding)
        db.commit()
        db.refresh(db_holding)
        return await portfolio_engine.analyze_holding(db_holding)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Error adding holding for {payload.symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add holding: {str(e)}")

@router.put("/holdings/{holding_id}", response_model=HoldingAnalysis)
async def update_holding(holding_id: int, payload: HoldingUpdate, db: Session = Depends(get_db)):
    """
    Updates holding details (quantity, price, date, notes).
    """
    try:
        db_holding = db.query(DBHolding).filter(DBHolding.id == holding_id).first()
        if not db_holding:
            raise HTTPException(status_code=404, detail="Holding not found")
            
        if payload.quantity is not None:
            db_holding.quantity = int(payload.quantity)
        if payload.buy_price is not None:
            db_holding.buy_price = float(payload.buy_price)
        if payload.purchase_date is not None:
            db_holding.purchase_date = payload.purchase_date
        if payload.notes is not None:
            db_holding.notes = payload.notes
            
        db.commit()
        db.refresh(db_holding)
        return await portfolio_engine.analyze_holding(db_holding)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Error updating holding {holding_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update holding: {str(e)}")

@router.delete("/holdings/{holding_id}")
async def delete_holding(holding_id: int, db: Session = Depends(get_db)):
    """
    Removes a holding from the tracking portfolio.
    """
    try:
        db_holding = db.query(DBHolding).filter(DBHolding.id == holding_id).first()
        if not db_holding:
            raise HTTPException(status_code=404, detail="Holding not found")
            
        sym = db_holding.symbol
        db.delete(db_holding)
        db.commit()
        return {"status": "success", "message": f"Holding {sym} removed"}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Error deleting holding {holding_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete holding: {str(e)}")
