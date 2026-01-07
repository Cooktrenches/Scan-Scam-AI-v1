"""
Script Simple : Vérifie les tokens dans tokens_a_verifier.txt
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


async def verify_tokens():
    """Vérifie les tokens du fichier"""

    # Lire le fichier
    tokens_file = Path(__file__).parent / "tokens_a_verifier.txt"

    if not tokens_file.exists():
        console.print("[red]Fichier tokens_a_verifier.txt non trouvé!")
        console.print("[yellow]Créez le fichier et ajoutez les adresses (une par ligne)")
        return

    # Charger adresses
    with open(tokens_file) as f:
        token_mints = [line.strip() for line in f if line.strip()]

    if not token_mints:
        console.print("[yellow]Le fichier est vide!")
        return

    console.print(Panel.fit(
        f"[bold cyan]VÉRIFICATION DE {len(token_mints)} TOKENS[/]\n\n"
        "[green]SUCCESS :[/] Market Cap >= $500,000\n"
        "[red]RUG :[/] Market Cap <= $20,000",
        border_style="cyan"
    ))

    # Préparer résultats
    results = {"rugs": [], "success": [], "skipped": []}
    client = httpx.AsyncClient(timeout=30.0)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Vérification...", total=len(token_mints))

        for mint in token_mints:
            try:
                # Récupérer données DexScreener
                response = await client.get(
                    f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
                )

                if response.status_code == 200:
                    data = response.json()
                    pairs = data.get("pairs", [])

                    if pairs:
                        pair = pairs[0]
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

                        token_data = {
                            "mint": base_token.get("address", mint),
                            "name": base_token.get("name", "Unknown"),
                            "symbol": base_token.get("symbol", "???"),
                            "market_cap": market_cap,
                            "price_change_24h": pair.get("priceChange", {}).get("h24", 0),
                            "liquidity": pair.get("liquidity", {}).get("usd", 0),
                            "age_hours": age_hours,
                            "dex_url": pair.get("url", ""),
                            "dex_id": pair.get("dexId", ""),
                            "collected_at": datetime.now().isoformat()
                        }

                        # Classifier
                        if market_cap >= 500_000:
                            token_data["classification"] = "SUCCESS"
                            results["success"].append(token_data)
                            console.print(f"[green]✓ {token_data['name']} - ${market_cap:,.0f} - SUCCESS")

                        elif market_cap <= 20_000:
                            token_data["classification"] = "RUG"
                            results["rugs"].append(token_data)
                            console.print(f"[red]✓ {token_data['name']} - ${market_cap:,.0f} - RUG")

                        else:
                            results["skipped"].append(token_data)
                            console.print(f"[yellow]◯ {token_data['name']} - ${market_cap:,.0f} - Zone grise")

                    else:
                        console.print(f"[red]✗ {mint[:16]}... - Pas de données")
                else:
                    console.print(f"[red]✗ {mint[:16]}... - Erreur API")

            except Exception as e:
                console.print(f"[red]✗ {mint[:16]}... - Erreur: {e}")

            progress.update(task, advance=1)
            await asyncio.sleep(0.5)  # Rate limiting

    await client.aclose()

    # Résumé
    console.print("\n" + "="*60)
    console.print("[bold cyan]Résumé :")
    console.print(f"  [green]SUCCESS : {len(results['success'])}")
    console.print(f"  [red]RUGS : {len(results['rugs'])}")
    console.print(f"  [yellow]Zone grise : {len(results['skipped'])}")

    # Sauvegarder ?
    if results["rugs"] or results["success"]:
        console.print()
        if Confirm.ask("Ajouter au dataset (rugs.json + success.json) ?"):
            # Charger existants
            dataset_dir = Path(__file__).parent / "dataset"
            rugs_file = dataset_dir / "rugs.json"
            success_file = dataset_dir / "success.json"

            # Charger
            existing_rugs = []
            existing_success = []

            if rugs_file.exists():
                with open(rugs_file) as f:
                    existing_rugs = json.load(f)

            if success_file.exists():
                with open(success_file) as f:
                    existing_success = json.load(f)

            # Merger
            existing_rug_mints = {t.get("mint") for t in existing_rugs}
            new_rugs = [t for t in results["rugs"] if t.get("mint") not in existing_rug_mints]
            all_rugs = existing_rugs + new_rugs

            existing_success_mints = {t.get("mint") for t in existing_success}
            new_successes = [t for t in results["success"] if t.get("mint") not in existing_success_mints]
            all_successes = existing_success + new_successes

            # Sauvegarder
            with open(rugs_file, "w") as f:
                json.dump(all_rugs, f, indent=2)

            with open(success_file, "w") as f:
                json.dump(all_successes, f, indent=2)

            console.print(f"\n[bold green]✓ Sauvegardé !")
            console.print(f"  [red]rugs.json : +{len(new_rugs)}")
            console.print(f"  [green]success.json : +{len(new_successes)}")

            console.print(f"\n[bold cyan]Dataset Total :")
            console.print(f"  [red]RUGS : {len(all_rugs)}")
            console.print(f"  [green]SUCCESS : {len(all_successes)}")
            console.print(f"  [yellow]TOTAL : {len(all_rugs) + len(all_successes)}")


async def main():
    await verify_tokens()


if __name__ == "__main__":
    asyncio.run(main())
