"""
Script Automatique d'Entraînement
Utilise VOS données (rugs.json + success.json) pour entraîner le modèle ML
"""

import asyncio
import json
import pandas as pd
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Confirm

from feature_extractor import TokenFeatureExtractor
from model_trainer import TokenClassifierTrainer

console = Console()


class SimpleTrainer:
    """Entraîneur simplifié pour vos données"""

    def __init__(self):
        self.dataset_dir = Path(__file__).parent / "dataset"
        self.rugs_file = self.dataset_dir / "rugs.json"
        self.success_file = self.dataset_dir / "success.json"
        self.features_file = self.dataset_dir / "features.csv"

    def check_files_exist(self) -> bool:
        """Vérifie que les fichiers de données existent"""
        console.print(Panel.fit(
            "[bold cyan]ÉTAPE 1 : Vérification des Fichiers[/]",
            border_style="cyan"
        ))

        files_ok = True

        # Vérifier rugs.json
        if self.rugs_file.exists():
            with open(self.rugs_file) as f:
                rugs = json.load(f)
            console.print(f"[green][OK] rugs.json trouvé : {len(rugs)} tokens")
        else:
            console.print(f"[red][X] rugs.json NON TROUVÉ")
            console.print(f"[yellow]  Créez le fichier : {self.rugs_file}")
            files_ok = False

        # Vérifier success.json
        if self.success_file.exists():
            with open(self.success_file) as f:
                successes = json.load(f)
            console.print(f"[green][OK] success.json trouvé : {len(successes)} tokens")
        else:
            console.print(f"[red][X] success.json NON TROUVÉ")
            console.print(f"[yellow]  Créez le fichier : {self.success_file}")
            files_ok = False

        if not files_ok:
            console.print("\n[red]ERREUR : Fichiers manquants![/]")
            console.print("[yellow]Voir GUIDE_ENTRAINEMENT.md pour créer vos fichiers")
            return False

        console.print(f"\n[green][OK] Tous les fichiers sont OK!")
        return True

    async def extract_features(self):
        """Extrait les features de tous les tokens"""
        console.print(Panel.fit(
            "[bold cyan]ÉTAPE 2 : Extraction des Features (75 par token)[/]",
            border_style="cyan"
        ))

        # Charger les données
        with open(self.rugs_file) as f:
            rugs = json.load(f)
        with open(self.success_file) as f:
            successes = json.load(f)

        total_tokens = len(rugs) + len(successes)
        console.print(f"[cyan]Total à traiter : {total_tokens} tokens")
        console.print(f"  - Rugs : {len(rugs)}")
        console.print(f"  - Succès : {len(successes)}\n")

        # Demander confirmation
        if total_tokens > 100:
            console.print(f"[yellow][!]  Cela prendra environ {total_tokens * 5 // 60} minutes")
            if not Confirm.ask("Continuer ?"):
                console.print("[yellow]Annulé par l'utilisateur")
                return False

        # Extraire features
        extractor = TokenFeatureExtractor()
        all_features = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            # Task pour les rugs
            task_rugs = progress.add_task(
                "[red]Extraction RUGS...",
                total=len(rugs)
            )

            for token in rugs:
                mint = token.get("mint")
                if not mint:
                    console.print(f"[yellow][!]  Token sans adresse mint : {token}")
                    progress.update(task_rugs, advance=1)
                    continue

                try:
                    features = await extractor.extract_all_features(mint)
                    if features:
                        features["label"] = 0  # RUG
                        all_features.append(features)
                        progress.update(task_rugs, advance=1, description=f"[red]RUGS : {len(all_features)} extraits")
                    else:
                        console.print(f"[yellow][!]  Échec extraction : {mint[:8]}...")
                        progress.update(task_rugs, advance=1)
                except Exception as e:
                    console.print(f"[red][X] Erreur {mint[:8]}... : {e}")
                    progress.update(task_rugs, advance=1)

                await asyncio.sleep(0.5)  # Rate limiting

            console.print(f"[green][OK] Rugs extraits : {len([f for f in all_features if f['label'] == 0])}\n")

            # Task pour les succès
            task_success = progress.add_task(
                "[green]Extraction SUCCESS...",
                total=len(successes)
            )

            for token in successes:
                mint = token.get("mint")
                if not mint:
                    console.print(f"[yellow][!]  Token sans adresse mint : {token}")
                    progress.update(task_success, advance=1)
                    continue

                try:
                    features = await extractor.extract_all_features(mint)
                    if features:
                        features["label"] = 2  # HIGH_POTENTIAL
                        all_features.append(features)
                        progress.update(task_success, advance=1, description=f"[green]SUCCESS : {len(all_features)} extraits")
                    else:
                        console.print(f"[yellow][!]  Échec extraction : {mint[:8]}...")
                        progress.update(task_success, advance=1)
                except Exception as e:
                    console.print(f"[red][X] Erreur {mint[:8]}... : {e}")
                    progress.update(task_success, advance=1)

                await asyncio.sleep(0.5)  # Rate limiting

        await extractor.close()

        # Sauvegarder
        if all_features:
            df = pd.DataFrame(all_features)
            df.to_csv(self.features_file, index=False)
            console.print(f"\n[bold green][OK] Features sauvegardées : {len(df)} tokens")
            console.print(f"[green]  Fichier : {self.features_file.name}")
            return True
        else:
            console.print(f"\n[red][X] Aucune feature extraite!")
            return False

    def train_model(self):
        """Entraîne le modèle ML"""
        console.print(Panel.fit(
            "[bold cyan]ÉTAPE 3 : Entraînement du Modèle ML[/]",
            border_style="cyan"
        ))

        if not self.features_file.exists():
            console.print(f"[red][X] Fichier features.csv non trouvé!")
            console.print(f"[yellow]  Exécutez d'abord l'extraction des features")
            return False

        # Entraîner
        trainer = TokenClassifierTrainer()
        trainer.train_full_pipeline(model_type="random_forest")

        return True

    async def run_complete_training(self):
        """Exécute le processus complet d'entraînement"""
        console.print(Panel.fit(
            "[bold yellow]ENTRAÎNEMENT AUTOMATIQUE DU MODÈLE ML[/]\n"
            "Utilise VOS données (rugs.json + success.json)",
            border_style="yellow"
        ))

        # Étape 1 : Vérifier fichiers
        if not self.check_files_exist():
            return

        console.print("\n")

        # Étape 2 : Extraire features
        success = await self.extract_features()
        if not success:
            console.print("\n[red][X] Échec extraction des features")
            return

        console.print("\n")

        # Étape 3 : Entraîner modèle
        success = self.train_model()
        if not success:
            console.print("\n[red][X] Échec entraînement du modèle")
            return

        # Succès !
        console.print("\n" + "="*60)
        console.print(Panel.fit(
            "[bold green][OK] ENTRAÎNEMENT TERMINÉ AVEC SUCCÈS ![/]\n\n"
            "Votre modèle ML est prêt à utiliser.\n"
            "Fichiers créés :\n"
            "  - dataset/features.csv\n"
            "  - models/random_forest_latest.pkl\n"
            "  - models/scaler_latest.pkl\n\n"
            "Prochaine étape :\n"
            "  → Tester : python test_my_model.py\n"
            "  → Intégrer au scanner (voir GUIDE_ENTRAINEMENT.md)",
            border_style="green"
        ))


async def main():
    """Point d'entrée principal"""
    trainer = SimpleTrainer()
    await trainer.run_complete_training()


if __name__ == "__main__":
    asyncio.run(main())
