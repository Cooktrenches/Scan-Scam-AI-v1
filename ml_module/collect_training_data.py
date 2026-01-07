"""
Collect real Pump.fun tokens for ML training
Automatically scans and labels tokens as RUG or SAFE
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import requests
import time
import pandas as pd
from datetime import datetime
import asyncio
from feature_extractor import TokenFeatureExtractor

class TokenDataCollector:
    """Collects and labels real token data for ML training"""

    def __init__(self):
        self.api_url = "http://localhost:5000/api/scan"
        self.pump_api = "https://frontend-api.pump.fun"
        self.collected_data = []
        self.extractor = TokenFeatureExtractor()

    def get_recent_tokens(self, limit=100):
        """Get recent tokens from Pump.fun"""
        try:
            response = requests.get(
                f"{self.pump_api}/coins",
                params={"limit": limit, "offset": 0},
                timeout=30
            )

            if response.status_code == 200:
                tokens = response.json()
                print(f"[OK] Fetched {len(tokens)} recent tokens from Pump.fun")
                return tokens
            else:
                print(f"[X] Failed to fetch tokens: {response.status_code}")
                return []
        except Exception as e:
            print(f"[X] Error fetching tokens: {e}")
            return []

    def label_token(self, token_data, scan_result):
        """
        Automatically label token as RUG or SAFE based on criteria

        RUG indicators:
        - Market cap dropped >90% from ATH
        - Token age >24h and mcap <$1000
        - Bonding curve complete but price crashed
        - Creator has rugged before (rug_percentage > 50%)

        SAFE indicators:
        - Market cap growing or stable
        - Active trading volume
        - Bonding curve not complete yet (still early)
        - Good social presence
        """
        try:
            mint = token_data.get("mint")
            mcap = token_data.get("usd_market_cap", 0)
            created_ts = token_data.get("created_timestamp", 0)
            complete = token_data.get("complete", False)
            raydium_pool = token_data.get("raydium_pool")

            # Calculate token age in hours
            age_hours = (time.time() - created_ts/1000) if created_ts > 0 else 0

            # Get price change
            price_change = token_data.get("priceChange", {})
            change_24h = price_change.get("h24", 0) if isinstance(price_change, dict) else 0

            # RUG detection criteria
            is_rug = False
            rug_reason = []

            # CRITICAL: Dead token (mcap near zero after launch)
            if age_hours > 24 and mcap < 500:
                is_rug = True
                rug_reason.append(f"Dead token: {age_hours:.0f}h old, mcap=${mcap:.0f}")

            # STRONG: Bonding complete but crashed hard
            if complete and raydium_pool and mcap < 2000:
                is_rug = True
                rug_reason.append(f"Bonding complete but rugged: mcap=${mcap:.0f}")

            # STRONG: Price dumped >90% in 24h
            if change_24h < -90:
                is_rug = True
                rug_reason.append(f"Price dump: {change_24h:.0f}% in 24h")

            # Get scan analysis if available
            if scan_result:
                creator_analysis = scan_result.get("detailed_analysis", {}).get("creator_analysis", {})
                rug_pct = creator_analysis.get("rug_percentage", 0)

                # Serial rugger
                if rug_pct > 60:
                    is_rug = True
                    rug_reason.append(f"Serial rugger: {rug_pct:.0f}% previous rugs")

            # SAFE criteria (if not already marked as rug)
            if not is_rug:
                # Growing token
                if mcap > 10000 and change_24h > -20:
                    return 0, "SAFE: Active token with stable price"

                # Very new token (give benefit of doubt)
                if age_hours < 2:
                    return 0, "SAFE: Too early to judge (< 2h old)"

                # Moderate mcap and not crashing
                if mcap > 5000 and change_24h > -50:
                    return 0, "SAFE: Stable mid-cap token"

            # Return label
            if is_rug:
                return 1, "RUG: " + " | ".join(rug_reason)
            else:
                return 0, "SAFE: No rug indicators detected"

        except Exception as e:
            print(f"[X] Error labeling token: {e}")
            return -1, f"ERROR: {str(e)}"

    async def collect_token_data(self, mint_address, token_data):
        """Collect features for a single token"""
        try:
            print(f"\n[*] Processing {mint_address[:8]}...")

            # Extract ML features
            features = await self.extractor.extract_all_features(mint_address)

            if not features:
                print(f"[X] Could not extract features for {mint_address[:8]}")
                return None

            # Get full scan result for labeling
            try:
                scan_response = requests.post(
                    self.api_url,
                    json={"mint_address": mint_address},
                    timeout=60
                )
                scan_result = scan_response.json() if scan_response.status_code == 200 else None
            except:
                scan_result = None

            # Label the token
            label, reason = self.label_token(token_data, scan_result)

            if label == -1:
                print(f"[X] Failed to label: {reason}")
                return None

            # Add label and metadata
            features['label'] = label
            features['mint_address'] = mint_address
            features['collected_at'] = datetime.now().isoformat()
            features['label_reason'] = reason

            label_text = "RUG" if label == 1 else "SAFE"
            print(f"[OK] Labeled as {label_text}: {reason}")

            return features

        except Exception as e:
            print(f"[X] Error collecting data for {mint_address}: {e}")
            return None

    async def collect_batch(self, num_tokens=100):
        """Collect a batch of tokens"""
        print(f"\n{'='*80}")
        print(f"COLLECTING {num_tokens} TOKENS FOR TRAINING")
        print(f"{'='*80}\n")

        # Get recent tokens
        tokens = self.get_recent_tokens(num_tokens)

        if not tokens:
            print("[X] No tokens fetched!")
            return

        # Process each token
        collected = []
        rug_count = 0
        safe_count = 0

        for i, token in enumerate(tokens):
            mint = token.get("mint")
            if not mint:
                continue

            print(f"\nProgress: {i+1}/{len(tokens)}")

            # Collect features
            features = await self.collect_token_data(mint, token)

            if features:
                collected.append(features)

                if features['label'] == 1:
                    rug_count += 1
                else:
                    safe_count += 1

            # Don't overwhelm the API
            time.sleep(2)

        # Save to CSV
        if collected:
            df = pd.DataFrame(collected)

            # Load existing data if any
            csv_path = "dataset/features.csv"
            try:
                existing_df = pd.read_csv(csv_path)
                # Combine with new data
                df = pd.concat([existing_df, df], ignore_index=True)
                # Remove duplicates by mint_address
                df = df.drop_duplicates(subset=['mint_address'], keep='last')
            except FileNotFoundError:
                pass

            # Save
            df.to_csv(csv_path, index=False)

            print(f"\n{'='*80}")
            print(f"COLLECTION COMPLETE!")
            print(f"{'='*80}")
            print(f"New tokens collected: {len(collected)}")
            print(f"  - RUG: {rug_count}")
            print(f"  - SAFE: {safe_count}")
            print(f"\nTotal dataset size: {len(df)} tokens")
            print(f"  - RUG: {(df['label']==1).sum()}")
            print(f"  - SAFE: {(df['label']==0).sum()}")
            print(f"\nSaved to: {csv_path}")
            print(f"{'='*80}\n")
        else:
            print("\n[X] No tokens collected!")


if __name__ == "__main__":
    print("=" * 80)
    print("PUMP.FUN TOKEN DATA COLLECTOR FOR ML TRAINING")
    print("=" * 80)
    print("\nThis script will:")
    print("1. Fetch recent tokens from Pump.fun")
    print("2. Scan each token to extract features")
    print("3. Automatically label as RUG or SAFE")
    print("4. Save to dataset/features.csv for ML training")
    print("\n" + "=" * 80)

    num_tokens = int(input("\nHow many tokens to collect? (recommended: 200-500): ") or "200")

    print(f"\n[OK] Starting collection of {num_tokens} tokens...")
    print("[!] This will take a while (2-3 seconds per token)")
    print("[!] Make sure web_app.py is running on localhost:5000\n")

    collector = TokenDataCollector()

    # Run async collection (Python 3.14 compatible)
    asyncio.run(collector.collect_batch(num_tokens))

    print("\n[OK] Collection finished! Now run train_with_my_data.py to retrain the model.")
