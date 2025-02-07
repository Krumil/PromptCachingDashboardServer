from dotenv import load_dotenv
from dune_client.client import DuneClient
import os
import asyncio
from .stats import stats_service, CacheStats

load_dotenv()

class DuneService:
    def __init__(self):
        self.api_key = os.getenv("DUNE_API_KEY")
        assert self.api_key, "Please set DUNE_API_KEY in your .env file."
        self.dune = DuneClient(self.api_key)
        # self.QUERY_ID = 4665548  # The query ID for prime caching data
        self.QUERY_ID = 4681874  # The query ID for prime caching data
        self._latest_result = None
        self.cache_file = "dune_cache.json"
        self.cache_duration = 24 * 60 * 60 + 60  # 24 hours in seconds + 1 minute

    async def get_latest_query_result(self):
        """
        Fetch the latest result from Dune Analytics query.
        Caches the result to avoid multiple API calls.
        Cache persists in a JSON file and is valid for 24 hours.
        """
        if self._latest_result is None:
            # Try to load from cache file
            cached_data = self._load_cache()
            if cached_data:
                self._latest_result = cached_data
                return self._latest_result

            try:
                loop = asyncio.get_running_loop()
                query_result = await loop.run_in_executor(None, self.dune.get_latest_result, self.QUERY_ID)
                self._latest_result = query_result.result.rows
                # Save to cache file
                self._save_cache(self._latest_result)
            except Exception as e:
                print(f"Error fetching Dune data: {str(e)}")
                return []
        
        return self._latest_result

    def _load_cache(self):
        """Load cached data from JSON file if it exists and is not expired"""
        import json
        from datetime import datetime
        import time
        
        try:
            if not os.path.exists(self.cache_file):
                return None
                
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
                
            # Check if cache is expired
            cache_time = cache_data.get('timestamp', 0)
            if time.time() - cache_time > self.cache_duration:
                return None
                
            return cache_data.get('data')
        except Exception as e:
            print(f"Error loading cache: {str(e)}")
            return None

    def _save_cache(self, data):
        """Save data to JSON cache file with timestamp"""
        import json
        import time
        
        try:
            cache_data = {
                'timestamp': time.time(),
                'data': data
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f)
        except Exception as e:
            print(f"Error saving cache: {str(e)}")

    async def get_interacting_addresses(self):
        """
        Fetch interacting addresses from Dune Analytics using the prime caching query.
        Returns a set of unique addresses that have interacted with the prime caching contract.
        """
        rows = await self.get_latest_query_result()
        
        addresses = set()
        for row in rows:
            if isinstance(row, dict):
                user = row.get('user')
                if user:
                    addresses.add(user)
        
        return addresses

    async def get_cache_stats(self):
        """
        Get cache statistics from the cached data.
        Returns None if no cached data is available.
        """
        try:
            cached_data = self._load_cache()
            if cached_data is None:
                # If no cache exists or it's expired, fetch new data
                await self.get_latest_query_result()
                cached_data = self._load_cache()
                
            if cached_data is None:
                return None
                
            # Process the cached data into stats
            return CacheStats(
                total_cached=len(cached_data),
                # Add other stats processing as needed based on your CacheStats model
            )
        except Exception as e:
            print(f"Error processing cache stats: {str(e)}")
            return None

    def invalidate_cache(self):
        """Clear the cached query result"""
        self._latest_result = None

# Create a singleton instance
dune_service = DuneService() 