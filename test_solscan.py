"""
Test script to debug Solscan API responses
"""
from solscan_api import SolscanAPI
import json
import httpx

# Test token
token_address = "CJuTJ9CrNMtNyupYbgRLRNJDuRpiBGZAc5uS64QQpump"

print("=" * 60)
print("Testing Solscan API")
print("=" * 60)

# First test direct API call
print("\n0. Testing DIRECT API call (no wrapper)...")
from config import SOLSCAN_API_KEY
headers = {}
if SOLSCAN_API_KEY:
    headers['token'] = SOLSCAN_API_KEY
    print(f"Using API Key: {SOLSCAN_API_KEY[:20]}...")
else:
    print("No API Key configured!")

client = httpx.Client(headers=headers, timeout=10.0)
url = f"https://api.solscan.io/token/meta?token={token_address}"
print(f"Calling: {url}")
response = client.get(url)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")
client.close()

api = SolscanAPI()

# Test 1: Get token meta
print("\n1. Testing get_token_meta()...")
meta = api.get_token_meta(token_address)
print(f"Result: {json.dumps(meta, indent=2) if meta else 'None'}")

# Test 2: Get token holders
print("\n2. Testing get_token_holders()...")
holders = api.get_token_holders(token_address, limit=5)
print(f"Found {len(holders)} holders")
if holders:
    print(f"First holder: {json.dumps(holders[0], indent=2)}")

# Test 3: Get token transfers
print("\n3. Testing get_token_transfer()...")
transfers = api.get_token_transfer(token_address, limit=10)
print(f"Found {len(transfers)} transfers")
if transfers:
    print(f"First transfer: {json.dumps(transfers[0], indent=2)}")

# Test 4: Get account info for a wallet
if holders and len(holders) > 0:
    wallet = holders[0].get("owner") or holders[0].get("address")
    if wallet:
        print(f"\n4. Testing get_account_info() for {wallet[:8]}...")
        account_info = api.get_account_info(wallet)
        print(f"Result: {json.dumps(account_info, indent=2) if account_info else 'None'}")

# Test 5: Get wallet tokens
if holders and len(holders) > 0:
    wallet = holders[0].get("owner") or holders[0].get("address")
    if wallet:
        print(f"\n5. Testing get_account_tokens() for {wallet[:8]}...")
        tokens = api.get_account_tokens(wallet)
        print(f"Found {len(tokens)} tokens")
        if tokens:
            print(f"First token: {json.dumps(tokens[0], indent=2)}")

api.close()
print("\n" + "=" * 60)
print("Tests completed!")
print("=" * 60)
