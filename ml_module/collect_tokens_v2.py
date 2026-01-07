"""
Collecteur Simple V2 - Filtres Simplifiés
SUCCESS : Market cap > 500K
RUG : Market cap < 20K
(Pas de critère d'âge)
"""

import asyncio
import httpx
import json
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()


class SimpleCollectorV2:
    """Collecteur simplifié - seulement market cap"""

    def __init__(self):
        self.dataset_dir = Path(__file__).parent / "dataset"
        self.dataset_dir.mkdir(exist_ok=True)

        self.rugs_file = self.dataset_dir / "rugs.json"
        self.success_file = self.dataset_dir / "success.json"

        self.client = httpx.AsyncClient(timeout=30.0)

        # Filtres simplifiés
        self.success_mcap_min = 500_000  # 500K
        self.rug_mcap_max = 20_000       # 20K

    async def search_pumpswap_tokens(self) -> list:
        """Recherche tous les tokens PumpSwap sur DexScreener"""

        console.print("[cyan]Recherche de TOUS les tokens PumpSwap sur DexScreener...")

        all_pairs = []

        # Recherches multiples pour couvrir un maximum de tokens
        search_queries = [
            "pump",
            "pump.fun",
            "pumpswap",
            "sol pump",
            "solana pump"
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

                    console.print(f"[dim]  '{query}' → {len(pairs)} pairs")

                await asyncio.sleep(1.5)  # Rate limiting

            except Exception as e:
                console.print(f"[yellow]Erreur '{query}': {e}")

        # Dédupliquer
        unique_pairs = {}
        for pair in all_pairs:
            mint = pair.get("baseToken", {}).get("address")
            if mint and mint not in unique_pairs:
                unique_pairs[mint] = pair

        console.print(f"[green]✓ {len(unique_pairs)} tokens PumpSwap uniques trouvés\n")
        return list(unique_pairs.values())

    def classify_pair(self, pair: dict) -> str:
        """
        Classifie une paire en RUG, SUCCESS ou SKIP

        RÈGLES SIMPLES :
        - SUCCESS : Market cap >= 500K
        - RUG : Market cap <= 20K
        - SKIP : Entre 20K et 500K (zone grise)
        """

        market_cap = float(pair.get("marketCap", 0) or 0)

        # CRITÈRE SUCCESS : >= 500K
        if market_cap >= self.success_mcap_min:
            return "SUCCESS"

        # CRITÈRE RUG : <= 20K
        if market_cap <= self.rug_mcap_max:
            return "RUG"

        # Zone grise (entre 20K et 500K)
        return "SKIP"

    def format_token(self, pair: dict, classification: str) -> dict:
        """Formate les données du token"""
        base_token = pair.get("baseToken", {})

        # Calculer âge (pour info)
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

    async def collect_and_classify(self) -> dict:
        """Collecte et classifie les tokens"""

        console.print(Panel.fit(
            "[bold cyan]COLLECTEUR V2 - FILTRES SIMPLIFIÉS[/]\n\n"
            "[green]SUCCESS :[/]\n"
            f"  • Market Cap >= ${self.success_mcap_min:,}\n"
            f"  • (Peu importe l'âge)\n\n"
            "[red]RUG :[/]\n"
            f"  • Market Cap <= ${self.rug_mcap_max:,}\n"
            f"  • (Peu importe l'âge)\n\n"
            "[dim]SKIP : Entre 20K et 500K (zone grise)",
            border_style="cyan"
        ))

        # Rechercher tous les tokens
        pairs = await self.search_pumpswap_tokens()

        if not pairs:
            console.print("[red]Aucun token trouvé!")
            return {"rugs": [], "success": []}

        # Classifier
        console.print("[cyan]Classification simple (market cap uniquement)...\n")

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
            task = progress.add_task("Classification...", total=len(pairs))

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
        console.print(f"\n[bold cyan]Résultats de la Classification :[/]")
        console.print(f"  [red]RUGS (< $20K) : {len(rugs)}")
        console.print(f"  [green]SUCCESS (> $500K) : {len(successes)}")
        console.print(f"  [dim]Zone grise (ignorés) : {skipped}\n")

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
        console.print("[bold green]✓ Fichiers Sauvegardés !")
        console.print(f"  [red]rugs.json : {len(existing['rugs'])} → {len(all_rugs)} (+{len(new_rugs)})")
        console.print(f"  [green]success.json : {len(existing['success'])} → {len(all_successes)} (+{len(new_successes)})")

        # Exemples de nouveaux RUGS
        if new_rugs:
            console.print(f"\n[red]Nouveaux RUGS ({len(new_rugs)}) :")
            for rug in new_rugs[:5]:
                age_str = f"{rug.get('age_hours', 0):.0f}h" if rug.get('age_hours') else "??h"
                console.print(f"  • {rug['name']} - ${rug['market_cap']:,.0f} - Âge: {age_str}")

        # Exemples de nouveaux SUCCESS
        if new_successes:
            console.print(f"\n[green]Nouveaux SUCCESS ({len(new_successes)}) :")
            for success in new_successes[:5]:
                age_str = f"{success.get('age_hours', 0):.0f}h" if success.get('age_hours') else "??h"
                console.print(f"  • {success['name']} - ${success['market_cap']:,.0f} - Âge: {age_str}")

        # Statistiques finales
        console.print(f"\n[bold cyan]📊 Dataset Total :")
        console.print(f"  [red]RUGS : {len(all_rugs)}")
        console.print(f"  [green]SUCCESS : {len(all_successes)}")
        console.print(f"  [yellow]TOTAL : {len(all_rugs) + len(all_successes)} tokens")

        # Recommandations
        if len(all_rugs) >= 50 and len(all_successes) >= 50:
            console.print(f"\n[bold green]✓ Vous avez assez de données ! (50+50)")
            console.print(f"[yellow]→ Vous pouvez entraîner maintenant :")
            console.print(f"[yellow]  python train_with_my_data.py")
        else:
            needed_rugs = max(0, 50 - len(all_rugs))
            needed_success = max(0, 50 - len(all_successes))
            console.print(f"\n[yellow]📌 Pour un bon modèle, collectez encore :")
            if needed_rugs > 0:
                console.print(f"  [red]• {needed_rugs} RUGS de plus")
            if needed_success > 0:
                console.print(f"  [green]• {needed_success} SUCCESS de plus")
            console.print(f"[dim]  Relancez ce script plusieurs fois")

    async def run(self):
        """Exécution principale"""

        console.print("[bold yellow]COLLECTEUR AUTOMATIQUE V2[/]")
        console.print("[dim]Filtres simplifiés : seulement market cap\n")

        # Collecter
        results = await self.collect_and_classify()

        if not results["rugs"] and not results["success"]:
            console.print("[yellow]Aucun token trouvé correspondant aux critères.")
            console.print("[yellow]Cela peut arriver si DexScreener a peu de données.")
            return

        # Sauvegarder
        console.print()
        if Confirm.ask("Sauvegarder ces résultats ?"):
            self.save_results(results)

            console.print("\n" + "="*60)
            console.print(Panel.fit(
                "[bold green]✓ COLLECTE TERMINÉE ![/]\n\n"
                "Relancez ce script plusieurs fois pour accumuler plus de données.\n"
                "Objectif : 50 RUGS + 50 SUCCESS minimum",
                border_style="green"
            ))
        else:
            console.print("[yellow]Annulé")

    async def close(self):
        """Ferme le client HTTP"""
        await self.client.aclose()


async def main():
    """Point d'entrée"""
    collector = SimpleCollectorV2()

    try:
        await collector.run()
    finally:
        await collector.close()


if __name__ == "__main__":
    asyncio.run(main())
