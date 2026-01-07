"""
Vérifier des Tokens Spécifiques
Collez des adresses de tokens et le script les classifie automatiquement
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
from rich.table import Table

console = Console()


class TokenChecker:
    """Vérifie et classifie des tokens spécifiques"""

    def __init__(self):
        self.dataset_dir = Path(__file__).parent / "dataset"
        self.dataset_dir.mkdir(exist_ok=True)

        self.rugs_file = self.dataset_dir / "rugs.json"
        self.success_file = self.dataset_dir / "success.json"

        self.client = httpx.AsyncClient(timeout=30.0)

        # Filtres
        self.success_mcap_min = 500_000  # 500K
        self.rug_mcap_max = 20_000       # 20K

    async def get_token_data(self, mint: str) -> dict:
        """Récupère les données d'un token depuis DexScreener"""
        try:
            response = await self.client.get(
                f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
            )

            if response.status_code == 200:
                data = response.json()
                pairs = data.get("pairs", [])

                if pairs:
                    # Prendre la première paire
                    pair = pairs[0]

                    # Extraire données
                    base_token = pair.get("baseToken", {})
                    market_cap = float(pair.get("marketCap", 0) or 0)

                    # Calculer âge
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
                        "market_cap": market_cap,
                        "price_change_24h": pair.get("priceChange", {}).get("h24", 0),
                        "liquidity": pair.get("liquidity", {}).get("usd", 0),
                        "age_hours": age_hours,
                        "dex_url": pair.get("url", ""),
                        "dex_id": pair.get("dexId", ""),
                        "found": True
                    }

        except Exception as e:
            console.print(f"[red]Erreur pour {mint[:8]}... : {e}")

        return {"mint": mint, "found": False}

    def classify_token(self, token_data: dict) -> str:
        """Classifie un token"""
        if not token_data.get("found"):
            return "NOT_FOUND"

        market_cap = token_data.get("market_cap", 0)

        # SUCCESS : >= 500K
        if market_cap >= self.success_mcap_min:
            return "SUCCESS"

        # RUG : <= 20K
        if market_cap <= self.rug_mcap_max:
            return "RUG"

        # Zone grise
        return "SKIP"

    async def check_tokens(self, token_mints: list) -> dict:
        """Vérifie une liste de tokens"""

        console.print(Panel.fit(
            f"[bold cyan]VÉRIFICATION DE {len(token_mints)} TOKENS[/]\n\n"
            "[green]SUCCESS :[/] Market Cap >= $500,000\n"
            "[red]RUG :[/] Market Cap <= $20,000\n"
            "[yellow]SKIP :[/] Entre 20K et 500K",
            border_style="cyan"
        ))

        results = {
            "rugs": [],
            "success": [],
            "skipped": [],
            "not_found": []
        }

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Vérification...", total=len(token_mints))

            for mint in token_mints:
                # Récupérer données
                token_data = await self.get_token_data(mint)

                if not token_data.get("found"):
                    results["not_found"].append(mint)
                    console.print(f"[red]✗ {mint[:16]}... - Non trouvé sur DexScreener")
                else:
                    # Classifier
                    classification = self.classify_token(token_data)

                    if classification == "SUCCESS":
                        token_data["classification"] = "SUCCESS"
                        token_data["collected_at"] = datetime.now().isoformat()
                        results["success"].append(token_data)
                        console.print(f"[green]✓ {token_data['name']} - ${token_data['market_cap']:,.0f} - SUCCESS")

                    elif classification == "RUG":
                        token_data["classification"] = "RUG"
                        token_data["collected_at"] = datetime.now().isoformat()
                        results["rugs"].append(token_data)
                        console.print(f"[red]✓ {token_data['name']} - ${token_data['market_cap']:,.0f} - RUG")

                    elif classification == "SKIP":
                        results["skipped"].append(token_data)
                        console.print(f"[yellow]◯ {token_data['name']} - ${token_data['market_cap']:,.0f} - Zone grise")

                progress.update(task, advance=1)
                await asyncio.sleep(0.5)  # Rate limiting

        return results

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

        # Merger rugs
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
        console.print("\n[bold green]✓ Fichiers Sauvegardés !")
        console.print(f"  [red]rugs.json : {len(existing['rugs'])} → {len(all_rugs)} (+{len(new_rugs)})")
        console.print(f"  [green]success.json : {len(existing['success'])} → {len(all_successes)} (+{len(new_successes)})")

        console.print(f"\n[bold cyan]📊 Dataset Total :")
        console.print(f"  [red]RUGS : {len(all_rugs)}")
        console.print(f"  [green]SUCCESS : {len(all_successes)}")
        console.print(f"  [yellow]TOTAL : {len(all_rugs) + len(all_successes)}")

    async def run(self):
        """Exécution principale"""

        console.print("[bold yellow]VÉRIFICATEUR DE TOKENS SPÉCIFIQUES[/]\n")

        console.print("[cyan]Collez les adresses de tokens (une par ligne)")
        console.print("[cyan]Appuyez sur ENTRÉE deux fois quand vous avez fini\n")

        # Lire les adresses
        token_mints = []
        while True:
            try:
                line = input().strip()
                if not line:
                    break
                if line:
                    token_mints.append(line)
            except EOFError:
                break

        if not token_mints:
            console.print("[yellow]Aucune adresse fournie")
            return

        console.print(f"\n[green]✓ {len(token_mints)} adresses à vérifier\n")

        # Vérifier les tokens
        results = await self.check_tokens(token_mints)

        # Résumé
        console.print("\n" + "="*60)
        console.print("[bold cyan]Résumé :")
        console.print(f"  [green]SUCCESS : {len(results['success'])}")
        console.print(f"  [red]RUGS : {len(results['rugs'])}")
        console.print(f"  [yellow]Zone grise : {len(results['skipped'])}")
        console.print(f"  [dim]Non trouvés : {len(results['not_found'])}")

        # Sauvegarder
        if results["rugs"] or results["success"]:
            console.print()
            if Confirm.ask("Sauvegarder dans dataset ?"):
                self.save_results(results)

                console.print("\n" + "="*60)
                console.print(Panel.fit(
                    "[bold green]✓ TERMINÉ ![/]\n\n"
                    "Les tokens ont été ajoutés au dataset.",
                    border_style="green"
                ))

    async def close(self):
        """Ferme le client"""
        await self.client.aclose()


async def main():
    """Point d'entrée"""
    checker = TokenChecker()

    try:
        await checker.run()
    finally:
        await checker.close()


if __name__ == "__main__":
    asyncio.run(main())
