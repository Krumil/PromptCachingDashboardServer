from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import json

router = APIRouter()

# Load the ENS data from the JSON file and create reverse mapping
try:
    with open("ens.json", "r") as f:
        ens_data = json.load(f)
        # Create reverse mapping for ENS to address lookups
        ens_to_address = {name.lower(): addr for addr, name in ens_data.items() if isinstance(name, str)}
except FileNotFoundError:
    ens_data = {}
    ens_to_address = {}

@router.get("/ens/{address}")
async def get_ens(address: str):
    """
    Get the ENS name for a given Ethereum address.
    If the address is not found, return a 404 error.
    """
    address = address.lower()  # Convert to lowercase for case-insensitive matching
    if address in ens_data:
        return {"address": address, "ens_name": ens_data[address]}
    else:
        return {"address": address, "ens_name": None}

@router.get("/ens")
async def get_all_ens():
    """
    Get all ENS entries.
    """
    return JSONResponse(content=ens_data)

@router.get("/ens/reverse/{ens_name}")
async def get_address_by_ens(ens_name: str):
    """
    Get the Ethereum address for a given ENS name.
    If the ENS name is not found, return a 404 error.
    """
    ens_name_lower = ens_name.lower()
    if ens_name_lower in ens_to_address:
        return {"ens_name": ens_name, "address": ens_to_address[ens_name_lower]}
    raise HTTPException(status_code=404, detail="ENS name not found")
