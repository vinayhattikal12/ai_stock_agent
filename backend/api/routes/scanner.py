from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.models.schemas import ScannerScanResponse, HistoricalScanSummary
from backend.models.database import get_db
from backend.services.quant.scanner import staged_scanner

router = APIRouter(prefix="/api/scanner", tags=["Scanner"])

@router.get("/scan", response_model=ScannerScanResponse)
async def run_market_scan():
    """
    Executes the multi-stage swing opportunity scan across the universe.
    Saves the result to the 15-day date-wise historical database.
    """
    return await staged_scanner.run_scan()

@router.get("/latest", response_model=ScannerScanResponse)
async def get_latest_scan(db: Session = Depends(get_db)):
    """
    Returns the most recent scan from the database.
    If the stored scan is from a previous date or empty, automatically executes a fresh live scan for today.
    """
    from datetime import date, datetime
    latest = staged_scanner.get_scan_by_date_or_latest("latest", db=db)
    today = date.today()
    if latest and latest.scan_timestamp:
        try:
            scan_dt = latest.scan_timestamp.date() if isinstance(latest.scan_timestamp, (date, datetime)) else datetime.fromisoformat(str(latest.scan_timestamp)).date()
            if scan_dt == today:
                return latest
        except Exception:
            pass
    return await staged_scanner.run_scan()

@router.get("/history", response_model=List[HistoricalScanSummary])
async def get_scan_history(db: Session = Depends(get_db)):
    """
    Returns summary list of available historical scan dates (maximum last 15 days).
    """
    return staged_scanner.get_history(db=db)

@router.get("/history/{date_or_id}", response_model=ScannerScanResponse)
async def get_scan_by_date(date_or_id: str, db: Session = Depends(get_db)):
    """
    Returns full scan result for a specific date (YYYY-MM-DD) or record ID.
    """
    res = staged_scanner.get_scan_by_date_or_latest(date_or_id, db=db)
    if not res:
        raise HTTPException(status_code=404, detail=f"No scan records found for '{date_or_id}'")
    return res

