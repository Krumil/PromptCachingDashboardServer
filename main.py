import aiohttp
import json
import asyncio

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
from web3 import Web3
from pydantic import BaseModel


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
	schedule_daily_update()
	await update_interacting_addresses()
	yield


app = FastAPI(lifespan=lifespan)

# Replace with your own Infura, Alchemy, or other provider URL
provider_url = "https://ethereum-rpc.publicnode.com"
provider_url_base = "https://base-rpc.publicnode.com"
staking_contract_address = "0x4a3826bd2e8a31956ad0397a49efde5e0d825238"
staking_contract_address_base = "0x75a44a70ccb0e886e25084be14bd45af57915451"
prime_token_address = "0xb23d80f5FefcDDaa212212F028021B41DEd428CF"

# Initialize web3 provider
web3 = Web3(Web3.HTTPProvider(provider_url))

# ABI definitions load from abi folder
with open("abi/staking_contract_abi.json", "r") as f:
	staking_contract_abi = json.load(f)

with open("abi/prime_token_abi.json", "r") as f:
	prime_token_abi = json.load(f)

# Contract instances
staking_contract_address = web3.to_checksum_address(staking_contract_address)
prime_token_address = web3.to_checksum_address(prime_token_address)
staking_contract = web3.eth.contract(
	address=staking_contract_address, abi=staking_contract_abi
)
prime_token_contract = web3.eth.contract(
	address=prime_token_address, abi=prime_token_abi
)

# Initialize the scheduler
scheduler = BackgroundScheduler()


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
	# Extract user addresses directly from logs
	addresses = [web3.to_checksum_address(log["topics"][1].hex()[-40:]) for log in logs]
	addresses = list(set(addresses))
	return addresses


async def fetch_cache_data(addresses):
	async with aiohttp.ClientSession() as session:
		tasks = []
		for address in addresses:
			api_url = (
				f"https://caching.wayfinder.ai/api/walletstats/{address}?format=json"
			)
			tasks.append(fetch_data(session, api_url, address))
		results = await asyncio.gather(*tasks)
	return results


async def fetch_data(session, api_url, address):
	async with session.get(api_url) as response:
		if response.status == 200:
			data = await response.json()
			return {"address": address, "data": data}
		else:
			return {"address": address, "data": None}


async def update_interacting_addresses():
	creation_block = 20019797
	print("Updating addresses")
	addresses = await get_interacting_addresses(
		staking_contract_address, creation_block
	)
	cache_data = await fetch_cache_data(addresses)
	cache_data = [data for data in cache_data if data["data"] is not None]
	with open("interacting_addresses.json", "w") as f:
		json.dump(cache_data, f, indent=4)
	print("Addresses updated")


@app.get("/get_global_data")
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


@app.get("/addresses")
async def get_addresses():
	with open("interacting_addresses.json", "r") as f:
		data = json.load(f)
	return data


class AddressRequest(BaseModel):
	address: str


@app.post("/addresses")
async def get_address_info(request: AddressRequest):
	position = calculate_address_position(request.address)
	address = request.address
	with open("interacting_addresses.json", "r") as f:
		data = json.load(f)
	for info in data:
		address_data = info["data"]
		if info["address"].lower() == address.lower():

			total_score = 0
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

			total_prime_cached = 0
			if "prime_amount_cached" in address_data:
				total_prime_cached += address_data["prime_amount_cached"]
			if "base_prime_amount_cached" in address_data:
				total_prime_cached += address_data["base_prime_amount_cached"]
			address_data["total_score"] = total_score
			address_data["total_prime_cached"] = total_prime_cached
			address_data["position"] = position
			address_data["number_of_addresses"] = len(data)
			return address_data
	return {"message": "Address not found"}


@app.post("/update_addresses")
async def trigger_update_addresses(background_tasks: BackgroundTasks):
	background_tasks.add_task(update_interacting_addresses)
	return {"message": "Address update initiated"}


# Schedule the daily update
def schedule_daily_update():
	scheduler.add_job(update_interacting_addresses, "interval", days=1)
	scheduler.start()


def calculate_address_position(address):
	# function that calculate the score of every address, sort them and return the position of the address
	with open("interacting_addresses.json", "r") as f:
		data = json.load(f)
	total_score = 0
	for info in data:
		address_data = info["data"]
		if info["address"].lower() == address.lower():
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
			break

	data = sorted(
		data,
		key=lambda x: x["data"]["scores"]["prime_score"]
		+ x["data"]["scores"]["community_score"]
		+ x["data"]["scores"]["initialization_score"],
		reverse=True,
	)

	for i, info in enumerate(data):
		if info["address"].lower() == address.lower():
			return i + 1

	return -1
