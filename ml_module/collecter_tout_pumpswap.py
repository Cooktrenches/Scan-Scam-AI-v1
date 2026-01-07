"""
Collecteur Complet PumpSwap
Récupère TOUS les tokens depuis DexScreener PumpSwap
"""

import asyncio
import httpx
import json
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt

console = Console()


class CompletePumpSwapCollector:
    """Collecte TOUS les tokens PumpSwap"""

    def __init__(self):
        self.dataset_dir = Path(__file__).parent / "dataset"
        self.dataset_dir.mkdir(exist_ok=True)

        self.rugs_file = self.dataset_dir / "rugs.json"
        self.success_file = self.dataset_dir / "success.json"

        self.client = httpx.AsyncClient(timeout=30.0)

        # Filtres
        self.success_mcap_min = 500_000  # 500K
        self.rug_mcap_max = 20_000       # 20K

    async def fetch_all_pumpswap_tokens(self, max_pages: int = 20) -> list:
        """
        Récupère tous les tokens PumpSwap en utilisant l'API DexScreener
        avec pagination
        """
        console.print("[cyan]Récupération de TOUS les tokens PumpSwap...")
        console.print(f"[dim]Recherche jusqu'à {max_pages} pages\n")

        all_tokens = []
        seen_mints = set()

        # Méthode 1 : Recherche par DEX
        console.print("[yellow]Méthode 1 : Recherche directe pumpswap...")

        try:
            # L'API DexScreener permet de filtrer par DEX
            response = await self.client.get(
                "https://api.dexscreener.com/latest/dex/search",
                params={"q": "pumpswap"}
            )

            if response.status_code == 200:
                data = response.json()
                pairs = data.get("pairs", [])

                for pair in pairs:
                    if pair.get("chainId") == "solana":
                        dex_id = str(pair.get("dexId", "")).lower()
                        if "pump" in dex_id:
                            mint = pair.get("baseToken", {}).get("address")
                            if mint and mint not in seen_mints:
                                all_tokens.append(pair)
                                seen_mints.add(mint)

                console.print(f"[green]✓ Trouvé {len(all_tokens)} tokens")

            await asyncio.sleep(2)

        except Exception as e:
            console.print(f"[red]Erreur : {e}")

        # Méthode 2 : Recherche par variations de mots-clés
        keywords = [
            "pump.fun",
            "pump fun",
            "pumpfun",
            "solana pump",
            "pump token",
            "pump coin"
        ]

        console.print(f"\n[yellow]Méthode 2 : Recherche par mots-clés ({len(keywords)} recherches)...")

        for keyword in keywords:
            try:
                response = await self.client.get(
                    "https://api.dexscreener.com/latest/dex/search",
                    params={"q": keyword}
                )

                if response.status_code == 200:
                    data = response.json()
                    pairs = data.get("pairs", [])

                    for pair in pairs:
                        if pair.get("chainId") == "solana":
                            dex_id = str(pair.get("dexId", "")).lower()
                            if "pump" in dex_id:
                                mint = pair.get("baseToken", {}).get("address")
                                if mint and mint not in seen_mints:
                                    all_tokens.append(pair)
                                    seen_mints.add(mint)

                    console.print(f"[dim]  '{keyword}' → {len(pairs)} pairs (+{len(all_tokens)} uniques)")

                await asyncio.sleep(1.5)  # Rate limiting

            except Exception as e:
                console.print(f"[red]Erreur '{keyword}': {e}")

        console.print(f"\n[bold green]✓ Total : {len(all_tokens)} tokens PumpSwap uniques\n")
        return all_tokens

    def classify_token(self, pair: dict) -> str:
        """Classifie un token"""
        market_cap = float(pair.get("marketCap", 0) or 0)

        if market_cap >= self.success_mcap_min:
            return "SUCCESS"
        elif market_cap <= self.rug_mcap_max:
            return "RUG"
        else:
            return "SKIP"

    def format_token(self, pair: dict, classification: str) -> dict:
        """Formate les données"""
        base_token = pair.get("baseToken", {})

        # Âge
        created_at = pair.get("pairCreatedAt")
        age_hours = None
        if created_at:
            try:
                created_dt = datetime.fromtimestamp(created_at / 1000)
                age_hours = (datetime.now() - created_dt).total_seconds() / 3600
            except:
                pass

        return {
            "mint": base_token.get("address"),
            "name": base_token.get("name", "Unknown"),
            "symbol": base_token.get("symbol", "???"),
            "market_cap": pair.get("marketCap", 0),
            "price_change_24h": pair.get("priceChange", {}).get("h24", 0),
            "liquidity": pair.get("liquidity", {}).get("usd", 0),
            "age_hours": age_hours,
            "dex_url": pair.get("url", ""),
            "dex_id": pair.get("dexId", ""),
            "classification": classification,
            "collected_at": datetime.now().isoformat()
        }

    async def collect_and_classify(self, max_pages: int = 20) -> dict:
        """Collecte et classifie"""

        console.print(Panel.fit(
            "[bold cyan]COLLECTE COMPLÈTE PUMPSWAP[/]\n\n"
            "[green]SUCCESS :[/] Market Cap >= $500,000\n"
            "[red]RUG :[/] Market Cap <= $20,000",
            border_style="cyan"
        ))

        # Récupérer tous les tokens
        all_pairs = await self.fetch_all_pumpswap_tokens(max_pages)

        if not all_pairs:
            console.print("[red]Aucun token trouvé!")
            return {"rugs": [], "success": []}

        # Classifier
        console.print("[cyan]Classification...\n")

        results = {"rugs": [], "success": [], "skipped": 0}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Classification...", total=len(all_pairs))

            for pair in all_pairs:
                classification = self.classify_token(pair)

                if classification == "SUCCESS":
                    results["success"].append(self.format_token(pair, "SUCCESS"))
                elif classification == "RUG":
                    results["rugs"].append(self.format_token(pair, "RUG"))
                else:
                    results["skipped"] += 1

                progress.update(task, advance=1)

        # Résultats
        console.print(f"\n[bold cyan]Résultats :")
        console.print(f"  [red]RUGS (< $20K) : {len(results['rugs'])}")
        console.print(f"  [green]SUCCESS (> $500K) : {len(results['success'])}")
        console.print(f"  [dim]Zone grise : {results['skipped']}\n")

        return results

    def load_existing(self) -> dict:
        """Charge existants"""
        existing = {"rugs": [], "success": []}

        if self.rugs_file.exists():
            with open(self.rugs_file) as f:
                existing["rugs"] = json.load(f)

        if self.success_file.exists():
            with open(self.success_file) as f:
                existing["success"] = json.load(f)

        return existing

    def save_results(self, new_data: dict):
        """Sauvegarde"""

        # Charger existants
        existing = self.load_existing()

        # Merger
        existing_rug_mints = {t.get("mint") for t in existing["rugs"]}
        new_rugs = [t for t in new_data["rugs"] if t.get("mint") not in existing_rug_mints]
        all_rugs = existing["rugs"] + new_rugs

        existing_success_mints = {t.get("mint") for t in existing["success"]}
        new_successes = [t for t in new_data["success"] if t.get("mint") not in existing_success_mints]
        all_successes = existing["success"] + new_successes

        # Sauvegarder
        with open(self.rugs_file, "w") as f:
            json.dump(all_rugs, f, indent=2)

        with open(self.success_file, "w") as f:
            json.dump(all_successes, f, indent=2)

        # Afficher
        console.print("[bold green]✓ Sauvegardé !")
        console.print(f"  [red]rugs.json : {len(existing['rugs'])} → {len(all_rugs)} (+{len(new_rugs)})")
        console.print(f"  [green]success.json : {len(existing['success'])} → {len(all_successes)} (+{len(new_successes)})")

        # Exemples
        if new_successes:
            console.print(f"\n[green]Nouveaux SUCCESS ({len(new_successes)}) :")
            for success in new_successes[:5]:
                console.print(f"  • {success['name']} - ${success['market_cap']:,.0f}")

        if new_rugs:
            console.print(f"\n[red]Nouveaux RUGS ({len(new_rugs)}) :")
            for rug in new_rugs[:5]:
                console.print(f"  • {rug['name']} - ${rug['market_cap']:,.0f}")

        # Stats
        console.print(f"\n[bold cyan]📊 Dataset Total :")
        console.print(f"  [red]RUGS : {len(all_rugs)}")
        console.print(f"  [green]SUCCESS : {len(all_successes)}")
        console.print(f"  [yellow]TOTAL : {len(all_rugs) + len(all_successes)}")

        # Recommandation
        if len(all_rugs) >= 50 and len(all_successes) >= 50:
            console.print(f"\n[bold green]✓ Vous avez assez de données !")
            console.print(f"[yellow]→ Entraînez maintenant : python train_with_my_data.py")
        else:
            needed_rugs = max(0, 50 - len(all_rugs))
            needed_success = max(0, 50 - len(all_successes))
            if needed_rugs > 0 or needed_success > 0:
                console.print(f"\n[yellow]📌 Objectif 50+50, encore besoin de :")
                if needed_rugs > 0:
                    console.print(f"  [red]• {needed_rugs} RUGS")
                if needed_success > 0:
                    console.print(f"  [green]• {needed_success} SUCCESS")

    async def run(self):
        """Exécution"""

        console.print("[bold yellow]COLLECTEUR COMPLET PUMPSWAP[/]")
        console.print("[dim]Récupère TOUS les tokens disponibles sur DexScreener\n")

        # Demander nombre de pages
        max_pages = IntPrompt.ask(
            "Nombre de pages à explorer",
            default=20
        )

        console.print()

        # Collecter
        results = await self.collect_and_classify(max_pages)

        if not results["rugs"] and not results["success"]:
            console.print("[yellow]Aucun token trouvé correspondant aux critères")
            return

        # Sauvegarder
        console.print()
        if Confirm.ask("Sauvegarder ?"):
            self.save_results(results)

            console.print("\n" + "="*60)
            console.print(Panel.fit(
                "[bold green]✓ COLLECTE TERMINÉE ![/]",
                border_style="green"
            ))

    async def close(self):
        """Ferme client"""
        await self.client.aclose()


async def main():
    collector = CompletePumpSwapCollector()

    try:
        await collector.run()
    finally:
        await collector.close()


if __name__ == "__main__":
    asyncio.run(main())
