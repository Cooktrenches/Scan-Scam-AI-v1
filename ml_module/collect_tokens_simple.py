"""
Collecteur Simple et Fiable - DexScreener Uniquement
Collecte tokens PumpSwap depuis DexScreener API
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


class SimpleCollector:
    """Collecteur simple utilisant seulement DexScreener"""

    def __init__(self):
        self.dataset_dir = Path(__file__).parent / "dataset"
        self.dataset_dir.mkdir(exist_ok=True)

        self.rugs_file = self.dataset_dir / "rugs.json"
        self.success_file = self.dataset_dir / "success.json"

        self.client = httpx.AsyncClient(timeout=30.0)

        # Critères (modifiables)
        self.success_mcap_min = 500_000  # 500K
        self.success_age_hours = 48

        self.rug_mcap_max = 20_000  # 20K
        self.rug_age_hours_max = 48
        self.rug_price_drop_min = 80  # -80%

    async def search_pumpswap_tokens(self) -> list:
        """Recherche tokens PumpSwap sur DexScreener"""

        console.print("[cyan]Recherche de tokens PumpSwap sur DexScreener...")

        all_pairs = []

        # Différentes recherches pour couvrir plus de tokens
        search_queries = [
            "pump",
            "pump.fun",
            "pumpswap",
            "sol pump"
        ]

        for query in search_queries:
            try:
                response = await self.client.get(
                    "https://api.dexscreener.com/latest/dex/search",
                    params={"q": query}
                )

                if response.status_code == 200:
                    data = response.json()
                    pairs = data.get("pairs", [])

                    # Filtrer: Solana + PumpSwap
                    for pair in pairs:
                        if pair.get("chainId") == "solana":
                            dex_id = str(pair.get("dexId", "")).lower()
                            # Vérifier que c'est bien PumpSwap
                            if "pump" in dex_id:
                                all_pairs.append(pair)

                    console.print(f"[dim]  '{query}' → {len(pairs)} pairs trouvées")

                await asyncio.sleep(1.5)  # Rate limiting

            except Exception as e:
                console.print(f"[yellow]Erreur recherche '{query}': {e}")

        # Dédupliquer
        unique_pairs = {}
        for pair in all_pairs:
            mint = pair.get("baseToken", {}).get("address")
            if mint and mint not in unique_pairs:
                unique_pairs[mint] = pair

        console.print(f"[green]✓ {len(unique_pairs)} tokens PumpSwap uniques trouvés\n")
        return list(unique_pairs.values())

    def classify_pair(self, pair: dict) -> str:
        """Classifie une paire en RUG, SUCCESS ou SKIP"""

        # Market data
        market_cap = float(pair.get("marketCap", 0) or 0)
        price_change_24h = float(pair.get("priceChange", {}).get("h24", 0) or 0)
        price_change_6h = float(pair.get("priceChange", {}).get("h6", 0) or 0)

        # Calculer âge
        created_at = pair.get("pairCreatedAt")
        age_hours = 999

        if created_at:
            try:
                created_dt = datetime.fromtimestamp(created_at / 1000)
                age_hours = (datetime.now() - created_dt).total_seconds() / 3600
            except:
                pass

        # CRITÈRE SUCCESS
        if market_cap >= self.success_mcap_min and age_hours >= self.success_age_hours:
            return "SUCCESS"

        # CRITÈRE RUG
        if market_cap <= self.rug_mcap_max and age_hours <= self.rug_age_hours_max:
            if price_change_24h <= -self.rug_price_drop_min or price_change_6h <= -self.rug_price_drop_min:
                return "RUG"

        return "SKIP"

    def format_token(self, pair: dict, classification: str) -> dict:
        """Formate les données du token"""
        base_token = pair.get("baseToken", {})

        return {
            "mint": base_token.get("address"),
            "name": base_token.get("name", "Unknown"),
            "symbol": base_token.get("symbol", "???"),
            "market_cap": pair.get("marketCap", 0),
            "price_change_24h": pair.get("priceChange", {}).get("h24", 0),
            "liquidity": pair.get("liquidity", {}).get("usd", 0),
            "dex_url": pair.get("url", ""),
            "dex_id": pair.get("dexId", ""),
            "classification": classification,
            "collected_at": datetime.now().isoformat()
        }

    async def collect_and_classify(self) -> dict:
        """Collecte et classifie les tokens"""

        console.print(Panel.fit(
            "[bold cyan]COLLECTEUR SIMPLE DEXSCREENER[/]\n\n"
            "[yellow]Critères SUCCESS:[/]\n"
            f"  • Market Cap > ${self.success_mcap_min:,}\n"
            f"  • Âge > {self.success_age_hours}h\n\n"
            "[yellow]Critères RUG:[/]\n"
            f"  • Market Cap < ${self.rug_mcap_max:,}\n"
            f"  • Dump en < {self.rug_age_hours_max}h\n"
            f"  • Chute > {self.rug_price_drop_min}%",
            border_style="cyan"
        ))

        # Rechercher tokens
        pairs = await self.search_pumpswap_tokens()

        if not pairs:
            console.print("[red]Aucun token trouvé!")
            return {"rugs": [], "success": []}

        # Classifier
        console.print("[cyan]Classification des tokens...\n")

        rugs = []
        successes = []
        skipped = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Analyse...", total=len(pairs))

            for pair in pairs:
                classification = self.classify_pair(pair)

                if classification == "RUG":
                    rugs.append(self.format_token(pair, "RUG"))
                elif classification == "SUCCESS":
                    successes.append(self.format_token(pair, "SUCCESS"))
                else:
                    skipped += 1

                progress.update(task, advance=1)

        # Résultats
        console.print(f"\n[bold cyan]Résultats :[/]")
        console.print(f"  [red]RUGS : {len(rugs)}")
        console.print(f"  [green]SUCCESS : {len(successes)}")
        console.print(f"  [dim]Ignorés : {skipped}\n")

        return {"rugs": rugs, "success": successes}

    def load_existing(self) -> dict:
        """Charge datasets existants"""
        existing = {"rugs": [], "success": []}

        if self.rugs_file.exists():
            with open(self.rugs_file) as f:
                existing["rugs"] = json.load(f)

        if self.success_file.exists():
            with open(self.success_file) as f:
                existing["success"] = json.load(f)

        return existing

    def save_results(self, new_data: dict):
        """Sauvegarde les résultats"""

        # Charger existants
        existing = self.load_existing()

        console.print("[cyan]Fusion avec données existantes...\n")

        # Merger rugs (éviter doublons)
        existing_rug_mints = {t.get("mint") for t in existing["rugs"] if t.get("mint")}
        new_rugs = [t for t in new_data["rugs"] if t.get("mint") not in existing_rug_mints]
        all_rugs = existing["rugs"] + new_rugs

        # Merger success
        existing_success_mints = {t.get("mint") for t in existing["success"] if t.get("mint")}
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
        if new_rugs:
            console.print(f"\n[red]Nouveaux RUGS ({len(new_rugs)}) :")
            for rug in new_rugs[:5]:
                console.print(f"  • {rug['name']} - ${rug['market_cap']:,.0f} - Drop: {rug['price_change_24h']:.1f}%")

        if new_successes:
            console.print(f"\n[green]Nouveaux SUCCESS ({len(new_successes)}) :")
            for success in new_successes[:5]:
                console.print(f"  • {success['name']} - ${success['market_cap']:,.0f}")

        # Statistiques
        console.print(f"\n[bold cyan]Dataset Total :")
        console.print(f"  RUGS : {len(all_rugs)}")
        console.print(f"  SUCCESS : {len(all_successes)}")
        console.print(f"  TOTAL : {len(all_rugs) + len(all_successes)}")

    async def run(self):
        """Exécution principale"""

        console.print("[bold yellow]COLLECTEUR AUTOMATIQUE[/]\n")

        # Collecter
        results = await self.collect_and_classify()

        if not results["rugs"] and not results["success"]:
            console.print("[yellow]Aucun token trouvé correspondant aux critères.")
            return

        # Sauvegarder
        console.print()
        if Confirm.ask("Sauvegarder ces résultats ?"):
            self.save_results(results)

            console.print("\n" + "="*60)
            console.print(Panel.fit(
                "[bold green]✓ COLLECTE TERMINÉE ![/]\n\n"
                "Prochaine étape :\n"
                "  → python train_with_my_data.py",
                border_style="green"
            ))
        else:
            console.print("[yellow]Annulé")

    async def close(self):
        """Ferme le client"""
        await self.client.aclose()


async def main():
    """Point d'entrée"""
    collector = SimpleCollector()

    try:
        await collector.run()
    finally:
        await collector.close()


if __name__ == "__main__":
    asyncio.run(main())
