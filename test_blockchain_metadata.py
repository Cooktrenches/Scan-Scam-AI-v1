"""Test blockchain metadata fetching"""
from metadata_fetcher import MetadataFetcher

token_mint = "E2ztpQ8G5pvwZrqLVNQAL14rSWWcaagvD1dDTyvppump"

print("=" * 60)
print("TEST BLOCKCHAIN + IPFS METADATA RETRIEVAL")
print("=" * 60)
print(f"\nToken: {token_mint}\n")

print("[1/3] Fetching metadata from Solana blockchain...")
fetcher = MetadataFetcher()
metadata = fetcher.get_metadata(token_mint)

if metadata:
    print("\n[OK] Metadata retrieved from blockchain + IPFS!")

    print("\n--- TOKEN INFO ---")
    print(f"Name:        {metadata.get('name', 'N/A')}")
    print(f"Symbol:      {metadata.get('symbol', 'N/A')}")
    print(f"URI:         {metadata.get('uri', 'N/A')[:80]}...")

    print("\n--- SOCIAL LINKS ---")
    print(f"Twitter:     {metadata.get('twitter', 'NOT FOUND')}")
    print(f"Telegram:    {metadata.get('telegram', 'NOT FOUND')}")
    print(f"Website:     {metadata.get('website', 'NOT FOUND')}")

    print("\n--- DESCRIPTION ---")
    desc = metadata.get('description', 'N/A')
    print(f"{desc[:200]}..." if len(desc) > 200 else desc)

    # Check success
    has_socials = any([
        metadata.get('twitter'),
        metadata.get('telegram'),
        metadata.get('website')
    ])

    if has_socials:
        print("\n" + "=" * 60)
        print("[OK] SUCCESS! Found social links from blockchain!")
        print("=" * 60)
    else:
        print("\n[!] No social links found in metadata")

else:
    print("\n[ERROR] Could not retrieve metadata")

fetcher.close()
