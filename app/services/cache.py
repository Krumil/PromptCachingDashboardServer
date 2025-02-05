import aiohttp
import asyncio
from typing import List, Dict
from dotenv import load_dotenv
import json
from .logging_service import logging_service

load_dotenv()

class CacheService:
    def __init__(self):
        self.BATCH_SIZE = 25  # Reduced from 100 to prevent too many concurrent connections
        self.TIMEOUT = 30  # Timeout in seconds
        self.MAX_CONCURRENT_REQUESTS = 50  # Limit concurrent connections
        self.semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)

    async def fetch_wayfinder_data(self, addresses: List[str]) -> List[Dict]:
        """Fetch cache data for multiple addresses in batches"""
        all_results = []
        total_batches = (len(addresses) + self.BATCH_SIZE - 1) // self.BATCH_SIZE
        errors_count = 0
        success_count = 0
        
        task_name = "fetch_wayfinder_data"
        logging_service.start_timer(task_name)
        
        await logging_service.log(f"🚀 Starting to fetch wayfinder data for {len(addresses)} addresses")
        
        # Process addresses in batches
        connector = aiohttp.TCPConnector(limit=self.MAX_CONCURRENT_REQUESTS, force_close=True)
        timeout = aiohttp.ClientTimeout(total=self.TIMEOUT)

        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for i in range(0, len(addresses), self.BATCH_SIZE):
                batch = addresses[i:i + self.BATCH_SIZE]
                current_batch = i//self.BATCH_SIZE + 1
                await logging_service.log(f"Processing batch {current_batch}/{total_batches}", send_telegram=False)
                
                tasks = [
                    self._fetch_data(session, f"https://caching.wayfinder.ai/api/walletstats/{address}?format=json", address)
                    for address in batch
                ]
                batch_results = await asyncio.gather(*tasks)
                
                # Count successes and failures
                batch_success = sum(1 for r in batch_results if r["data"] is not None)
                batch_errors = sum(1 for r in batch_results if r["data"] is None)
                success_count += batch_success
                errors_count += batch_errors
                
                all_results.extend(batch_results)
                
                # Send progress update less frequently
                if current_batch % 10 == 0 or current_batch == total_batches:
                    await logging_service.log(
                        f"📊 Progress Update:\n"
                        f"Batch: {current_batch}/{total_batches}\n"
                        f"✅ Success: {success_count}\n"
                        f"❌ Errors: {errors_count}\n"
                        f"Progress: {(success_count/len(addresses)*100):.1f}%"
                    )
                
                # Add a small delay between batches to prevent overwhelming
                if i + self.BATCH_SIZE < len(addresses):
                    await asyncio.sleep(1)

        # Send any remaining errors
        await logging_service.send_error_report()
        
        duration = logging_service.end_timer(task_name)
        # Send final summary
        await logging_service.log(
            f"🏁 Cache data fetch completed in {duration:.2f} seconds\n"
            f"✅ Total successful: {success_count}\n"
            f"❌ Total failed: {errors_count}\n"
            f"📊 Success rate: {(success_count/len(addresses)*100):.1f}%"
        )
        
        return all_results

    async def _fetch_data(self, session: aiohttp.ClientSession, api_url: str, address: str) -> Dict:
        """Fetch data for a single address with basic error handling"""
        async with self.semaphore:  # Limit concurrent requests
            try:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"address": address, "data": data}
                    elif response.status == 429:  # Rate limit
                        response_text = await response.text()
                        await logging_service.add_error("Rate Limit", address, response_text)
                        await asyncio.sleep(2)  # Wait a bit longer for rate limits
                        return {"address": address, "data": None}
                    else:
                        try:
                            response_text = await response.text()
                            error_detail = f"Status {response.status}. Response: {response_text}"
                        except:
                            error_detail = f"Status {response.status}. Could not read response body."
                        await logging_service.add_error("HTTP Error", address, error_detail)
                        return {"address": address, "data": None}
                        
            except asyncio.TimeoutError:
                error_detail = f"Request timed out after {self.TIMEOUT} seconds"
                await logging_service.add_error("Timeout", address, error_detail)
                return {"address": address, "data": None}
            except aiohttp.ClientError as e:
                error_detail = f"Network error: {str(e)}"
                await logging_service.add_error("Network Error", address, error_detail)
                return {"address": address, "data": None}
            except json.JSONDecodeError as e:
                error_detail = f"Invalid JSON response: {str(e)}"
                await logging_service.add_error("JSON Error", address, error_detail)
                return {"address": address, "data": None}
            except Exception as e:
                error_detail = f"Unexpected error: {str(e)}"
                await logging_service.add_error("General Error", address, error_detail)
                return {"address": address, "data": None}

# Create a singleton instance
cache_service = CacheService()
