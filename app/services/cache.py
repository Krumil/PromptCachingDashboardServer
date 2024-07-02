import aiohttp
import asyncio

async def fetch_cache_data(addresses):
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_data(session, f"https://caching.wayfinder.ai/api/walletstats/{address}?format=json", address)
            for address in addresses
        ]
        return await asyncio.gather(*tasks)

async def fetch_data(session, api_url, address):
    async with session.get(api_url) as response:
        if response.status == 200:
            data = await response.json()
            return {"address": address, "data": data}
        else:
            return {"address": address, "data": None}
