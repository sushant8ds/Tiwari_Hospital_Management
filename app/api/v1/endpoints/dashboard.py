"""
Dashboard statistics endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from decimal import Decimal

from app.core.database import get_db
from app.crud.ipd import bed_crud
from app.crud.payment import payment_crud
from app.crud.visit import visit_crud

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard statistics (Public endpoint)
    
    Returns:
    - today_opd_count: Number of OPD visits today
    - ipd_count: Number of active IPD patients
    - available_beds: Number of available beds
    - today_collection: Total collection for today
    """
    try:
        # Get today's date
        today = date.today()
        
        # Get today's OPD count
        daily_visits = await visit_crud.get_daily_visits(db, today)
        today_opd_count = len(daily_visits)
        
        # Get bed occupancy stats
        bed_stats = await bed_crud.get_bed_occupancy_stats(db)
        
        # Get today's collection
        today_collection = await payment_crud.get_daily_collection(db, datetime.now())
        
        return {
            "today_opd_count": today_opd_count,
            "ipd_count": bed_stats.get("occupied", 0),
            "available_beds": bed_stats.get("available", 0),
            "today_collection": float(today_collection)
        }
        
    except Exception as e:
        # Return zeros if there's an error
        return {
            "today_opd_count": 0,
            "ipd_count": 0,
            "available_beds": 0,
            "today_collection": 0.0
        }
