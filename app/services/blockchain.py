from ..config import web3
from .logging_service import logging_service
from dotenv import load_dotenv
import aiohttp
import json
import logging
import os
import asyncio

load_dotenv()

# Limit concurrent tasks to avoid overloading the API endpoints
MAX_CONCURRENT_REQUESTS = 50

class BlockchainService:
	def __init__(self):
		self.api_key = os.getenv("ALCHEMY_API_KEY")
		assert self.api_key, "Please set ALCHEMY_API_KEY in your .env file."

	async def _fetch_logs(self, filter_params, semaphore):
		loop = asyncio.get_running_loop()
		async with semaphore:
			return await loop.run_in_executor(None, web3.eth.get_logs, filter_params)

	async def fetch_logs_in_batches(self, contract_address, from_block, to_block, batch_size):
		task_name = f"fetch_logs_{contract_address}"
		logging_service.start_timer(task_name)
		
		all_logs = []
		contract_address = web3.to_checksum_address(contract_address)
		semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
		tasks = []
		for start_block in range(from_block, to_block + 1, batch_size):
			end_block = min(start_block + batch_size - 1, to_block)
			filter_params = {
				"fromBlock": start_block,
				"toBlock": end_block,
				"address": contract_address,
			}
			tasks.append(self._fetch_logs(filter_params, semaphore))
		
		# Run batch log requests concurrently
		results = await asyncio.gather(*tasks, return_exceptions=False)
		for logs in results:
			all_logs.extend(logs)
		
		duration = logging_service.end_timer(task_name)
		await logging_service.log(
			f"Fetched logs for {contract_address} in {duration:.2f} seconds",
			send_telegram=False
		)
		return all_logs

	async def get_interacting_addresses_alchemy(self, network: str, contract_address: str, from_block: int):
		task_name = f"get_interacting_addresses_alchemy_{network}"
		logging_service.start_timer(task_name)
		
		await logging_service.log(
			f"[{network}] Start get_interacting_addresses for contract: {contract_address}"
		)
		to_block = await self.get_latest_block_number(network)
		logs = await self._fetch_logs_in_batches_alchemy(network, contract_address, from_block, to_block)
		await logging_service.log(f"[{network}] Retrieved {len(logs)} logs from Alchemy")

		addresses = []
		for log in logs:
			if len(log.get("topics", [])) > 1:
				addr_hex = "0x" + log["topics"][1][-40:]
				addresses.append(addr_hex.lower())

		unique_addresses = set(addresses)
		
		duration = logging_service.end_timer(task_name)
		await logging_service.log(
			f"[{network}] Found {len(unique_addresses)} unique addresses in {duration:.2f} seconds"
		)
		return unique_addresses

	async def _fetch_logs_in_batches_alchemy(self, network: str, contract_address: str, start_block: int, end_block: int):
		"""
		Chunk the block range into increments suited to Alchemy's limits, then run the requests concurrently.
		"""
		all_logs = []
		batch_size = 100000 if network == "eth-mainnet" else 10000000
		chunks = []
		current_block = start_block
		while current_block <= end_block:
			chunk_end = min(current_block + batch_size - 1, end_block)
			chunks.append((current_block, chunk_end))
			current_block = chunk_end + 1

		semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
		async with aiohttp.ClientSession() as session:
			tasks = [
				self._fetch_logs_alchemy_with_semaphore(session, network, contract_address, f, t, semaphore)
				for f, t in chunks
			]
			results = await asyncio.gather(*tasks, return_exceptions=False)
			for logs in results:
				all_logs.extend(logs)
		return all_logs

	async def _fetch_logs_alchemy_with_semaphore(self, session: aiohttp.ClientSession, network: str, contract_address: str, from_block: int, to_block: int, semaphore: asyncio.Semaphore):
		async with semaphore:
			return await self._fetch_logs_alchemy(session, network, contract_address, from_block, to_block)

	async def _fetch_logs_alchemy(self, session: aiohttp.ClientSession, network: str, contract_address: str, from_block: int, to_block: int):
		"""Calls Alchemy's eth_getLogs endpoint for a given block range."""
		def to_hex(block):
			return hex(block) if isinstance(block, int) else str(block)

		payload = {
			"jsonrpc": "2.0",
			"id": 1,
			"method": "eth_getLogs",
			"params": [{
				"fromBlock": to_hex(from_block),
				"toBlock": to_hex(to_block),
				"address": contract_address,
			}]
		}

		url = f"https://{network}.g.alchemy.com/v2/{self.api_key}"

		async with session.post(url, json=payload) as resp:
			resp.raise_for_status()
			data = await resp.json()

		return data.get("result", [])

	def calculate_and_sort_addresses(self, data):
		logging.debug("Starting calculate_and_sort_addresses function")
		
		total_all_scores = sum(
			sum(info.get("data", {}).get("merged_score_data", {}).values())
			for info in data
		)
		logging.debug(f"Total score for all addresses: {total_all_scores}")

		for address_info in data:
			merged_scores = address_info["data"].get("merged_score_data", {})
			address_score = sum(merged_scores.values())
			percentage = (address_score / total_all_scores) * 100 if total_all_scores > 0 else 0
			address_info["data"]["percentage"] = percentage
			logging.debug(
				f"Address {address_info['address']} - Score: {address_score}, Percentage: {percentage:.2f}%"
			)

		sorted_data = sorted(
			data,
			key=lambda x: sum(x["data"].get("merged_score_data", {}).values()),
			reverse=True
		)
		
		for index, address_info in enumerate(sorted_data):
			address_info["data"]["position"] = index + 1
			logging.debug(
				f"Address {address_info['address']} assigned position {index + 1}"
			)

		return sorted_data

	def calculate_addresses_position(self, addresses):
		with open("interacting_addresses.json", "r") as f:
			data = json.load(f)
		
		if len(addresses) == 1:
			for index, address_info in enumerate(data):
				if address_info["address"].lower() == addresses[0].lower():
					return index + 1
			return len(data)
		else:
			total_score = 0
			for address in addresses:
				address_info = next(
					(info for info in data if info["address"].lower() == address.lower()),
					None
				)
				if address_info:
					total_score += sum(address_info["data"].get("merged_score_data", {}).values())
			
			higher_scores = sum(
				1 for info in data
				if sum(info["data"].get("merged_score_data", {}).values()) > total_score
			)
			
			return higher_scores + 1

	async def get_avatar_count(self, addresses_data):
		url = f"https://eth-mainnet.g.alchemy.com/nft/v3/{self.api_key}/getOwnersForContract"
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

		address_to_balance = {
			owner['ownerAddress'].lower(): sum(int(token['balance']) for token in owner['tokenBalances'])
			for owner in owners_data
		}

		for item in addresses_data:
			address = item['address'].lower()
			item['data']['avatar_count'] = address_to_balance.get(address, 0)

		return addresses_data

	async def get_latest_block_number(self, network: str) -> int:
		url = f"https://{network}.g.alchemy.com/v2/{self.api_key}"
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
		
		hex_block_number = data["result"]
		return int(hex_block_number, 16)

	async def update_ens_names(self):
		task_name = "update_ens_names"
		logging_service.start_timer(task_name)
		
		try:
			await logging_service.log("Starting ENS name update process...")
			
			try:
				with open("ens.json", "r") as f:
					ens_data = json.load(f)
				await logging_service.log(f"Loaded {len(ens_data)} existing ENS records")
			except FileNotFoundError:
				await logging_service.log("No existing ENS data found, starting fresh")
				ens_data = {}
			
			new_ens_count = 0
			updated_ens_count = 0

			loop = asyncio.get_running_loop()
			semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

			async def process_address(i, address):
				nonlocal new_ens_count, updated_ens_count
				address = web3.to_checksum_address(address)
				try:
					async with semaphore:
						ens_name = await loop.run_in_executor(None, web3.ens.name, address)
					if ens_name:
						if address.lower() not in ens_data or ens_data[address.lower()] != ens_name:
							ens_data[address.lower()] = ens_name
							new_ens_count += 1
						else:
							updated_ens_count += 1
						await logging_service.log(
							f"[{i}/{len(ens_data)}] Found ENS name for {address}: {ens_name}",
							send_telegram=False
						)
					else:
						if address.lower() in ens_data:
							del ens_data[address.lower()]
						await logging_service.log(
							f"[{i}/{len(ens_data)}] No ENS name found for {address}",
							send_telegram=False
						)
				except Exception as e:
					await logging_service.add_error("ENS Lookup", address, str(e))
					await logging_service.log(
						f"[{i}/{len(ens_data)}] Error getting ENS name for {address}: {e}",
						send_telegram=False
					)

			# Process all addresses concurrently with rate limiting via semaphore
			unique_addresses = {info["address"] for info in ens_data}
			tasks = [process_address(i, addr) for i, addr in enumerate(unique_addresses, 1)]
			await asyncio.gather(*tasks)

			# Save updated ENS data
			with open("ens.json", "w") as f:
				json.dump(ens_data, f, indent=4)
			await logging_service.log("ENS data saved successfully")
			
			# Update interacting addresses with new ENS data
			try:
				with open("interacting_addresses.json", "r") as f:
					interacting_addresses = json.load(f)
				
				# Use the new add_ens_names function to update the addresses
				updated_addresses = await self.add_ens_names(interacting_addresses)
				
				with open("interacting_addresses.json", "w") as f:
					json.dump(updated_addresses, f, indent=4)
				await logging_service.log("Interacting addresses updated successfully")
				
			except FileNotFoundError:
				await logging_service.log("No interacting_addresses.json file found to update")
			
			duration = logging_service.end_timer(task_name)
			await logging_service.log(
				f"\n🏁 ENS update summary ({duration:.2f} seconds):\n"
				f"- Total addresses processed: {len(unique_addresses)}\n"
				f"- New/Updated ENS names found: {new_ens_count}\n"
				f"- Unchanged ENS names: {updated_ens_count}\n"
				f"- Total ENS records: {len(ens_data)}"
			)
			
		except Exception as e:
			await logging_service.add_error("Critical ENS Update", "global", str(e))
			await logging_service.log(f"Critical error during ENS update process: {e}")
			logging_service.end_timer(task_name)

	async def add_ens_names(self, addresses_data):
		"""
		Add ENS names to addresses_data using cached data from ens.json.
		This is a fast operation that doesn't make any network calls.
		"""
		task_name = "add_ens_names"
		logging_service.start_timer(task_name)
		
		try:
			try:
				with open("ens.json", "r") as f:
					ens_data = json.load(f)
				await logging_service.log(f"Loaded {len(ens_data)} cached ENS records")
			except FileNotFoundError:
				await logging_service.log("No cached ENS data found")
				logging_service.end_timer(task_name)
				return addresses_data

			ens_matches = 0
			for address_info in addresses_data:
				address = address_info["address"].lower()
				if address in ens_data:
					address_info["data"]["ens_name"] = ens_data[address]
					ens_matches += 1
				elif "ens_name" in address_info["data"]:
					del address_info["data"]["ens_name"]

			duration = logging_service.end_timer(task_name)
			await logging_service.log(
				f"Added {ens_matches} ENS names from cache in {duration:.2f} seconds"
			)
			
			return addresses_data
			
		except Exception as e:
			await logging_service.add_error("Add ENS Names", "global", str(e))
			await logging_service.log(f"Error during ENS name addition: {e}")
			logging_service.end_timer(task_name)
			return addresses_data

# Create a singleton instance
blockchain_service = BlockchainService()
