"""
Data Collector - Collects historical token data for ML training
Fetches confirmed rugs and successful tokens from various sources
"""

import json
import httpx
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class HistoricalDataCollector:
    """Collects historical token data for ML training"""

    def __init__(self):
        self.dataset_dir = Path(__file__).parent / "dataset"
        self.dataset_dir.mkdir(exist_ok=True)

        self.rugs_file = self.dataset_dir / "rugs.json"
        self.success_file = self.dataset_dir / "success.json"

        self.client = httpx.AsyncClient(timeout=30.0)

    async def collect_pump_fun_tokens(self, limit: int = 1000) -> List[Dict]:
        """
        Collect tokens from Pump.fun platform

        Args:
            limit: Number of tokens to collect

        Returns:
            List of token data
        """
        console.print(f"[cyan]Collecting {limit} tokens from Pump.fun...")

        all_tokens = []
        offset = 0
        batch_size = 50

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Fetching tokens...", total=limit)

            while len(all_tokens) < limit:
                try:
                    response = await self.client.get(
                        "https://frontend-api-v2.pump.fun/coins",
                        params={
                            "offset": offset,
                            "limit": batch_size,
                            "sort": "created_timestamp",
                            "order": "DESC"
                        }
                    )

                    if response.status_code != 200:
                        console.print(f"[red]Error: {response.status_code}")
                        break

                    batch = response.json()
                    if not batch:
                        break

                    all_tokens.extend(batch)
                    offset += batch_size
                    progress.update(task, completed=len(all_tokens))

                    await asyncio.sleep(0.5)  # Rate limiting

                except Exception as e:
                    console.print(f"[red]Error fetching batch: {e}")
                    break

        console.print(f"[green]Collected {len(all_tokens)} tokens")
        return all_tokens[:limit]

    async def analyze_token_outcome(self, token: Dict) -> str:
        """
        Analyze if a token is a rug, success, or safe

        Args:
            token: Token data

        Returns:
            "rug", "success", or "safe"
        """
        mint_address = token.get("mint")

        try:
            # Get historical price data from DexScreener
            response = await self.client.get(
                f"https://api.dexscreener.com/latest/dex/tokens/{mint_address}"
            )

            if response.status_code != 200:
                return "unknown"

            data = response.json()
            pairs = data.get("pairs", [])

            if not pairs:
                return "unknown"

            pair = pairs[0]

            # Extract metrics
            market_cap = float(pair.get("marketCap", 0))
            liquidity = float(pair.get("liquidity", {}).get("usd", 0))
            price_change_24h = float(pair.get("priceChange", {}).get("h24", 0))

            # Classification logic
            # RUG: Market cap dropped >90% or liquidity < $100
            if market_cap < 1000 or liquidity < 100:
                if price_change_24h < -90:
                    return "rug"

            # SUCCESS: Market cap > $5M and sustained
            if market_cap > 5_000_000 and liquidity > 50_000:
                return "success"

            # SAFE: Moderate, stable token
            if market_cap > 50_000 and liquidity > 5_000:
                return "safe"

            return "unknown"

        except Exception as e:
            console.print(f"[yellow]Error analyzing {mint_address}: {e}")
            return "unknown"

    async def classify_and_save_tokens(self, tokens: List[Dict]):
        """
        Classify tokens as rug/success/safe and save to files

        Args:
            tokens: List of token data
        """
        rugs = []
        successes = []
        safe_tokens = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Classifying tokens...", total=len(tokens))

            for token in tokens:
                outcome = await self.analyze_token_outcome(token)

                if outcome == "rug":
                    rugs.append(token)
                elif outcome == "success":
                    successes.append(token)
                elif outcome == "safe":
                    safe_tokens.append(token)

                progress.update(task, advance=1)
                await asyncio.sleep(0.3)  # Rate limiting for DexScreener

        # Save to files
        self._save_json(self.rugs_file, rugs)
        self._save_json(self.success_file, successes)

        console.print(f"\n[green]Classification Complete:")
        console.print(f"  [red]Rugs: {len(rugs)}")
        console.print(f"  [green]Success: {len(successes)}")
        console.print(f"  [yellow]Safe: {len(safe_tokens)}")

    def _save_json(self, filepath: Path, data: List[Dict]):
        """Save data to JSON file"""
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        console.print(f"[green]Saved {len(data)} tokens to {filepath.name}")

    async def load_existing_datasets(self) -> Dict[str, List[Dict]]:
        """Load existing datasets"""
        datasets = {}

        if self.rugs_file.exists():
            with open(self.rugs_file, "r") as f:
                datasets["rugs"] = json.load(f)
        else:
            datasets["rugs"] = []

        if self.success_file.exists():
            with open(self.success_file, "r") as f:
                datasets["success"] = json.load(f)
        else:
            datasets["success"] = []

        return datasets

    async def collect_training_data(self, num_tokens: int = 500):
        """
        Main method to collect training data

        Args:
            num_tokens: Number of tokens to collect and classify
        """
        console.print("[bold cyan]=== Historical Data Collection ===[/]")
        console.print(f"Target: {num_tokens} tokens\n")

        # Collect tokens
        tokens = await self.collect_pump_fun_tokens(limit=num_tokens)

        # Classify and save
        await self.classify_and_save_tokens(tokens)

        # Summary
        datasets = await self.load_existing_datasets()
        console.print(f"\n[bold green]Dataset Summary:")
        console.print(f"  Total Rugs: {len(datasets['rugs'])}")
        console.print(f"  Total Success: {len(datasets['success'])}")

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


async def main():
    """Main entry point for data collection"""
    collector = HistoricalDataCollector()

    try:
        await collector.collect_training_data(num_tokens=500)
    finally:
        await collector.close()


if __name__ == "__main__":
    asyncio.run(main())
