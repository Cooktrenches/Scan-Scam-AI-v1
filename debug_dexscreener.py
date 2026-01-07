"""Debug DexScreener response for BUDZBURN"""
import httpx
import json

token_mint = "E2ztpQ8G5pvwZrqLVNQAL14rSWWcaagvD1dDTyvppump"

print("Fetching from DexScreener...")
url = f"https://api.dexscreener.com/latest/dex/tokens/{token_mint}"

client = httpx.Client(timeout=30.0)
response = client.get(url)

if response.status_code == 200:
    data = response.json()

    if 'pairs' in data and len(data['pairs']) > 0:
        pair = data['pairs'][0]

        print("\n=== INFO SECTION ===")
        info = pair.get('info', {})
        print(json.dumps(info, indent=2))

        print("\n=== SOCIALS ===")
        socials = info.get('socials', [])
        for social in socials:
            print(f"  {social}")

        print("\n=== WEBSITES ===")
        websites = info.get('websites', [])
        for website in websites:
            print(f"  {website}")

    else:
        print("No pairs found!")
else:
    print(f"Error: {response.status_code}")

client.close()
