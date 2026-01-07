"""
Script Automatique de Collecte de Tokens depuis DexScreener
Critères :
- SUCCESS : Market cap > 500K, âge > 48h
- RUG : Market cap < 20K, dump en < 48h
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt

console = Console()


class DexScreenerCollector:
    """Collecte automatique de tokens depuis DexScreener"""

    def __init__(self):
        self.dataset_dir = Path(__file__).parent / "dataset"
        self.dataset_dir.mkdir(exist_ok=True)

        self.rugs_file = self.dataset_dir / "rugs.json"
        self.success_file = self.dataset_dir / "success.json"

        self.client = httpx.AsyncClient(timeout=30.0)

        # Critères
        self.success_mcap_min = 500_000  # 500K minimum
        self.success_age_hours = 48  # 48h minimum

        self.rug_mcap_max = 20_000  # 20K maximum
        self.rug_age_hours_max = 48  # Dump en moins de 48h
        self.rug_price_drop_min = 80  # Chute de prix minimum -80%

    async def fetch_pump_fun_tokens(self, limit: int = 500) -> list:
        """Récupère les tokens Pump.fun depuis DexScreener"""
        console.print("[cyan]Récupération des tokens depuis DexScreener...")

        all_tokens = []

        try:
            # DexScreener API - recherche tokens Solana
            response = await self.client.get(
                "https://api.dexscreener.com/latest/dex/search",
                params={"q": "pump.fun"}
            )

            if response.status_code != 200:
                console.print(f"[red]Erreur API : {response.status_code}")
                return []

            data = response.json()
            pairs = data.get("pairs", [])

            # Filtrer uniquement Pump.fun sur Solana
            for pair in pairs:
                if pair.get("chainId") == "solana":
                    # Vérifier que c'est bien un token Pump.fun
                    dex_id = pair.get("dexId", "")
                    if "pump" in dex_id.lower() or "pump" in pair.get("url", "").lower():
                        all_tokens.append(pair)

            console.print(f"[green]✓ Trouvé {len(all_tokens)} tokens Pump.fun")

        except Exception as e:
            console.print(f"[red]Erreur : {e}")

        return all_tokens[:limit]

    async def search_tokens_by_criteria(self, max_pages: int = 10) -> list:
        """Recherche tokens en parcourant plusieurs pages"""
        console.print("[cyan]Recherche de tokens sur DexScreener...\n")

        all_tokens = []

        # Recherche par différentes queries
        queries = ["pump", "solana pump", "pump.fun"]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Recherche en cours...", total=len(queries))

            for query in queries:
                try:
                    response = await self.client.get(
                        f"https://api.dexscreener.com/latest/dex/search",
                        params={"q": query}
                    )

                    if response.status_code == 200:
                        data = response.json()
                        pairs = data.get("pairs", [])

                        # Filtrer Solana + Pump.fun
                        for pair in pairs:
                            if pair.get("chainId") == "solana":
                                all_tokens.append(pair)

                        progress.update(task, advance=1)

                    await asyncio.sleep(1)  # Rate limiting

                except Exception as e:
                    console.print(f"[yellow]Erreur pour '{query}': {e}")
                    progress.update(task, advance=1)

        # Dédupliquer
        unique_tokens = {}
        for token in all_tokens:
            addr = token.get("baseToken", {}).get("address")
            if addr and addr not in unique_tokens:
                unique_tokens[addr] = token

        console.print(f"[green]✓ {len(unique_tokens)} tokens uniques trouvés\n")
        return list(unique_tokens.values())

    def classify_token(self, pair: dict) -> str:
        """Classifie un token en RUG, SUCCESS ou SKIP"""

        # Extraire données
        market_cap = float(pair.get("marketCap", 0) or 0)
        price_change_24h = float(pair.get("priceChange", {}).get("h24", 0) or 0)
        price_change_6h = float(pair.get("priceChange", {}).get("h6", 0) or 0)
        liquidity = float(pair.get("liquidity", {}).get("usd", 0) or 0)

        # Calculer l'âge approximatif
        created_at = pair.get("pairCreatedAt")
        age_hours = 999  # Par défaut ancien

        if created_at:
            try:
                created_dt = datetime.fromtimestamp(created_at / 1000)
                age_hours = (datetime.now() - created_dt).total_seconds() / 3600
            except:
                pass

        # CRITÈRE SUCCESS : mcap > 500K et âge > 48h
        if market_cap >= self.success_mcap_min and age_hours >= self.success_age_hours:
            return "SUCCESS"

        # CRITÈRE RUG : mcap < 20K et dump récent (< 48h)
        if market_cap <= self.rug_mcap_max and age_hours <= self.rug_age_hours_max:
            # Vérifier qu'il y a eu un gros dump
            if price_change_24h <= -self.rug_price_drop_min or price_change_6h <= -self.rug_price_drop_min:
                return "RUG"

        return "SKIP"

    def format_token_data(self, pair: dict, classification: str) -> dict:
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
            "classification": classification,
            "collected_at": datetime.now().isoformat()
        }

    async def collect_and_classify(self, max_tokens: int = 200) -> dict:
        """Collecte et classifie les tokens"""

        console.print(Panel.fit(
            "[bold cyan]COLLECTE AUTOMATIQUE DEPUIS DEXSCREENER[/]\n\n"
            "[yellow]Critères SUCCESS:[/]\n"
            f"  • Market Cap > ${self.success_mcap_min:,}\n"
            f"  • Âge > {self.success_age_hours}h\n\n"
            "[yellow]Critères RUG:[/]\n"
            f"  • Market Cap < ${self.rug_mcap_max:,}\n"
            f"  • Dump en < {self.rug_age_hours_max}h\n"
            f"  • Chute de prix > {self.rug_price_drop_min}%",
            border_style="cyan"
        ))

        # Récupérer tokens
        tokens = await self.search_tokens_by_criteria()

        if not tokens:
            console.print("[red]Aucun token trouvé !")
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
            console=console
        ) as progress:
            task = progress.add_task("Analyse...", total=len(tokens))

            for pair in tokens:
                classification = self.classify_token(pair)

                if classification == "RUG":
                    rugs.append(self.format_token_data(pair, "RUG"))
                elif classification == "SUCCESS":
                    successes.append(self.format_token_data(pair, "SUCCESS"))
                else:
                    skipped += 1

                progress.update(task, advance=1)

        # Afficher résultats
        console.print(f"\n[bold cyan]Résultats de la Classification :[/]")
        console.print(f"  [red]RUGS détectés : {len(rugs)}")
        console.print(f"  [green]SUCCESS détectés : {len(successes)}")
        console.print(f"  [dim]Ignorés : {skipped}\n")

        return {"rugs": rugs, "success": successes}

    def load_existing_datasets(self) -> dict:
        """Charge les datasets existants"""
        existing = {"rugs": [], "success": []}

        if self.rugs_file.exists():
            with open(self.rugs_file) as f:
                existing["rugs"] = json.load(f)

        if self.success_file.exists():
            with open(self.success_file) as f:
                existing["success"] = json.load(f)

        return existing

    def merge_and_save(self, new_data: dict):
        """Fusionne avec les données existantes et sauvegarde"""

        # Charger existants
        existing = self.load_existing_datasets()

        console.print("[cyan]Fusion avec les données existantes...\n")

        # Merger les rugs (éviter doublons)
        existing_rug_mints = {t.get("mint") for t in existing["rugs"] if t.get("mint")}
        new_rugs = [t for t in new_data["rugs"] if t.get("mint") not in existing_rug_mints]

        all_rugs = existing["rugs"] + new_rugs

        # Merger les success
        existing_success_mints = {t.get("mint") for t in existing["success"] if t.get("mint")}
        new_successes = [t for t in new_data["success"] if t.get("mint") not in existing_success_mints]

        all_successes = existing["success"] + new_successes

        # Sauvegarder
        with open(self.rugs_file, "w") as f:
            json.dump(all_rugs, f, indent=2)

        with open(self.success_file, "w") as f:
            json.dump(all_successes, f, indent=2)

        console.print("[bold green]✓ Fichiers sauvegardés !")
        console.print(f"  [red]rugs.json : {len(existing['rugs'])} → {len(all_rugs)} (+{len(new_rugs)})")
        console.print(f"  [green]success.json : {len(existing['success'])} → {len(all_successes)} (+{len(new_successes)})")

        # Afficher échantillons
        if new_rugs:
            console.print("\n[red]Exemples de RUGS ajoutés :")
            for rug in new_rugs[:3]:
                console.print(f"  • {rug['name']} ({rug['symbol']}) - Mcap: ${rug['market_cap']:,.0f}")

        if new_successes:
            console.print("\n[green]Exemples de SUCCESS ajoutés :")
            for success in new_successes[:3]:
                console.print(f"  • {success['name']} ({success['symbol']}) - Mcap: ${success['market_cap']:,.0f}")

    async def run(self):
        """Exécute la collecte complète"""

        console.print("[bold yellow]COLLECTEUR AUTOMATIQUE DE TOKENS[/]\n")

        # Demander combien de tokens
        max_tokens = IntPrompt.ask(
            "Combien de tokens analyser maximum ?",
            default=200
        )

        # Collecter et classifier
        results = await self.collect_and_classify(max_tokens)

        if not results["rugs"] and not results["success"]:
            console.print("[yellow]Aucun token correspondant aux critères trouvé.")
            console.print("[yellow]Essayez d'ajuster les critères dans le script.")
            return

        # Demander confirmation avant sauvegarde
        console.print()
        if Confirm.ask("Sauvegarder ces résultats ?"):
            self.merge_and_save(results)

            console.print("\n" + "="*60)
            console.print(Panel.fit(
                "[bold green]✓ COLLECTE TERMINÉE ![/]\n\n"
                "Prochaine étape :\n"
                "  → python train_with_my_data.py",
                border_style="green"
            ))
        else:
            console.print("[yellow]Sauvegarde annulée")

    async def close(self):
        """Ferme le client HTTP"""
        await self.client.aclose()


async def main():
    """Point d'entrée principal"""
    collector = DexScreenerCollector()

    try:
        await collector.run()
    finally:
        await collector.close()


if __name__ == "__main__":
    asyncio.run(main())
