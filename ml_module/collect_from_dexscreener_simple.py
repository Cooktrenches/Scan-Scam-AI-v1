"""
Windows-compatible token collector using DexScreener API
NO emojis - pure ASCII for Windows compatibility
Collects tokens and labels them as RUG or SAFE for ML training
"""
import asyncio
import httpx
import json
import sys
from pathlib import Path
from datetime import datetime
import time

sys.path.append(str(Path(__file__).parent.parent))
from feature_extractor import TokenFeatureExtractor


class SimpleCollectorDex:
    def __init__(self):
        self.dataset_dir = Path(__file__).parent / "dataset"
        self.dataset_dir.mkdir(exist_ok=True)
        self.client = httpx.AsyncClient(timeout=60.0)
        self.extractor = TokenFeatureExtractor()

    async def fetch_tokens_from_dexscreener(self, max_tokens: int = 200):
        """Fetch Solana tokens from DexScreener using multiple strategies"""
        print(f"\n[*] Fetching {max_tokens} tokens from DexScreener...")
        print("[*] Using multiple search strategies...\n")

        all_tokens = []
        seen_addresses = set()

        # Strategy 1: Search for popular Solana keywords (expanded list)
        search_terms = [
            "pump", "solana", "pepe", "meme", "inu", "doge", "shib", "wojak", "chad",
            "token", "coin", "moon", "elon", "cat", "dog", "frog", "ape", "nft",
            "ai", "bot", "defi", "dao", "web3", "meta", "trump", "biden", "usa",
            "japan", "anime", "game", "play", "earn", "stake", "farm", "yield",
            "btc", "eth", "bnb", "xrp", "ada", "link", "uni", "aave", "snx",
            "baby", "mini", "mega", "ultra", "super", "hyper", "turbo", "rocket",
            "lambo", "diamond", "gem", "gold", "silver", "platinum", "based", "giga"
        ]

        for term in search_terms:
            if len(all_tokens) >= max_tokens:
                break

            try:
                print(f"[*] Searching for '{term}' tokens...")
                response = await self.client.get(
                    f"https://api.dexscreener.com/latest/dex/search/?q={term}",
                    headers={"Accept": "application/json"}
                )

                if response.status_code == 200:
                    data = response.json()
                    pairs = data.get("pairs", [])

                    for pair in pairs:
                        if len(all_tokens) >= max_tokens:
                            break

                        # Only get Solana tokens
                        if pair.get("chainId") != "solana":
                            continue

                        base_token = pair.get("baseToken", {})
                        token_address = base_token.get("address")

                        if not token_address or token_address in seen_addresses:
                            continue

                        seen_addresses.add(token_address)

                        # Extract token data
                        token_data = {
                            "mint": token_address,
                            "name": base_token.get("name", "Unknown"),
                            "symbol": base_token.get("symbol", "???"),
                            "priceUsd": pair.get("priceUsd", "0"),
                            "volume_24h": pair.get("volume", {}).get("h24", 0),
                            "priceChange_24h": pair.get("priceChange", {}).get("h24", 0),
                            "liquidity": pair.get("liquidity", {}).get("usd", 0),
                            "fdv": pair.get("fdv", 0),
                            "pairCreatedAt": pair.get("pairCreatedAt", 0),
                            "dexId": pair.get("dexId", ""),
                        }

                        all_tokens.append(token_data)

                    print(f"    -> Found {len(pairs)} pairs, collected {len(all_tokens)} unique tokens so far")

                elif response.status_code == 429:
                    print(f"[!] Rate limited, waiting 10 seconds...")
                    await asyncio.sleep(10)
                else:
                    print(f"[X] API Error {response.status_code} for '{term}'")

                # Small delay between searches to avoid rate limiting
                await asyncio.sleep(2)

            except Exception as e:
                print(f"[X] Error searching '{term}': {e}")
                continue

        print(f"\n[OK] Total unique tokens collected: {len(all_tokens)}")
        return all_tokens

    def label_token(self, token_data: dict):
        """Label token as RUG (1) or SAFE (0) based on market behavior"""
        try:
            mint = token_data.get("mint", "")
            fdv = float(token_data.get("fdv", 0))
            liquidity = float(token_data.get("liquidity", 0))
            volume_24h = float(token_data.get("volume_24h", 0))
            price_change_24h = float(token_data.get("priceChange_24h", 0))
            created_at = token_data.get("pairCreatedAt", 0)

            # Calculate age in hours
            if created_at > 0:
                age_hours = (time.time() * 1000 - created_at) / 3600000
            else:
                age_hours = 0

            is_rug = False
            reason = ""

            # RUG DETECTION CRITERIA

            # 1. Dead token (old + near-zero value)
            if age_hours > 24 and fdv < 500:
                is_rug = True
                reason = f"Dead token: {age_hours:.0f}h old, FDV=${fdv:.0f}"

            # 2. Crashed hard (older + very low FDV)
            elif age_hours > 6 and fdv < 1000:
                is_rug = True
                reason = f"Crashed: {age_hours:.0f}h old, FDV=${fdv:.0f}"

            # 3. Price dumped >80% in 24h
            elif price_change_24h < -80:
                is_rug = True
                reason = f"Dumped {price_change_24h:.0f}% in 24h"

            # 4. No liquidity (abandoned)
            elif age_hours > 12 and liquidity < 500:
                is_rug = True
                reason = f"No liquidity: ${liquidity:.0f}"

            # 5. No volume (dead)
            elif age_hours > 12 and volume_24h < 100:
                is_rug = True
                reason = f"No volume: ${volume_24h:.0f}/24h"

            # SAFE CRITERIA

            # 1. Active with good metrics
            elif fdv > 10000 and liquidity > 5000 and price_change_24h > -30:
                is_rug = False
                reason = f"Active: FDV=${fdv:.0f}, stable price"

            # 2. Too early to judge (give benefit of doubt)
            elif age_hours < 2:
                is_rug = False
                reason = "Too early (< 2h old)"

            # 3. Moderate metrics, not crashing
            elif fdv > 5000 and price_change_24h > -50:
                is_rug = False
                reason = f"Stable: FDV=${fdv:.0f}"

            # 4. Has liquidity and volume
            elif liquidity > 2000 and volume_24h > 1000:
                is_rug = False
                reason = f"Trading: Liq=${liquidity:.0f}, Vol=${volume_24h:.0f}"

            # Default: unclear
            else:
                is_rug = False
                reason = f"Uncertain: FDV=${fdv:.0f}, Age={age_hours:.1f}h"

            label = 1 if is_rug else 0
            return label, reason

        except Exception as e:
            print(f"[X] Error labeling token: {e}")
            return -1, f"ERROR: {str(e)}"

    async def collect_and_label(self, num_tokens: int = 200):
        """Main collection process"""
        print("\n" + "="*80)
        print("DEXSCREENER TOKEN COLLECTOR FOR ML TRAINING")
        print("="*80)
        print(f"\n[*] Collecting {num_tokens} tokens from DexScreener...")
        print("[*] This will take 10-15 minutes")
        print("[*] Press Ctrl+C to stop\n")

        # Fetch tokens from DexScreener
        tokens = await self.fetch_tokens_from_dexscreener(num_tokens)

        if not tokens:
            print("\n[X] No tokens fetched!")
            print("[!] DexScreener may be rate limiting or API is down")
            print("[!] Try again in a few minutes")
            await self.client.aclose()
            return

        # Process each token
        collected_features = []
        rug_count = 0
        safe_count = 0
        error_count = 0

        print(f"\n[*] Processing {len(tokens)} tokens...\n")

        for i, token in enumerate(tokens):
            mint = token.get("mint")
            if not mint:
                continue

            try:
                # Show progress
                symbol = token.get("symbol", "???")
                print(f"[{i+1}/{len(tokens)}] Processing {symbol} ({mint[:8]}...)")

                # Label the token FIRST (before extracting features)
                label, reason = self.label_token(token)

                if label == -1:
                    print(f"    -> ERROR: {reason}")
                    error_count += 1
                    continue

                # Extract ML features
                print(f"    -> Extracting features...")
                features = await self.extractor.extract_all_features(mint)

                if features:
                    # Add label and metadata
                    features['label'] = label
                    features['label_reason'] = reason
                    features['collected_at'] = datetime.now().isoformat()

                    collected_features.append(features)

                    if label == 1:
                        rug_count += 1
                        print(f"    -> [RUG] {reason}")
                    else:
                        safe_count += 1
                        print(f"    -> [SAFE] {reason}")
                else:
                    print(f"    -> SKIP: Could not extract features")
                    error_count += 1

                # Small delay to avoid overwhelming APIs
                await asyncio.sleep(2)

            except KeyboardInterrupt:
                print("\n[!] Stopped by user")
                break
            except Exception as e:
                print(f"    -> ERROR: {e}")
                error_count += 1
                continue

        # Save results
        if collected_features:
            import pandas as pd

            df_new = pd.DataFrame(collected_features)
            csv_path = self.dataset_dir / "features.csv"

            # Merge with existing data
            try:
                df_existing = pd.read_csv(csv_path)
                print(f"\n[*] Found existing dataset with {len(df_existing)} tokens")
                df = pd.concat([df_existing, df_new], ignore_index=True)
                # Remove duplicates by token_mint
                df = df.drop_duplicates(subset=['token_mint'], keep='last')
                print(f"[*] After removing duplicates: {len(df)} tokens")
            except FileNotFoundError:
                print(f"\n[*] Creating new dataset file")
                df = df_new

            df.to_csv(csv_path, index=False)

            print("\n" + "="*80)
            print("COLLECTION COMPLETE!")
            print("="*80)
            print(f"New tokens collected: {len(collected_features)}")
            print(f"  - RUG: {rug_count}")
            print(f"  - SAFE: {safe_count}")
            print(f"  - Errors: {error_count}")
            print(f"\nTotal dataset size: {len(df)} tokens")
            print(f"  - RUG: {(df['label']==1).sum()}")
            print(f"  - SAFE: {(df['label']==0).sum()}")
            print(f"\nSaved to: {csv_path}")
            print("\n[*] Next step: Run 'python train_with_my_data.py' to retrain the model")
            print("="*80)
        else:
            print("\n[X] No tokens collected!")
            print(f"[!] Errors: {error_count}")

        await self.client.aclose()


async def main():
    print("="*80)
    print("DEXSCREENER TOKEN COLLECTOR (Windows Compatible)")
    print("="*80)
    print("\nThis script will:")
    print("1. Fetch tokens from DexScreener API")
    print("2. Extract ML features for each token")
    print("3. Auto-label as RUG or SAFE")
    print("4. Save to dataset/features.csv")
    print("\n" + "="*80)

    # Accept command-line argument or use default
    if len(sys.argv) > 1:
        try:
            num_tokens = int(sys.argv[1])
            print(f"\n[*] Collecting {num_tokens} tokens (from command-line argument)")
        except ValueError:
            print("\n[!] Invalid number provided, using default: 200")
            num_tokens = 200
    else:
        num = input("\nHow many tokens to collect (default: 200)? ")
        num_tokens = int(num) if num.strip() and num.strip().isdigit() else 200

    collector = SimpleCollectorDex()
    await collector.collect_and_label(num_tokens)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[!] Collection stopped by user")
    except Exception as e:
        print(f"\n[X] Fatal error: {e}")
        import traceback
        traceback.print_exc()
