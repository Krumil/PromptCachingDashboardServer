from fastapi import APIRouter
from ..services.blockchain import calculate_addresses_position
from ..models.request import AddressRequest
import json

router = APIRouter()

@router.get("/get_global_data")
async def get_total_score():
    with open("interacting_addresses.json", "r") as f:
        data = json.load(f)
    total_score = 0
    total_prime_cached = 0
    for info in data:
        address_data = info["data"]
        if "scores" in address_data:
            total_score += (
                address_data["scores"]["prime_score"]
                + address_data["scores"]["community_score"]
                + address_data["scores"]["initialization_score"]
            )
        if "base_scores" in address_data:
            total_score += (
                address_data["base_scores"]["prime_score"]
                + address_data["base_scores"]["community_score"]
                + address_data["base_scores"]["initialization_score"]
            )
        if "prime_amount_cached" in address_data:
            total_prime_cached += address_data["prime_amount_cached"]
        if "base_prime_amount_cached" in address_data:
            total_prime_cached += address_data["base_prime_amount_cached"]
    return {"total_score": total_score, "total_prime_cached": total_prime_cached}

@router.get("/addresses")
async def get_addresses():
    with open("interacting_addresses.json", "r") as f:
        return json.load(f)

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
            address_score = sum(address_data.get("scores", {}).values()) + sum(address_data.get("base_scores", {}).values())
            total_score += address_score
            total_combined_score += address_score
            total_prime_cached += address_data.get("prime_amount_cached", 0) + address_data.get("base_prime_amount_cached", 0)
            addresses_found.append(address_info)
    
    total_users = len(data) - len(request.addresses) + 1
    
    if addresses_found:
        position = calculate_addresses_position(request.addresses)
        print(f"Calculated position: {position}")
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
        return {"message": "No addresses found"}
