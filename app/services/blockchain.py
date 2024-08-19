from ..config import web3
from .cache import fetch_cache_data
from dotenv import load_dotenv
import aiohttp
import json
import logging
import os

load_dotenv()

async def fetch_logs_in_batches(contract_address, from_block, to_block, batch_size):
    all_logs = []
    contract_address = web3.to_checksum_address(contract_address)
    for start_block in range(from_block, to_block + 1, batch_size):
        end_block = min(start_block + batch_size - 1, to_block)
        filter_params = {
            "fromBlock": start_block,
            "toBlock": end_block,
            "address": contract_address,
        }
        logs = web3.eth.get_logs(filter_params)
        all_logs.extend(logs)
    return all_logs

async def get_interacting_addresses(contract_address, from_block, batch_size=10000):
    logging.info(f"Starting get_interacting_addresses for contract: {contract_address}")
    to_block = web3.eth.block_number
    logging.info(f"Fetching logs from block {from_block} to {to_block}")
    logs = await fetch_logs_in_batches(
        contract_address, from_block, to_block, batch_size
    )
    logging.info(f"Retrieved {len(logs)} logs")
    addresses = [web3.to_checksum_address(log["topics"][1].hex()[-40:]) for log in logs]
    addresses = list(set(addresses))
    logging.info(f"Found {len(addresses)} unique addresses")
    logging.info("Fetching cache data for addresses")
    cache_data = await fetch_cache_data(addresses)
    cache_data = [data for data in cache_data if data["data"] is not None]    
    logging.info(f"Retrieved cache data for {len(cache_data)} addresses")
    logging.info("Calculating and sorting addresses")

    with open("original_interacting_addresses.json", "w") as f:
        json.dump(cache_data, f, indent=4)

    # for every cache_data item, check if "extra" is present and "primary_address_badge_data" is present
    # if so, use that data, otherwise use the data from the cache_data item
    for item in cache_data:
        if "extra" in item["data"] and "primary_address_badge_data" in item["data"]["extra"]:
            item["data"] = item["data"]["extra"]["primary_address_badge_data"]

    sorted_addresses_data = calculate_and_sort_addresses(cache_data)
    logging.info("Getting avatar count for sorted addresses")
    sorted_addresses_data = await get_avatar_count(sorted_addresses_data)
    logging.info("Finished processing interacting addresses")
    return sorted_addresses_data

def calculate_and_sort_addresses(data):
    logging.info("Starting calculate_and_sort_addresses function")
    
    # Calculate total score for all addresses
    total_all_scores = sum(
        sum(info.get("data", {}).get("scores", {}).values()) + sum(info.get("data", {}).get("base_scores", {}).values())
        for info in data
    )
    logging.debug(f"Total score for all addresses: {total_all_scores}")

    # Calculate scores and positions for all addresses
    for address_info in data:
        address_score = sum(address_info["data"].get("scores", {}).values()) + sum(address_info["data"].get("base_scores", {}).values())
        percentage = (address_score / total_all_scores) * 100 if total_all_scores > 0 else 0
        address_info["data"]["total_score"] = address_score
        address_info["data"]["percentage"] = percentage
        logging.debug(f"Address {address_info['address']} - Score: {address_score}, Percentage: {percentage:.2f}%")

    # Sort data based on total scores
    sorted_data = sorted(
        data,
        key=lambda x: x["data"]["total_score"],
        reverse=True
    )
    logging.info("Data sorted based on total scores")
    # Assign positions
    for index, address_info in enumerate(sorted_data):
        address_info["data"]["position"] = index + 1
        logging.debug(f"Address {address_info['address']} assigned position {index + 1}")

    logging.info("Finished calculate_and_sort_addresses function")
    return sorted_data

def calculate_addresses_position(addresses):
    with open("interacting_addresses.json", "r") as f:
        data = json.load(f)
    
    if len(addresses) == 1:
        # If only one address, return its position directly
        for index, address_info in enumerate(data):
            if address_info["address"].lower() == addresses[0].lower():
                return index + 1
        return len(data)  # Return last position if address not found
    else:
        # For multiple addresses, sum scores and calculate position
        total_score = 0
        for address in addresses:
            address_info = next((info for info in data if info["address"].lower() == address.lower()), None)
            if address_info:
                address_data = address_info["data"]
                total_score += sum(address_data.get("scores", {}).values()) + sum(address_data.get("base_scores", {}).values())
        
        # Count how many addresses have a higher score
        higher_scores = sum(1 for info in data if 
                            (sum(info["data"].get("scores", {}).values()) + 
                             sum(info["data"].get("base_scores", {}).values())) > total_score)
        
        return higher_scores + 1  # Position is one more than the count of higher scores

    
async def get_avatar_count(addresses_data):
    api_key = os.getenv("ALCHEMY_API_KEY")
    url = f"https://eth-mainnet.g.alchemy.com/nft/v3/{api_key}/getOwnersForContract"
    params = {
        "contractAddress": "0x0fc3dd8c37880a297166bed57759974a157f0e74",
        "withTokenBalances": "true"
    }
    
    async def fetch_owners(session):
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('owners', [])
            else:
                logging.error(f"Failed to fetch data: {response.status}")
                return []

    async with aiohttp.ClientSession() as session:
        owners_data = await fetch_owners(session)

    # Create a dictionary for quick lookup
    address_to_balance = {
        owner['ownerAddress'].lower(): sum(int(token['balance']) for token in owner['tokenBalances'])
        for owner in owners_data
    }

    # Update avatar_count for each address in addresses_data
    for item in addresses_data:
        address = item['address'].lower()
        item['data']['avatar_count'] = address_to_balance.get(address, 0)

    return addresses_data

    
