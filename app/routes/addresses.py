from fastapi import APIRouter
from ..services.blockchain import calculate_address_position
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
    position = calculate_address_position(request.address)
    address = request.address
    with open("interacting_addresses.json", "r") as f:
        data = json.load(f)
    for info in data:
        if info["address"].lower() == address.lower():
            address_data = info["data"]
            total_score = sum(
                address_data.get("scores", {}).values()
            ) + sum(
                address_data.get("base_scores", {}).values()
            )
            total_prime_cached = (
                address_data.get("prime_amount_cached", 0)
                + address_data.get("base_prime_amount_cached", 0)
            )
            address_data.update({
                "total_score": total_score,
                "total_prime_cached": total_prime_cached,
                "position": position,
                "total_users": len(data),
            })
            return address_data
    return {"message": "Address not found"}
