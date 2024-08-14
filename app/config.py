import json
from web3 import Web3
# from apscheduler.schedulers.background import BackgroundScheduler
# from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
from .constants import PROVIDER_URL, STAKING_CONTRACT_ADDRESS, PRIME_TOKEN_ADDRESS

load_dotenv()

web3 = Web3(Web3.HTTPProvider(PROVIDER_URL))

with open("abi/staking_contract_abi.json", "r") as f:
    staking_contract_abi = json.load(f)

with open("abi/prime_token_abi.json", "r") as f:
    prime_token_abi = json.load(f)

staking_contract = web3.eth.contract(
    address=web3.to_checksum_address(STAKING_CONTRACT_ADDRESS), 
    abi=staking_contract_abi
)
prime_token_contract = web3.eth.contract(
    address=web3.to_checksum_address(PRIME_TOKEN_ADDRESS), 
    abi=prime_token_abi
)

# scheduler = BackgroundScheduler()

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     from .services.scheduler import schedule_daily_update, update_interacting_addresses
#     schedule_daily_update()
#     await update_interacting_addresses()
#     yield
