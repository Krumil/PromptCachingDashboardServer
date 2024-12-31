from ..config import web3
from .cache import fetch_cache_data
from dotenv import load_dotenv
import aiohttp
import json
import logging
import os

load_dotenv()

ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
assert ALCHEMY_API_KEY, "Please set ALCHEMY_API_KEY in your .env file."

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
    print(f"Starting get_interacting_addresses for contract: {contract_address}")
    to_block = web3.eth.block_number
    print(f"Fetching logs from block {from_block} to {to_block}")
    logs = await fetch_logs_in_batches(
        contract_address, from_block, to_block, batch_size
    )
    print(f"Retrieved {len(logs)} logs")
    addresses = [web3.to_checksum_address(log["topics"][1].hex()[-40:]) for log in logs]
    addresses = list(set(addresses))
    print(f"Found {len(addresses)} unique addresses")
    print("Fetching cache data for addresses")
    cache_data = await fetch_cache_data(addresses)
    cache_data = [data for data in cache_data if data["data"] is not None]    
    print(f"Retrieved cache data for {len(cache_data)} addresses")
    print("Calculating and sorting addresses")

    with open("original_interacting_addresses.json", "w") as f:
        json.dump(cache_data, f, indent=4)

    # for every cache_data item, check if "extra" is present and "primary_address_badge_data" is present
    # if so, use that data, otherwise use the data from the cache_data item
    for item in cache_data:
        if "extra" in item["data"] and "primary_address_badge_data" in item["data"]["extra"]:
            item["data"] = item["data"]["extra"]["primary_address_badge_data"]

    sorted_addresses_data = calculate_and_sort_addresses(cache_data)
    print("Getting avatar count for sorted addresses")
    sorted_addresses_data = await get_avatar_count(sorted_addresses_data)
    print("Finished processing interacting addresses")
    return sorted_addresses_data

async def get_interacting_addresses_alchemy(
    network: str,
    contract_address: str,
    from_block: int,
):
    """
    Fetch all logs via Alchemy from `from_block` to 'latest',
    extract unique interacting addresses, and return them as a set.
    """
    print(f"[{network}] Start get_interacting_addresses for contract: {contract_address}")
    to_block = await get_latest_block_number(network)

    logs = await fetch_logs_in_batches_alchemy(
        network,
        contract_address,
        from_block,
        to_block,
    )
    print(f"[{network}] Retrieved {len(logs)} logs from Alchemy")

    # Extract addresses from topics
    addresses = []
    for log in logs:
        if len(log["topics"]) > 1:
            # Last 40 hex chars = address
            addr_hex = "0x" + log["topics"][1][-40:]
            addresses.append(addr_hex.lower())

    unique_addresses = set(addresses)
    print(f"[{network}] Found {len(unique_addresses)} unique addresses")

    return unique_addresses


async def fetch_logs_in_batches_alchemy(
    network: str,
    contract_address: str,
    start_block: int,
    end_block: int,
):
    """
    Chunk the block range [start_block..end_block] in increments of up to 2,000 blocks.
    This ensures no single request returns more than Alchemy's limit.
    """
    all_logs = []
    
    batch_size = 100000 if network == "eth-mainnet" else 10000000

    current_block = start_block

    async with aiohttp.ClientSession() as session:
        while current_block <= end_block:
            chunk_end = current_block + batch_size - 1

            if chunk_end > end_block:
                chunk_end = end_block

            # Fetch logs for [current_block..chunk_end]
            logs_chunk = await fetch_logs_alchemy(
                session,
                network,
                contract_address,
                current_block,
                chunk_end
            )
            all_logs.extend(logs_chunk)

            if chunk_end >= end_block:
                break

            current_block = chunk_end + 1

    return all_logs



async def fetch_logs_alchemy(
    session: aiohttp.ClientSession,
    network: str,
    contract_address: str,
    from_block: int,
    to_block
):
    """
    Calls Alchemy's eth_getLogs endpoint for a single block range.
    :param to_block: can be an integer or the string "latest"
    """
    # Convert from_block to hex if int
    def to_hex(block):
        if isinstance(block, int):
            return hex(block)
        return str(block)

    # Build the JSON-RPC body
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_getLogs",
        "params": [
            {
                "fromBlock": to_hex(from_block),
                "toBlock": to_hex(to_block),
                "address": contract_address,
            }
        ],
    }

    # Alchemy endpoint for, e.g., "eth-mainnet" => https://eth-mainnet.g.alchemy.com/v2/<API_KEY>
    # or "base-mainnet" => https://base-mainnet.g.alchemy.com/v2/<API_KEY>
    url = f"https://{network}.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

    async with session.post(url, json=payload) as resp:
        resp.raise_for_status()
        data = await resp.json()

    # data["result"] is either a list of logs or an error
    result = data.get("result", [])
    return result


def calculate_and_sort_addresses(data):
    print("Starting calculate_and_sort_addresses function")
    
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
    print("Data sorted based on total scores")
    # Assign positions
    for index, address_info in enumerate(sorted_data):
        address_info["data"]["position"] = index + 1
        logging.debug(f"Address {address_info['address']} assigned position {index + 1}")

    print("Finished calculate_and_sort_addresses function")
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

async def get_latest_block_number(network: str) -> int:
    """
    Calls Alchemy's eth_blockNumber to get the most recent block.
    Returns it as an integer (decimal).
    """
    url = f"https://{network}.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_blockNumber",
        "params": []
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            resp.raise_for_status()
            data = await resp.json()
    
    # data["result"] is the block number in hex, e.g. "0x12345..."
    hex_block_number = data["result"]
    return int(hex_block_number, 16)