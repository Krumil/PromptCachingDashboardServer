import json
from ..config import web3

async def fetch_logs_in_batches(contract_address, from_block, to_block, batch_size):
    all_logs = []
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
    to_block = web3.eth.block_number
    logs = await fetch_logs_in_batches(
        contract_address, from_block, to_block, batch_size
    )
    addresses = [web3.to_checksum_address(log["topics"][1].hex()[-40:]) for log in logs]
    return list(set(addresses))

def calculate_address_position(address):
    with open("interacting_addresses.json", "r") as f:
        data = json.load(f)
    total_score = 0
    for info in data:
        if info["address"].lower() == address.lower():
            total_score = sum(
                info["data"].get("scores", {}).values()
            ) + sum(
                info["data"].get("base_scores", {}).values()
            )
            break
    sorted_data = sorted(
        data,
        key=lambda x: sum(
            x["data"].get("scores", {}).values()
        ) + sum(
            x["data"].get("base_scores", {}).values()
        ),
        reverse=True,
    )
    for i, info in enumerate(sorted_data):
        if info["address"].lower() == address.lower():
            return i + 1
    return -1
