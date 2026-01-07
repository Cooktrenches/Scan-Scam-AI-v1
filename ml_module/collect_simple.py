"""
Simple token collector - NO emojis for Windows compatibility
Collects tokens from Pump.fun and labels them as RUG or SAFE
"""
import asyncio
import httpx
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))
from feature_extractor import TokenFeatureExtractor

class SimpleCollector:
    def __init__(self):
        self.dataset_dir = Path(__file__).parent / "dataset"
        self.dataset_dir.mkdir(exist_ok=True)
        self.client = httpx.AsyncClient(timeout=30.0)
        self.extractor = TokenFeatureExtractor()

    async def fetch_tokens(self, max_tokens: int = 200):
        """Fetch tokens from Pump.fun API"""
        print(f"\n[*] Fetching {max_tokens} tokens from Pump.fun...")

        all_tokens = []
        batch_size = 50
        offset = 0

        while len(all_tokens) < max_tokens:
            try:
                response = await self.client.get(
                    "https://frontend-api-v2.pump.fun/coins",
                    params={
                        "offset": offset,
                        "limit": batch_size,
                        "sort": "created_timestamp",
                        "order": "DESC",
                        "includeNsfw": "false"
                    }
                )

                if response.status_code != 200:
                    print(f"[X] API Error: {response.status_code}")
                    break

                batch = response.json()
                if not batch:
                    break

                all_tokens.extend(batch)
                offset += batch_size
                print(f"[*] Fetched {len(all_tokens)}/{max_tokens} tokens...")

            except Exception as e:
                print(f"[X] Error: {e}")
                break

        print(f"[OK] Total tokens fetched: {len(all_tokens)}")
        return all_tokens[:max_tokens]

    async def verify_token_status(self, token_data: dict):
        """Check if token is RUG or SAFE via DexScreener"""
        try:
            mint = token_data.get("mint")
            response = await self.client.get(
                f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
            )

            if response.status_code == 200:
                data = response.json()
                pairs = data.get("pairs", [])
                if pairs:
                    return pairs[0].get("fdv", 0)  # Fully diluted valuation
            return 0
        except:
            return 0

    def label_token(self, token_data: dict, current_mcap: float):
        """Label token as RUG (1) or SAFE (0)"""
        mint = token_data.get("mint", "")
        initial_mcap = token_data.get("usd_market_cap", 0)
        created_ts = token_data.get("created_timestamp", 0)

        # Calculate age in hours
        age_hours = (datetime.now().timestamp() * 1000 - created_ts) / 3600000 if created_ts > 0 else 0

        # RUG detection
        is_rug = False
        reason = ""

        # Dead token (old + near-zero mcap)
        if age_hours > 24 and current_mcap < 500:
            is_rug = True
            reason = f"Dead token: {age_hours:.0f}h old, mcap=${current_mcap:.0f}"

        # Crashed token
        elif age_hours > 6 and current_mcap < 1000:
            is_rug = True
            reason = f"Crashed: {age_hours:.0f}h old, mcap=${current_mcap:.0f}"

        # Price dumped hard
        elif initial_mcap > 5000 and current_mcap < initial_mcap * 0.1:
            is_rug = True
            reason = f"Dumped >90%: ${initial_mcap:.0f} -> ${current_mcap:.0f}"

        # SAFE if still active
        elif current_mcap > 5000:
            is_rug = False
            reason = f"Active: mcap=${current_mcap:.0f}"

        # Too early to judge
        elif age_hours < 2:
            is_rug = False
            reason = "Too early to judge"

        else:
            # Default: stable mid-cap
            is_rug = False
            reason = f"Stable: mcap=${current_mcap:.0f}"

        label = 1 if is_rug else 0
        return label, reason

    async def collect_and_label(self, num_tokens: int = 200):
        """Main collection process"""
        print("\n" + "="*80)
        print("PUMP.FUN TOKEN COLLECTOR")
        print("="*80)
        print(f"\n[*] Starting collection of {num_tokens} tokens...")
        print("[*] This will take 5-10 minutes")
        print("[*] Press Ctrl+C to stop\n")

        # Fetch tokens
        tokens = await self.fetch_tokens(num_tokens)
        if not tokens:
            print("[X] No tokens fetched!")
            return

        # Process each token
        collected_features = []
        rug_count = 0
        safe_count = 0

        print(f"\n[*] Processing {len(tokens)} tokens...\n")

        for i, token in enumerate(tokens):
            mint = token.get("mint")
            if not mint:
                continue

            try:
                # Show progress
                print(f"[{i+1}/{len(tokens)}] Processing {mint[:8]}...")

                # Get current market cap
                current_mcap = await self.verify_token_status(token)

                # Label the token
                label, reason = self.label_token(token, current_mcap)

                # Extract features
                features = await self.extractor.extract_all_features(mint)

                if features:
                    features['label'] = label
                    features['label_reason'] = reason
                    features['collected_at'] = datetime.now().isoformat()

                    collected_features.append(features)

                    if label == 1:
                        rug_count += 1
                        print(f"    -> RUG: {reason}")
                    else:
                        safe_count += 1
                        print(f"    -> SAFE: {reason}")
                else:
                    print(f"    -> SKIP: Could not extract features")

                # Small delay to avoid rate limits
                await asyncio.sleep(1)

            except KeyboardInterrupt:
                print("\n[!] Stopped by user")
                break
            except Exception as e:
                print(f"    -> ERROR: {e}")
                continue

        # Save results
        if collected_features:
            import pandas as pd

            df_new = pd.DataFrame(collected_features)
            csv_path = self.dataset_dir / "features.csv"

            # Merge with existing data
            try:
                df_existing = pd.read_csv(csv_path)
                df = pd.concat([df_existing, df_new], ignore_index=True)
                df = df.drop_duplicates(subset=['token_mint'], keep='last')
            except FileNotFoundError:
                df = df_new

            df.to_csv(csv_path, index=False)

            print("\n" + "="*80)
            print("COLLECTION COMPLETE!")
            print("="*80)
            print(f"New tokens collected: {len(collected_features)}")
            print(f"  - RUG: {rug_count}")
            print(f"  - SAFE: {safe_count}")
            print(f"\nTotal dataset size: {len(df)} tokens")
            print(f"  - RUG: {(df['label']==1).sum()}")
            print(f"  - SAFE: {(df['label']==0).sum()}")
            print(f"\nSaved to: {csv_path}")
            print("\n[*] Next step: Run 'python train_with_my_data.py' to retrain the model")
            print("="*80)
        else:
            print("\n[X] No tokens collected!")

        await self.client.aclose()

async def main():
    print("="*80)
    print("SIMPLE TOKEN COLLECTOR FOR ML TRAINING")
    print("="*80)

    num = input("\nHow many tokens to collect (default: 200)? ")
    num_tokens = int(num) if num.strip() else 200

    collector = SimpleCollector()
    await collector.collect_and_label(num_tokens)

if __name__ == "__main__":
    asyncio.run(main())
