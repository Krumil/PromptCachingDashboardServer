from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import json

router = APIRouter()

# Load the ENS data from the JSON file
try:
    with open("ens.json", "r") as f:
        ens_data = json.load(f)
except FileNotFoundError:
    ens_data = {}

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
        raise HTTPException(status_code=404, detail="Address not found")

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
    for address, name in ens_data.items():
        if name.lower() == ens_name.lower():
            return {"ens_name": ens_name, "address": address}
    raise HTTPException(status_code=404, detail="ENS name not found")
