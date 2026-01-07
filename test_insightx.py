"""
Test InsightX API endpoints
"""
import httpx
import json

api_key = "c9e02789-6954-4909-8474-86f4234fa41b"
test_token = "CJuTJ9CrNMtNyupYbgRLRNJDuRpiBGZAc5uS64QQpump"
network = "solana"  # or "mainnet"

print("=" * 60)
print("Testing InsightX API")
print("=" * 60)

client = httpx.Client(timeout=30.0)

# Common base URLs for InsightX
base_urls = [
    "https://api.insightx.network",
    "https://api.insightx.io",
    "https://insightx.network/api"
]

# Test endpoints
endpoints_to_test = [
    # Sniper metrics
    f"/bubblemaps/v1/{network}/{test_token}/sniper-metrics",
    f"/scanner/v1/tokens/{network}/{test_token}",
    f"/bubblemaps/v1/solana/{test_token}/sniper-metrics",

    # Cluster metrics
    f"/bubblemaps/v1/{network}/{test_token}/cluster-metrics",
    f"/bubblemaps/v1/solana/{test_token}/cluster-metrics",

    # Token scan
    f"/scanner/v1/tokens/solana/{test_token}",
    f"/v1/tokens/{network}/{test_token}",
]

headers = {
    "x-api-key": api_key,
    "X-API-KEY": api_key,
    "Authorization": f"Bearer {api_key}",
    "api-key": api_key
}

for base_url in base_urls:
    print(f"\n{'='*60}")
    print(f"Testing base URL: {base_url}")
    print(f"{'='*60}")

    for endpoint in endpoints_to_test:
        url = f"{base_url}{endpoint}"
        try:
            # Try with different header combinations
            for auth_header in ["x-api-key", "X-API-KEY", "Authorization"]:
                test_headers = {auth_header: headers[auth_header]}
                response = client.get(url, headers=test_headers, timeout=10.0)

                if response.status_code == 200:
                    print(f"\n[OK] SUCCESS!")
                    print(f"   URL: {url}")
                    print(f"   Header: {auth_header}")
                    print(f"   Response: {json.dumps(response.json(), indent=2)[:500]}")
                    break
                elif response.status_code not in [404, 401, 403]:
                    print(f"\n[!]  Status {response.status_code}: {url}")
                    print(f"   Response: {response.text[:200]}")
                    break
        except Exception as e:
            continue

client.close()
print("\n" + "=" * 60)
print("Tests completed!")
print("=" * 60)
