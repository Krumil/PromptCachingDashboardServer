from dotenv import load_dotenv
from dune_client.client import DuneClient
import os
import asyncio
import json

load_dotenv()

class DuneService:
    def __init__(self):
        self.api_key = os.getenv("DUNE_API_KEY")
        assert self.api_key, "Please set DUNE_API_KEY in your .env file."
        self.dune = DuneClient(self.api_key)
        self.QUERY_ID = 4665548  # The query ID for prime caching data

    async def get_interacting_addresses(self):
        """
        Fetch interacting addresses from Dune Analytics using the prime caching query.
        Returns a set of unique addresses that have interacted with the prime caching contract.
        """
        
        try:
            # Execute in thread pool since Dune client is synchronous
            loop = asyncio.get_running_loop()
            query_result = await loop.run_in_executor(None, self.dune.get_latest_result, self.QUERY_ID)
            
            addresses = set()
            for row in query_result.result.rows:

                # Assuming the address is in a field called 'user'
                if isinstance(row, dict):
                    user = row.get('user')
                    if user:
                        addresses.add(user)
            
            return addresses

        except Exception as e:
            print(f"Error in get_interacting_addresses: {str(e)}")
            print(f"Exception type: {type(e)}")
            if hasattr(e, '__dict__'):
                print(f"Exception attributes: {e.__dict__}")
            return set()

# Create a singleton instance
dune_service = DuneService() 