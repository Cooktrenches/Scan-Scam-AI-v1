"""
Collecteur Automatique de Tokens PUMPSWAP UNIQUEMENT
Filtre seulement les tokens encore sur la bonding curve Pump.fun

Critères :
- SUCCESS : Market cap > 500K, âge > 48h, sur PumpSwap
- RUG : Market cap < 20K, dump en < 48h, sur PumpSwap
"""

import asyncio
import httpx
import json
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt

console = Console()


class PumpSwapCollector:
    """Collecte tokens PUMPSWAP uniquement depuis l'API Pump.fun"""

    def __init__(self):
        self.dataset_dir = Path(__file__).parent / "dataset"
        self.dataset_dir.mkdir(exist_ok=True)

        self.rugs_file = self.dataset_dir / "rugs.json"
        self.success_file = self.dataset_dir / "success.json"

        self.client = httpx.AsyncClient(timeout=30.0)

        # Critères
        self.success_mcap_min = 500_000  # 500K USD
        self.success_age_hours = 48

        self.rug_mcap_max = 20_000  # 20K USD
        self.rug_age_hours_max = 48
        self.rug_price_drop_min = 80  # -80%

    async def fetch_pump_fun_tokens(self, limit: int = 200) -> list:
        """
        Récupère les tokens directement depuis l'API Pump.fun
        Ces tokens sont TOUS sur PumpSwap (bonding curve)
        """
        console.print("[cyan]Récupération des tokens depuis Pump.fun API...")

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
            task = progress.add_task(f"Fetching tokens...", total=limit)

            while len(all_tokens) < limit:
                try:
                    # API Pump.fun
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
                        console.print(f"[yellow]Erreur API : {response.status_code}")
                        break

                    batch = response.json()

                    if not batch:
                        break

                    all_tokens.extend(batch)
                    offset += batch_size

                    progress.update(task, completed=len(all_tokens))

                    await asyncio.sleep(0.5)  # Rate limiting

                except Exception as e:
                    console.print(f"[red]Erreur : {e}")
                    break

        console.print(f"[green]✓ {len(all_tokens)} tokens Pump.fun récupérés\n")
        return all_tokens[:limit]

    async def get_token_market_data(self, mint: str) -> dict:
        """Récupère les données de marché depuis DexScreener"""
        try:
            response = await self.client.get(
                f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
            )

            if response.status_code == 200:
                data = response.json()
                pairs = data.get("pairs", [])

                if pairs:
                    # Prendre la première paire (généralement PumpSwap)
                    pair = pairs[0]

                    # Vérifier que c'est bien PumpSwap
                    dex_id = pair.get("dexId", "").lower()
                    if "pump" in dex_id or "pumpswap" in dex_id:
                        return {
                            "market_cap": float(pair.get("marketCap", 0) or 0),
                            "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0) or 0),
                            "price_change_6h": float(pair.get("priceChange", {}).get("h6", 0) or 0),
                            "liquidity": float(pair.get("liquidity", {}).get("usd", 0) or 0),
                            "url": pair.get("url", ""),
                            "on_pumpswap": True
                        }

        except:
            pass

        return None

    def classify_token(self, token: dict, market_data: dict) -> str:
        """Classifie le token en RUG, SUCCESS ou SKIP"""

        if not market_data:
            return "SKIP"

        # Extraire données
        market_cap = market_data["market_cap"]
        price_change_24h = market_data["price_change_24h"]
        price_change_6h = market_data["price_change_6h"]

        # Calculer l'âge
        created_timestamp = token.get("created_timestamp", 0)
        if created_timestamp:
            created_dt = datetime.fromtimestamp(created_timestamp / 1000)
            age_hours = (datetime.now() - created_dt).total_seconds() / 3600
        else:
            age_hours = 999

        # CRITÈRE SUCCESS : mcap > 500K et âge > 48h
        if market_cap >= self.success_mcap_min and age_hours >= self.success_age_hours:
            return "SUCCESS"

        # CRITÈRE RUG : mcap < 20K, âge < 48h, et gros dump
        if market_cap <= self.rug_mcap_max and age_hours <= self.rug_age_hours_max:
            if price_change_24h <= -self.rug_price_drop_min or price_change_6h <= -self.rug_price_drop_min:
                return "RUG"

        return "SKIP"

    def format_token_data(self, token: dict, market_data: dict, classification: str) -> dict:
        """Formate les données du token"""
        return {
            "mint": token.get("mint"),
            "name": token.get("name", "Unknown"),
            "symbol": token.get("symbol", "???"),
            "creator": token.get("creator"),
            "market_cap": market_data.get("market_cap", 0),
            "price_change_24h": market_data.get("price_change_24h", 0),
            "liquidity": market_data.get("liquidity", 0),
            "dex_url": market_data.get("url", ""),
            "on_pumpswap": True,
            "classification": classification,
            "collected_at": datetime.now().isoformat()
        }

    async def collect_and_classify(self, max_tokens: int = 200) -> dict:
        """Collecte et classifie les tokens PumpSwap"""

        console.print(Panel.fit(
            "[bold cyan]COLLECTE AUTOMATIQUE - PUMPSWAP UNIQUEMENT[/]\n\n"
            "[yellow]Critères SUCCESS:[/]\n"
            f"  • Market Cap > ${self.success_mcap_min:,}\n"
            f"  • Âge > {self.success_age_hours}h\n"
            f"  • Sur PumpSwap (bonding curve)\n\n"
            "[yellow]Critères RUG:[/]\n"
            f"  • Market Cap < ${self.rug_mcap_max:,}\n"
            f"  • Dump en < {self.rug_age_hours_max}h\n"
            f"  • Chute de prix > {self.rug_price_drop_min}%\n"
            f"  • Sur PumpSwap (bonding curve)",
            border_style="cyan"
        ))

        # Récupérer tokens depuis Pump.fun
        tokens = await self.fetch_pump_fun_tokens(limit=max_tokens)

        if not tokens:
            console.print("[red]Aucun token trouvé !")
            return {"rugs": [], "success": []}

        # Analyser chaque token
        console.print("[cyan]Analyse des tokens (vérification market data)...\n")

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
            task = progress.add_task("Analyse...", total=len(tokens))

            for token in tokens:
                mint = token.get("mint")
                if not mint:
                    progress.update(task, advance=1)
                    continue

                # Récupérer données de marché
                market_data = await self.get_token_market_data(mint)

                if market_data and market_data.get("on_pumpswap"):
                    # Classifier
                    classification = self.classify_token(token, market_data)

                    if classification == "RUG":
                        rugs.append(self.format_token_data(token, market_data, "RUG"))
                    elif classification == "SUCCESS":
                        successes.append(self.format_token_data(token, market_data, "SUCCESS"))
                    else:
                        skipped += 1
                else:
                    skipped += 1

                progress.update(task, advance=1)
                await asyncio.sleep(0.3)  # Rate limiting DexScreener

        # Afficher résultats
        console.print(f"\n[bold cyan]Résultats de la Classification :[/]")
        console.print(f"  [red]RUGS détectés : {len(rugs)}")
        console.print(f"  [green]SUCCESS détectés : {len(successes)}")
        console.print(f"  [dim]Ignorés (pas sur PumpSwap ou hors critères) : {skipped}\n")

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
            console.print("\n[red]Exemples de RUGS ajoutés (PumpSwap) :")
            for rug in new_rugs[:5]:
                console.print(f"  • {rug['name']} ({rug['symbol']}) - Mcap: ${rug['market_cap']:,.0f} - Drop: {rug['price_change_24h']:.1f}%")

        if new_successes:
            console.print("\n[green]Exemples de SUCCESS ajoutés (PumpSwap) :")
            for success in new_successes[:5]:
                console.print(f"  • {success['name']} ({success['symbol']}) - Mcap: ${success['market_cap']:,.0f}")

        # Afficher statistiques finales
        console.print(f"\n[bold cyan]Dataset Final :[/]")
        console.print(f"  Total RUGS : {len(all_rugs)}")
        console.print(f"  Total SUCCESS : {len(all_successes)}")
        console.print(f"  Total : {len(all_rugs) + len(all_successes)} tokens")

    async def run(self):
        """Exécute la collecte complète"""

        console.print("[bold yellow]COLLECTEUR PUMPSWAP[/]\n")

        # Demander combien de tokens
        max_tokens = IntPrompt.ask(
            "Combien de tokens analyser maximum ?",
            default=200
        )

        console.print(f"\n[yellow]ℹ️  Cela prendra environ {max_tokens * 0.5 // 60:.0f} minutes")
        console.print(f"[dim](~0.5 seconde par token pour éviter rate limits)\n")

        if not Confirm.ask("Continuer ?"):
            console.print("[yellow]Annulé")
            return

        # Collecter et classifier
        results = await self.collect_and_classify(max_tokens)

        if not results["rugs"] and not results["success"]:
            console.print("[yellow]\nAucun token correspondant aux critères trouvé.")
            console.print("[yellow]Les tokens récents peuvent ne pas encore correspondre aux critères.")
            console.print("[yellow]Essayez avec plus de tokens ou attendez quelques jours.")
            return

        # Demander confirmation avant sauvegarde
        console.print()
        if Confirm.ask("Sauvegarder ces résultats ?"):
            self.merge_and_save(results)

            console.print("\n" + "="*60)
            console.print(Panel.fit(
                "[bold green]✓ COLLECTE TERMINÉE ![/]\n\n"
                f"Dataset mis à jour avec tokens PumpSwap uniquement.\n\n"
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
    collector = PumpSwapCollector()

    try:
        await collector.run()
    finally:
        await collector.close()


if __name__ == "__main__":
    asyncio.run(main())
