from ..config import scheduler
from .blockchain import get_interacting_addresses
from .cache import fetch_cache_data
from ..constants import STAKING_CONTRACT_ADDRESS
import json

async def update_interacting_addresses():
    creation_block = 20019797
    print("Updating addresses")
    addresses = await get_interacting_addresses(STAKING_CONTRACT_ADDRESS, creation_block)
    cache_data = await fetch_cache_data(addresses)
    cache_data = [data for data in cache_data if data["data"] is not None]
    with open("interacting_addresses.json", "w") as f:
        json.dump(cache_data, f, indent=4)
    print("Addresses updated")

def schedule_daily_update():
    scheduler.add_job(update_interacting_addresses, "interval", days=1)
    scheduler.start()
