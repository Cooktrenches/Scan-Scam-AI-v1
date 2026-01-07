"""
Test InsightX API with correct URL
"""
import httpx
import json

api_key = "c9e02789-6954-4909-8474-86f4234fa41b"
test_token = "CJuTJ9CrNMtNyupYbgRLRNJDuRpiBGZAc5uS64QQpump"

print("=" * 60)
print("Testing InsightX API (Correct URL)")
print("=" * 60)

client = httpx.Client(timeout=30.0)
base_url = "https://api.insightx.network"

# Test endpoints for Solana
endpoints = {
    "Distribution Metrics": f"/bubblemaps/v1/solana/{test_token}/metrics/distribution",
    "Sniper Metrics": f"/bubblemaps/v1/solana/{test_token}/metrics/sniper",
    "Cluster Metrics": f"/bubblemaps/v1/solana/{test_token}/metrics/cluster",
    "Token Scanner": f"/scanner/v1/tokens/solana/{test_token}",
}

headers = {
    "X-API-Key": api_key,
    "accept": "application/json"
}

for name, endpoint in endpoints.items():
    url = f"{base_url}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    try:
        response = client.get(url, headers=headers)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"[OK] SUCCESS!")
            print(f"Response: {json.dumps(data, indent=2)[:1000]}")
        else:
            print(f"Response: {response.text[:500]}")

    except Exception as e:
        print(f"Error: {e}")

client.close()
print("\n" + "=" * 60)
print("Tests completed!")
print("=" * 60)
