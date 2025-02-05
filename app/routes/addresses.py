from fastapi import APIRouter, Query, HTTPException
from ..services.blockchain import blockchain_service
from ..models.request import AddressRequest
import json
from typing import Optional
from .ens import ens_to_address  # Import the ENS lookup mapping

router = APIRouter()

@router.get("/get_global_data")
async def get_total_score():
    with open("interacting_addresses.json", "r") as f:
        data = json.load(f)
    total_score = 0
    total_prime_cached = 0
    for info in data:
        address_data = info["data"]
        if "merged_score_data" in address_data:
            scores = address_data["merged_score_data"]
            total_score += (
                scores["prime_score"]		
                + scores["community_score"]
                + scores["initialization_score"]
            )
        if "prime_amount_cached" in address_data:
            total_prime_cached += address_data["prime_amount_cached"]
        if "base_prime_amount_cached" in address_data:
            total_prime_cached += address_data["base_prime_amount_cached"]
    return {
        "total_score": total_score, 
        "total_prime_cached": total_prime_cached,
        "total_addresses": len(data)
    }

@router.get("/addresses")
async def get_addresses(
    page: Optional[int] = Query(default=1, ge=1, description="Page number"),
    page_size: Optional[int] = Query(default=10, ge=1, le=100, description="Number of items per page")
):
    with open("interacting_addresses.json", "r") as f:
        data = json.load(f)
    
    # Sort data by leaderboard_rank
    data.sort(key=lambda x: x.get("data", {}).get("leaderboard_rank", float('inf')))
    
    # Calculate pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    # Get paginated data
    paginated_data = data[start_idx:end_idx]
    
    return {
        "total": len(data),
        "page": page,
        "page_size": page_size,
        "total_pages": (len(data) + page_size - 1) // page_size,
        "data": paginated_data
    }

@router.post("/addresses")
async def get_address_info(request: AddressRequest):
    total_score = 0
    total_prime_cached = 0
    total_users = 0
    addresses_found = 0

    with open("interacting_addresses.json", "r") as f:
        data = json.load(f)
    
    addresses_found = []
    total_combined_score = 0
    for address in request.addresses:
        address_info = next((info for info in data if info["address"].lower() == address.lower()), None)
        
        if address_info:
            address_data = address_info["data"]
            if "merged_score_data" in address_data:
                scores = address_data["merged_score_data"]
                address_score = scores["prime_score"] + scores["community_score"] + scores["initialization_score"]
                total_score += address_score
                total_combined_score += address_score
            total_prime_cached += address_data.get("prime_amount_cached", 0) + address_data.get("base_prime_amount_cached", 0)
            addresses_found.append(address_info)
    
    total_users = len(data) - len(request.addresses) + 1
    
    if addresses_found:
        position = blockchain_service.calculate_addresses_position(request.addresses)
        return {
            "total_score": total_score,
            "total_prime_cached": total_prime_cached,
            "position": position,
            "total_users": total_users,
            "addresses_processed": len(request.addresses),
            "addresses_found": addresses_found,
            "addresses_not_found": len(request.addresses) - len(addresses_found)
        }
    else:
        print("No addresses found")
        return {"addresses_found": addresses_found}

@router.get("/search_position")
async def search_position(query: Optional[str] = Query(None, description="Ethereum address or ENS name")):
    # Validate query parameter
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    # Convert query to lowercase for case-insensitive matching
    query = query.lower()
    
    # If the query looks like an ENS name (contains .eth), try to resolve it
    search_address = query
    if '.eth' in query:
        if query in ens_to_address:
            search_address = ens_to_address[query]
        else:
            raise HTTPException(status_code=404, detail="ENS name not found")

    # Load and parse JSON data
    with open("interacting_addresses.json", "r") as f:
        data = json.load(f)
    
    # Sort data by leaderboard_rank
    data.sort(key=lambda x: x.get("data", {}).get("leaderboard_rank", float('inf')))
    
    # Find the searched address and its position
    searched_address_info = next(
        (item for item in data if item["address"].lower() == search_address.lower()),
        None
    )
    
    if not searched_address_info:
        raise HTTPException(status_code=404, detail="Address not found")
    
    searched_rank = searched_address_info["data"].get("leaderboard_rank")
    if searched_rank is None:
        raise HTTPException(status_code=404, detail="Address has no rank")
    
    # Calculate the next round number after the searched rank (round up to nearest 10)
    next_round_number = ((searched_rank + 9) // 10) * 10
    
    # Get all addresses up to the next round number
    context_addresses = []
    for item in data:
        rank = item["data"].get("leaderboard_rank")
        if rank is not None and rank <= next_round_number:
            context_addresses.append(item)
    
    return {
        "addresses": context_addresses,
        "position": searched_rank,
        "total_addresses": len(data),
        "queried_as": query,
        "resolved_address": search_address,
        "next_round_number": next_round_number
    }
