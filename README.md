
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

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/fastapi-ethereum-interaction.git
   cd fastapi-ethereum-interaction
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:

   Create a `.env` file in the root directory and add any necessary environment variables. For example:

   ```env
   INFURA_API_KEY=your_infura_api_key
   ```

4. Add the ABI files:

   Ensure that `staking_contract_abi.json` and `prime_token_abi.json` are present in the `abi/` directory.

## Running the Application

1. Start the FastAPI application:

   ```bash
   uvicorn app.main:app --reload
   ```

2. The application will be available at `http://127.0.0.1:8000`.

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
