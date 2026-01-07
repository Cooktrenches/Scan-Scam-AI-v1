"""Test full scanner with BUDZBURN token"""
from main import RugDetector

token_mint = "E2ztpQ8G5pvwZrqLVNQAL14rSWWcaagvD1dDTyvppump"

print("=" * 60)
print("TEST FULL SCANNER WITH BUDZBURN TOKEN")
print("=" * 60)
print(f"\nToken: {token_mint}\n")

detector = RugDetector()

print("[1/1] Running full analysis...\n")
result = detector.analyze_token(token_mint)

print("\n" + "=" * 60)
print("SCAN RESULTS")
print("=" * 60)

print(f"\nToken: {result['token_name']} ({result['symbol']})")
print(f"Risk Score: {result['risk_score']}/100")
print(f"Risk Level: {result['risk_level']}")

print("\n--- SOCIAL LINKS ---")
print(f"Twitter:  {result['metadata'].get('twitter', 'NOT FOUND')}")
print(f"Telegram: {result['metadata'].get('telegram', 'NOT FOUND')}")
print(f"Website:  {result['metadata'].get('website', 'NOT FOUND')}")

print("\n--- MARKET DATA ---")
print(f"Market Cap: ${result['market_cap_usd']:,.2f}")
print(f"Liquidity:  ${result['liquidity_usd']:,.2f}")
print(f"Price:      ${result['price_usd']:.8f}")

print("\n--- RED FLAGS ---")
if result['red_flags']:
    for flag in result['red_flags']:
        print(f"  {flag}")
else:
    print("  None")

print("\n" + "=" * 60)

# Check success
has_socials = any([
    result['metadata'].get('twitter'),
    result['metadata'].get('telegram'),
    result['metadata'].get('website')
])

if has_socials:
    print("[OK] SUCCESS! Social links detected from blockchain!")
    print("=" * 60)
else:
    print("[!!] WARNING: No social links found")
    print("=" * 60)

detector.close()
