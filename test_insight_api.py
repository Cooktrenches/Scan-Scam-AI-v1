"""
Test script to identify which API this key belongs to
"""
import httpx

api_key = "c9e02789-6954-4909-8474-86f4234fa41b"
test_token = "CJuTJ9CrNMtNyupYbgRLRNJDuRpiBGZAc5uS64QQpump"

print("=" * 60)
print("Testing Insight API")
print("=" * 60)

client = httpx.Client(timeout=30.0)

# Test 1: Shyft API
print("\n1. Testing Shyft API...")
try:
    url = f"https://api.shyft.to/sol/v1/token/get_info?network=mainnet-beta&token_address={test_token}"
    headers = {"x-api-key": api_key}
    response = client.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("[OK] SHYFT API WORKS!")
        print(f"Response: {response.json()}")
    else:
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Birdeye API
print("\n2. Testing Birdeye API...")
try:
    url = f"https://public-api.birdeye.so/defi/token_overview?address={test_token}"
    headers = {"X-API-KEY": api_key}
    response = client.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("[OK] BIRDEYE API WORKS!")
        print(f"Response: {response.json()}")
    else:
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: QuickNode API
print("\n3. Testing QuickNode API...")
try:
    url = f"https://api.quicknode.com/token/{test_token}"
    headers = {"x-api-key": api_key}
    response = client.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("[OK] QUICKNODE API WORKS!")
        print(f"Response: {response.json()}")
    else:
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

# Test 4: Generic test with common endpoints
print("\n4. Testing generic endpoints...")
apis_to_test = [
    ("Shyft Holders", f"https://api.shyft.to/sol/v1/token/holders?network=mainnet-beta&token_address={test_token}", {"x-api-key": api_key}),
    ("Shyft Transactions", f"https://api.shyft.to/sol/v1/transaction/history?network=mainnet-beta&account={test_token}", {"x-api-key": api_key}),
]

for name, url, headers in apis_to_test:
    try:
        response = client.get(url, headers=headers)
        if response.status_code == 200:
            print(f"[OK] {name} works!")
            data = response.json()
            print(f"   Keys: {list(data.keys())[:5]}")
    except Exception:
        pass

client.close()
print("\n" + "=" * 60)
print("Tests completed!")
print("=" * 60)
