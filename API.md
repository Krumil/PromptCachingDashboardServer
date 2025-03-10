# PRIME Caching Dashboard API Documentation

Welcome to the PRIME Caching Dashboard API documentation! This guide will help you understand and integrate with our API endpoints.

## Getting Started

The API is RESTful and returns responses in JSON format. All endpoints are prefixed with the base URL of your deployment.

Base URL: `https://promptcachingdashboardserver.onrender.com`

## Global Data Endpoints

### Get Global Data
```http
GET /get_global_data
```
Returns aggregated statistics about the PRIME caching system, including total scores and cached amounts across all addresses.

**Example Request**
```bash
curl -X GET https://promptcachingdashboardserver.onrender.com/get_global_data
```

**Example Response**
```json
{
    "total_score": 15750,
    "total_prime_cached": 25000,
    "total_addresses": 500
}
```

## Address Endpoints

### Get All Addresses
```http
GET /addresses
```
Returns a paginated list of all addresses and their associated data. Use this endpoint to build leaderboards or display address rankings.

**Query Parameters**
- `page` (optional): Page number (default: 1, min: 1)
- `page_size` (optional): Number of items per page (default: 10, min: 1, max: 100)

**Example Request**
```bash
# Get the first page with 20 items
curl -X GET "https://promptcachingdashboardserver.onrender.com/addresses?page=1&page_size=20"
```

**Example Response**
```json
{
    "total": 500,
    "page": 1,
    "page_size": 20,
    "total_pages": 25,
    "data": [
        {
            "address": "0x1234...",
            "data": {
                "leaderboard_rank": 1,
                "merged_score_data": {
                    "prime_score": 100,
                    "community_score": 50,
                    "initialization_score": 25
                },
                "prime_amount_cached": 1000
            }
        },
        // ... more addresses
    ]
}
```

### Get Address Information
```http
POST /addresses
```
Get detailed information for specific addresses. Useful for checking multiple addresses at once.

**Request Body**
```json
{
    "addresses": [
        "0x1234567890123456789012345678901234567890",
        "0xabcdef0123456789abcdef0123456789abcdef01"
    ]
}
```

**Example Request**
```bash
curl -X POST https://promptcachingdashboardserver.onrender.com/addresses \
    -H "Content-Type: application/json" \
    -d '{"addresses": ["0x1234...", "0xabcd..."]}'
```

**Example Response**
```json
{
    "total_score": 175,
    "total_prime_cached": 2000,
    "position": 42,
    "total_users": 500,
    "addresses_processed": 2,
    "addresses_found": [
        {
            "address": "0x1234...",
            "data": {
                "leaderboard_rank": 42,
                "merged_score_data": {
                    "prime_score": 75,
                    "community_score": 25,
                    "initialization_score": 10
                }
            }
        }
        // ... more addresses
    ],
    "addresses_not_found": 0
}
```

### Search Position
```http
GET /search_position
```
Search for an address or ENS name and get its position in the leaderboard. Supports both Ethereum addresses and ENS names.

**Query Parameters**
- `query`: Ethereum address or ENS name (e.g., "vitalik.eth" or "0x1234...")

**Example Requests**
```bash
# Search by ENS name
curl -X GET "https://promptcachingdashboardserver.onrender.com/search_position?query=vitalik.eth"

# Search by address
curl -X GET "https://promptcachingdashboardserver.onrender.com/search_position?query=0x1234..."
```

**Example Response**
```json
{
    "addresses": [
        {
            "address": "0x1234...",
            "data": {
                "leaderboard_rank": 42,
                // ... other address data
            }
        }
        // ... nearby addresses
    ],
    "position": 42,
    "total_addresses": 500,
    "queried_as": "vitalik.eth",
    "resolved_address": "0x1234...",
    "next_round_number": 50
}
```

## Statistics Endpoints

### Get Cache Statistics
```http
GET /stats
```
Get comprehensive statistics about PRIME caching activity, including historical data and trends.

**Example Request**
```bash
curl -X GET https://promptcachingdashboardserver.onrender.com/stats
```

**Example Response**
```json
{
    "cache_stats": {
        "total_cached_last_24h": 5000,
        "unique_cachers_24h": 150,
        "average_cache_amount": 1000,
        "total_withdrawals": 2000,
        "active_caches": 3000
    }
}
```

## Update Endpoints

These endpoints are typically used for administrative purposes and may require authentication.

### Update Addresses
```http
POST /update_addresses
```
Triggers a background task to update the interacting addresses list. This process may take some time to complete.

**Example Request**
```bash
curl -X POST https://promptcachingdashboardserver.onrender.com/update_addresses
```

**Example Response**
```json
{
    "message": "Address update initiated"
}
```

### Update ENS Names
```http
GET /update_ens
```
Triggers an update of ENS name resolution for all tracked addresses.

**Example Request**
```bash
curl -X GET https://promptcachingdashboardserver.onrender.com/update_ens
```

**Example Response**
```json
{
    "message": "ENS update initiated"
}
```

### Recalculate Percentages
```http
POST /recalculate_percentages
```
Recalculates percentages and sorts addresses based on the latest data.

**Example Request**
```bash
curl -X POST https://promptcachingdashboardserver.onrender.com/recalculate_percentages
```

**Example Response**
```json
{
    "message": "Successfully recalculated percentages"
}
```

## ENS Endpoints

### Get ENS Name for Address
```http
GET /ens/{address}
```
Retrieve the ENS name associated with an Ethereum address.

**Parameters**
- `address`: Ethereum address (e.g., "0x1234...")

**Example Request**
```bash
curl -X GET https://promptcachingdashboardserver.onrender.com/ens/0x1234...
```

**Example Response**
```json
{
    "address": "0x1234...",
    "ens_name": "vitalik.eth"
}
```

### Get All ENS Entries
```http
GET /ens
```
Retrieve all known ENS name mappings in the system.

**Example Request**
```bash
curl -X GET https://promptcachingdashboardserver.onrender.com/ens
```

**Example Response**
```json
{
    "0x1234...": "vitalik.eth",
    "0xabcd...": "uniswap.eth",
    // ... more mappings
}
```

### Get Address by ENS Name
```http
GET /ens/reverse/{ens_name}
```
Look up an Ethereum address using an ENS name.

**Parameters**
- `ens_name`: ENS name (e.g., "vitalik.eth")

**Example Request**
```bash
curl -X GET https://promptcachingdashboardserver.onrender.com/ens/reverse/vitalik.eth
```

**Example Response**
```json
{
    "ens_name": "vitalik.eth",
    "address": "0x1234..."
}
```