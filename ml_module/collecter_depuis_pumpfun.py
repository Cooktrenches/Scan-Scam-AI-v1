"""
Collecteur depuis API Pump.fun
Récupère TOUS les tokens depuis l'API Pump.fun, puis vérifie leur market cap sur DexScreener
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


class PumpFunAPICollector:
    """Collecte depuis l'API Pump.fun officielle"""

    def __init__(self):
        self.dataset_dir = Path(__file__).parent / "dataset"
        self.dataset_dir.mkdir(exist_ok=True)

        self.rugs_file = self.dataset_dir / "rugs.json"
        self.success_file = self.dataset_dir / "success.json"

        self.client = httpx.AsyncClient(timeout=30.0)

        # Filtres
        self.success_mcap_min = 500_000  # 500K
        self.rug_mcap_max = 20_000       # 20K

    async def fetch_pumpfun_tokens(self, max_tokens: int = 1000) -> list:
        """
        Récupère les tokens depuis l'API Pump.fun
        Cette API liste TOUS les tokens créés sur Pump.fun
        """
        console.print(f"[cyan]Récupération de {max_tokens} tokens depuis Pump.fun API...")

        all_tokens = []
        batch_size = 50
        offset = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Fetching tokens...", total=max_tokens)

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
                        console.print(f"[yellow]Erreur API Pump.fun: {response.status_code}")
                        break

                    batch = response.json()

                    if not batch:
                        console.print(f"[yellow]Fin des données (offset {offset})")
                        break

                    all_tokens.extend(batch)
                    offset += batch_size

                    progress.update(task, completed=len(all_tokens))

                    await asyncio.sleep(0.3)  # Rate limiting

                except Exception as e:
                    console.print(f"[red]Erreur : {e}")
                    break

        console.print(f"[green]✓ {len(all_tokens)} tokens récupérés depuis Pump.fun\n")
        return all_tokens[:max_tokens]

    async def get_market_cap(self, mint: str) -> float:
        """Récupère le market cap depuis DexScreener"""
        try:
            response = await self.client.get(
                f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
            )

            if response.status_code == 200:
                data = response.json()
                pairs = data.get("pairs", [])

                if pairs:
                    pair = pairs[0]
                    return float(pair.get("marketCap", 0) or 0)

        except:
            pass

        return 0

    async def classify_tokens(self, tokens: list) -> dict:
        """Classifie les tokens en RUG/SUCCESS"""

        console.print("[cyan]Classification des tokens (vérification market cap)...\n")

        results = {"rugs": [], "success": [], "skipped": 0, "no_data": 0}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Vérification market cap...", total=len(tokens))

            for token in tokens:
                mint = token.get("mint")

                if not mint:
                    progress.update(task, advance=1)
                    continue

                # Récupérer market cap depuis DexScreener
                market_cap = await self.get_market_cap(mint)

                # Calculer âge
                created_timestamp = token.get("created_timestamp", 0)
                age_hours = None
                if created_timestamp:
                    try:
                        created_dt = datetime.fromtimestamp(created_timestamp / 1000)
                        age_hours = (datetime.now() - created_dt).total_seconds() / 3600
                    except:
                        pass

                # Formater token
                token_data = {
                    "mint": mint,
                    "name": token.get("name", "Unknown"),
                    "symbol": token.get("symbol", "???"),
                    "creator": token.get("creator"),
                    "market_cap": market_cap,
                    "age_hours": age_hours,
                    "collected_at": datetime.now().isoformat()
                }

                # Classifier
                if market_cap >= self.success_mcap_min:
                    token_data["classification"] = "SUCCESS"
                    results["success"].append(token_data)

                elif market_cap <= self.rug_mcap_max and market_cap > 0:
                    token_data["classification"] = "RUG"
                    results["rugs"].append(token_data)

                elif market_cap == 0:
                    results["no_data"] += 1

                else:
                    results["skipped"] += 1

                progress.update(task, advance=1)
                await asyncio.sleep(0.3)  # Rate limiting DexScreener

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

        console.print("\n[bold green]✓ Sauvegardé !")
        console.print(f"  [red]rugs.json : {len(existing['rugs'])} → {len(all_rugs)} (+{len(new_rugs)})")
        console.print(f"  [green]success.json : {len(existing['success'])} → {len(all_successes)} (+{len(new_successes)})")

        if new_successes:
            console.print(f"\n[green]Nouveaux SUCCESS ({len(new_successes)}) :")
            for success in new_successes[:5]:
                console.print(f"  • {success['name']} - ${success['market_cap']:,.0f}")

        if new_rugs:
            console.print(f"\n[red]Nouveaux RUGS ({len(new_rugs)}) :")
            for rug in new_rugs[:5]:
                console.print(f"  • {rug['name']} - ${rug['market_cap']:,.0f}")

        console.print(f"\n[bold cyan]📊 Dataset Total :")
        console.print(f"  [red]RUGS : {len(all_rugs)}")
        console.print(f"  [green]SUCCESS : {len(all_successes)}")
        console.print(f"  [yellow]TOTAL : {len(all_rugs) + len(all_successes)}")

        if len(all_rugs) >= 50 and len(all_successes) >= 50:
            console.print(f"\n[bold green]✓ Vous avez assez de données !")
            console.print(f"[yellow]→ Entraînez : python train_with_my_data.py")

    async def run(self):
        """Exécution"""

        console.print("[bold yellow]COLLECTEUR API PUMP.FUN[/]")
        console.print("[dim]Récupère tokens depuis Pump.fun, puis vérifie market cap sur DexScreener\n")

        # Demander nombre de tokens
        max_tokens = IntPrompt.ask(
            "Combien de tokens à analyser",
            default=500
        )

        console.print(f"\n[yellow]⚠️  Cela prendra environ {max_tokens * 0.4 // 60:.0f} minutes")
        console.print(f"[dim](~0.4s par token pour éviter rate limits)\n")

        if not Confirm.ask("Continuer ?"):
            console.print("[yellow]Annulé")
            return

        console.print()
        console.print(Panel.fit(
            "[bold cyan]COLLECTE DEPUIS PUMP.FUN[/]\n\n"
            "[green]SUCCESS :[/] Market Cap >= $500,000\n"
            "[red]RUG :[/] Market Cap <= $20,000",
            border_style="cyan"
        ))

        # Étape 1 : Récupérer tokens depuis Pump.fun
        tokens = await self.fetch_pumpfun_tokens(max_tokens)

        if not tokens:
            console.print("[red]Aucun token récupéré!")
            return

        # Étape 2 : Classifier (vérifier market cap)
        results = await self.classify_tokens(tokens)

        # Résultats
        console.print("\n" + "="*60)
        console.print("[bold cyan]Résultats :")
        console.print(f"  [green]SUCCESS (> $500K) : {len(results['success'])}")
        console.print(f"  [red]RUGS (< $20K) : {len(results['rugs'])}")
        console.print(f"  [yellow]Zone grise : {results['skipped']}")
        console.print(f"  [dim]Pas de données : {results['no_data']}")

        # Sauvegarder
        if results["rugs"] or results["success"]:
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
    collector = PumpFunAPICollector()

    try:
        await collector.run()
    finally:
        await collector.close()


if __name__ == "__main__":
    asyncio.run(main())
