"""
Tests for the Dune service.

This module contains tests for the Dune Analytics integration, including:
- Successful address retrieval
- Empty result handling
- Error handling
- Duplicate address handling
"""
import json
import asyncio
import pytest
from app.services.dune import dune_service
from unittest.mock import MagicMock, patch
from typing import List, NamedTuple

class MockRow(NamedTuple):
    user: str
    chain: str
    norm_amt: float
    depositIndex: int

def create_mock_result(addresses: List[str]):
    """Helper function to create a mock Dune query result"""
    rows = [MockRow(
        user=addr,
        chain='ETH',
        norm_amt=100.0,
        depositIndex=1
    ) for addr in addresses]
    
    mock_result = MagicMock()
    mock_result.rows = rows
    return mock_result

@pytest.mark.asyncio
async def test_get_addresses_success():
    """Test successful retrieval of interacting addresses"""
    try:
        print("\nTesting successful address retrieval from Dune...")
        # Mock addresses
        test_addresses = [
            "0x1234567890123456789012345678901234567890",
            "0xabcdef0123456789abcdef0123456789abcdef01",
            "0x9876543210987654321098765432109876543210"
        ]
        
        # Create mock result
        mock_result = create_mock_result(test_addresses)
        
        # Patch the Dune client's get_latest_result method
        with patch.object(dune_service.dune, 'get_latest_result', return_value=mock_result):
            # Call the service method
            addresses = await dune_service.get_interacting_addresses()
            
            # Verify the results
            assert isinstance(addresses, set)
            assert len(addresses) == len(test_addresses)
            assert all(addr.lower() in addresses for addr in test_addresses)
            print("Successfully retrieved and verified addresses!")
    except Exception as e:
        print(f"Error during successful retrieval test: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_get_addresses_empty():
    """Test handling of empty result set"""
    try:
        print("\nTesting empty result handling...")
        # Create empty mock result
        mock_result = create_mock_result([])
        
        # Patch the Dune client's get_latest_result method
        with patch.object(dune_service.dune, 'get_latest_result', return_value=mock_result):
            # Call the service method
            addresses = await dune_service.get_interacting_addresses()
            
            # Verify the results
            assert isinstance(addresses, set)
            assert len(addresses) == 0
            print("Successfully handled empty result!")
    except Exception as e:
        print(f"Error during empty result test: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_get_addresses_error():
    """Test error handling"""
    try:
        print("\nTesting error handling...")
        # Patch the Dune client to raise an exception
        with patch.object(dune_service.dune, 'get_latest_result', side_effect=Exception("Dune API error")):
            # Call the service method
            addresses = await dune_service.get_interacting_addresses()
            
            # Verify error handling
            assert isinstance(addresses, set)
            assert len(addresses) == 0
            print("Successfully handled error condition!")
    except Exception as e:
        print(f"Error during error handling test: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_get_addresses_duplicates():
    """Test handling of duplicate addresses"""
    try:
        print("\nTesting duplicate address handling...")
        # Mock addresses with duplicates (different case)
        test_addresses = [
            "0x1234567890123456789012345678901234567890",
            "0x1234567890123456789012345678901234567890",  # Duplicate
            "0X1234567890123456789012345678901234567890",  # Same address, different case
            "0xabcdef0123456789abcdef0123456789abcdef01"
        ]
        
        # Create mock result
        mock_result = create_mock_result(test_addresses)
        
        # Patch the Dune client's get_latest_result method
        with patch.object(dune_service.dune, 'get_latest_result', return_value=mock_result):
            # Call the service method
            addresses = await dune_service.get_interacting_addresses()
            
            # Verify the results
            assert isinstance(addresses, set)
            assert len(addresses) == 2  # Should only have two unique addresses
            assert all(addr.lower() in addresses for addr in {
                "0x1234567890123456789012345678901234567890",
                "0xabcdef0123456789abcdef0123456789abcdef01"
            })
            print("Successfully handled duplicate addresses!")
    except Exception as e:
        print(f"Error during duplicate handling test: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_real_dune_api():
    """Test real Dune API call without mocks"""
    try:
        print("\nMaking real Dune API call...")
        addresses = await dune_service.get_interacting_addresses()
        
        print(f"\nReceived {len(addresses)} unique addresses")
        if len(addresses) > 0:
            print("\nSample addresses (first 5):")
            for addr in list(addresses)[:5]:
                print(f"  - {addr}")
        
        assert isinstance(addresses, set)
        print("\nAPI call successful!")
        return addresses
    except Exception as e:
        print(f"\nError during real API call: {str(e)}")
        raise

async def main():
    """Run the real API test"""
    await test_real_dune_api()

if __name__ == "__main__":
    asyncio.run(main()) 