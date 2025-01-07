from ..constants import STAKING_CONTRACT_ADDRESS, STAKING_CONTRACT_ADDRESS_BASE, CREATION_BLOCK, BASE_CREATION_BLOCK
from .blockchain import get_interacting_addresses_alchemy, calculate_and_sort_addresses, get_avatar_count
from .cache import fetch_cache_data
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import json
import os

load_dotenv()

ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
assert ALCHEMY_API_KEY, "Please set ALCHEMY_API_KEY in your .env file."

scheduler = BackgroundScheduler()

# async def update_interacting_addresses():
#     creation_block = 20019797
#     base_creation_block = 15628915
#     print("Updating addresses")
#     addresses_base = await get_interacting_addresses(STAKING_CONTRACT_ADDRESS_BASE, base_creation_block)
#     addresses = await get_interacting_addresses(STAKING_CONTRACT_ADDRESS, creation_block)
#     addresses.update(addresses_base)
#     with open("interacting_addresses.json", "w") as f:
#         json.dump(addresses, f, indent=4)
#     print("Addresses updated")


ETH_NETWORK = "eth-mainnet"
BASE_NETWORK = "base-mainnet"


async def update_interacting_addresses():
    """
    1) Fetch interacting addresses from Base & Mainnet (via Alchemy).
    2) Merge all addresses (remove duplicates).
    3) Fetch cache data for the merged addresses in one shot.
    4) Save the final data object to JSON (like the old code).
    """


    print("Step 1: Fetching interacting addresses from Base & Mainnet...")

    addresses_base = await get_interacting_addresses_alchemy(
        BASE_NETWORK,
        STAKING_CONTRACT_ADDRESS_BASE,
        BASE_CREATION_BLOCK
    )  # returns a set of addresses

    addresses_eth = await get_interacting_addresses_alchemy(
        ETH_NETWORK,
        STAKING_CONTRACT_ADDRESS,
        CREATION_BLOCK
    )  # also returns a set of addresses

    print(f"Base returned {len(addresses_base)} addresses.")
    print(f"Ethereum returned {len(addresses_eth)} addresses.")

    # Step 2: Merge and remove duplicates
    merged_addresses = addresses_base.union(addresses_eth)
    print(f"Merged total: {len(merged_addresses)} unique addresses.")

    # Step 3: Fetch cache data for the merged addresses
    print("Fetching cache data for merged addresses...")
    cache_data = await fetch_cache_data(list(merged_addresses))
    # Filter out any that have `data=None`
    cache_data = [item for item in cache_data if item["data"] is not None]
    print(f"Retrieved cache data for {len(cache_data)} addresses (non-empty data).")

    # Optionally save the raw/unprocessed data:
    with open("original_interacting_addresses.json", "w") as f:
        json.dump(cache_data, f, indent=4)

    # Step 4: Transform data if "extra" / "primary_address_badge_data" is present
    for item in cache_data:
        if "extra" in item["data"] and "primary_address_badge_data" in item["data"]["extra"]:
            item["data"] = item["data"]["extra"]["primary_address_badge_data"]

    # Now do your custom sorting
    print("Calculating and sorting addresses...")
    sorted_addresses_data = calculate_and_sort_addresses(cache_data)

    print("Getting avatar count for sorted addresses...")
    sorted_addresses_data = await get_avatar_count(sorted_addresses_data)

    # Finally, save the *full object* (like the old code) to interacting_addresses.json
    # You can choose the final name. If you only want the final sorted data, just dump that.
    with open("interacting_addresses.json", "w") as f:
        json.dump(sorted_addresses_data, f, indent=4)

    print("Successfully updated interacting_addresses.json with full data!")

def schedule_hourly_update():
    """Schedule the update_interacting_addresses function to run every hour"""
    scheduler.add_job(update_interacting_addresses, 'interval', hours=1)
    scheduler.start()