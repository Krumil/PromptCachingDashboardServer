from fastapi import APIRouter, HTTPException
from app.services.dune import dune_service
from app.services.stats import CacheStats
from app.services.blockchain import BlockchainService
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union
import json

router = APIRouter()

@router.get("/stats", response_model=CacheStats)
async def get_cache_stats():
    """
    Get comprehensive statistics about PRIME caching activity.
    Returns various metrics including total cached, withdrawals, unique cachers, and time-based stats.
    """
    try:
        stats = await dune_service.get_cache_stats()
        if stats is None:
            raise HTTPException(status_code=404, detail="No caching statistics available")
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PercentageVerificationResult(BaseModel):
    is_valid: bool
    total_percentage: float
    difference: float
    tolerance: float

@router.get("/verify-percentages", response_model=PercentageVerificationResult)
async def verify_percentages(tolerance: float = 0.01):
    """
    Verify that the sum of all percentages in the addresses data equals 100% (within tolerance).
    Returns whether the sum is valid, the actual sum, and the difference from 100%.
    
    Parameters:
    - tolerance: Acceptable deviation from 100% (default: 0.01 which is 0.01%)
    """
    try:
        # Get the blockchain service instance
        blockchain_service = BlockchainService()
        
        # Load addresses data from the JSON file
        with open("interacting_addresses.json", "r") as f:
            addresses_data = json.load(f)
        
        # Verify the percentages
        is_valid, total_percentage, difference = blockchain_service.verify_percentages_sum(
            addresses_data, tolerance
        )
        
        return {
            "is_valid": is_valid,
            "total_percentage": total_percentage,
            "difference": difference,
            "tolerance": tolerance
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 