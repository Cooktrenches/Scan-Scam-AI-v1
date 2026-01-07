"""
Test extraction avec VRAIES features
"""
import asyncio
from feature_extractor import TokenFeatureExtractor

async def test():
    print("=" * 60)
    print("TEST EXTRACTION AVEC VRAIES FEATURES")
    print("=" * 60)

    extractor = TokenFeatureExtractor()

    # Test avec un token connu
    test_token = "7iRW57yuUXFehj5UzxvVaHCJjYCRyc2jPM2JFQq5pump"

    print(f"\nExtraction features pour: {test_token}\n")

    try:
        features = await extractor.extract_all_features(test_token)

        if features:
            print(f"[OK] {len(features)} features extraites!")

            # Montrer quelques features importantes
            print("\nFeatures importantes extraites:")
            important_keys = [
                "instant_sniper_count",
                "sniper_holdings_percentage",
                "volume_24h",
                "liquidity_usd",
                "market_cap_usd",
                "mint_authority_renounced",
                "holder_count",
                "fresh_wallet_percentage"
            ]

            for key in important_keys:
                if key in features:
                    print(f"  {key}: {features[key]}")

            print("\n[OK] Integration reussie!")
        else:
            print("[ERREUR] Aucune feature extraite")

    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()

    await extractor.close()

if __name__ == "__main__":
    asyncio.run(test())
