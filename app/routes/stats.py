from fastapi import APIRouter, HTTPException
from app.services.dune import dune_service
from app.services.stats import CacheStats

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