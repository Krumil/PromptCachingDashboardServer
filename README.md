
# FastAPI Ethereum Interaction

This project is a FastAPI application that interacts with the Ethereum blockchain to fetch, cache, and provide data related to addresses interacting with a specific staking contract.

## Project Structure

```
project_root/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── constants.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── addresses.py
│   │   └── update.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── blockchain.py
│   │   ├── cache.py
│   │   └── scheduler.py
│   └── models/
│       ├── __init__.py
│       └── request.py
│
├── abi/
│   ├── staking_contract_abi.json
│   └── prime_token_abi.json
│
├── interacting_addresses.json
├── .env
├── requirements.txt
└── README.md
```

## Features

- Fetches logs from an Ethereum staking contract.
- Extracts interacting addresses from the logs.
- Caches data from a third-party API for these addresses.
- Provides endpoints to get global data, address-specific data, and trigger updates.

## Setup

### Prerequisites

- Python 3.7+
- FastAPI
- Web3.py
- APScheduler
- aiohttp
- dotenv

## Endpoints

### Get Global Data

- **URL:** `/get_global_data`
- **Method:** `GET`
- **Description:** Fetches the total scores and prime cached for all addresses.

### Get Addresses

- **URL:** `/addresses`
- **Method:** `GET`
- **Description:** Retrieves the list of all interacting addresses.

### Get Address Info

- **URL:** `/addresses`
- **Method:** `POST`
- **Description:** Retrieves detailed information for a specific address.
- **Request Body:**
  ```json
  {
    "address": "address_here"
  }
  ```

### Update Addresses

- **URL:** `/update_addresses`
- **Method:** `POST`
- **Description:** Triggers the update process to fetch and cache data for interacting addresses.
