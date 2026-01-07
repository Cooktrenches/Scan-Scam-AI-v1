"""Test Pump.fun metadata retrieval"""
from liquidity_analyzer import LiquidityAnalyzer

# Token BUDZBURN
token_mint = "E2ztpQ8G5pvwZrqLVNQAL14rSWWcaagvD1dDTyvppump"

print("=" * 60)
print("TEST PUMP.FUN METADATA RETRIEVAL")
print("=" * 60)
print(f"\nToken: {token_mint}\n")

analyzer = LiquidityAnalyzer()

print("[1/2] Fetching token data with Pump.fun fallback...")
token_data = analyzer.get_token_data(token_mint)

if token_data:
    print("\n[OK] Token data retrieved!")
    print("\n--- SOCIAL METADATA ---")
    print(f"Twitter:     {token_data.get('twitter', 'NOT FOUND')}")
    print(f"Telegram:    {token_data.get('telegram', 'NOT FOUND')}")
    print(f"Website:     {token_data.get('website', 'NOT FOUND')}")
    print(f"Description: {token_data.get('description', 'NOT FOUND')[:100]}...")
    print(f"Creator:     {token_data.get('creator', 'NOT FOUND')}")

    print("\n--- MARKET DATA ---")
    print(f"Name:        {token_data.get('name')}")
    print(f"Symbol:      {token_data.get('symbol')}")
    print(f"Market Cap:  ${token_data.get('usd_market_cap', 0):,.2f}")
    print(f"Price:       ${token_data.get('price', 0):.8f}")
    print(f"Liquidity:   ${token_data.get('liquidity', 0):,.2f}")

    # Check if social data is present
    has_socials = any([
        token_data.get('twitter'),
        token_data.get('telegram'),
        token_data.get('website')
    ])

    if has_socials:
        print("\n[OK] SUCCESS! Social metadata retrieved from Pump.fun!")
    else:
        print("\n[!] WARNING: No social metadata found")

else:
    print("\n[ERROR] Could not retrieve token data")

analyzer.close()
print("\n" + "=" * 60)
