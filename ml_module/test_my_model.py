"""
Script de Test du Modèle ML
Teste votre modèle entraîné sur quelques tokens
"""

import asyncio
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from predictor import TokenPredictor
from feature_extractor import TokenFeatureExtractor

console = Console()


async def test_model():
    """Teste le modèle sur vos tokens"""

    console.print(Panel.fit(
        "[bold cyan]TEST DU MODÈLE ML[/]",
        border_style="cyan"
    ))

    # Vérifier que le modèle existe
    models_dir = Path(__file__).parent / "models"
    model_file = models_dir / "random_forest_latest.pkl"

    if not model_file.exists():
        console.print("[red][X] Modèle non trouvé!")
        console.print("[yellow]Entraînez d'abord le modèle : python train_with_my_data.py")
        return

    console.print(f"[green][OK] Modèle trouvé : {model_file.name}\n")

    # Charger le modèle
    try:
        predictor = TokenPredictor()
        console.print("[green][OK] Modèle chargé avec succès!\n")
    except Exception as e:
        console.print(f"[red][X] Erreur chargement modèle : {e}")
        return

    # Charger quelques tokens de test
    dataset_dir = Path(__file__).parent / "dataset"
    rugs_file = dataset_dir / "rugs.json"
    success_file = dataset_dir / "success.json"

    test_tokens = []

    # Prendre 3 rugs
    if rugs_file.exists():
        with open(rugs_file) as f:
            rugs = json.load(f)
            for token in rugs[:3]:
                if token.get("mint"):
                    test_tokens.append({
                        "mint": token["mint"],
                        "name": token.get("name", "Unknown"),
                        "expected": "RUG"
                    })

    # Prendre 3 succès
    if success_file.exists():
        with open(success_file) as f:
            successes = json.load(f)
            for token in successes[:3]:
                if token.get("mint"):
                    test_tokens.append({
                        "mint": token["mint"],
                        "name": token.get("name", "Unknown"),
                        "expected": "HIGH_POTENTIAL"
                    })

    if not test_tokens:
        console.print("[yellow]Aucun token de test trouvé")
        return

    console.print(f"[cyan]Test sur {len(test_tokens)} tokens...\n")

    # Tester chaque token
    extractor = TokenFeatureExtractor()
    results = []

    for i, token in enumerate(test_tokens, 1):
        console.print(f"[cyan]--- Token {i}/{len(test_tokens)} : {token['name']} ---")
        console.print(f"[dim]Mint: {token['mint'][:16]}...")
        console.print(f"[dim]Attendu: {token['expected']}")

        try:
            # Extraire features
            console.print("[yellow]Extraction features...")
            features = await extractor.extract_all_features(token['mint'])

            if not features:
                console.print("[red][X] Échec extraction features\n")
                continue

            # Prédire
            console.print("[yellow]Prédiction...")
            risk_level, ml_score, details = predictor.predict_with_score(features)

            # Afficher résultat
            console.print(f"\n[bold]PRÉDICTION :")
            console.print(f"  Score ML : [yellow]{ml_score}/100")
            console.print(f"  Classe : [{'green' if details['predicted_class'] == token['expected'] else 'red'}]{details['predicted_class']}")
            console.print(f"  Confiance : [yellow]{details['confidence']:.1f}%")

            # Probabilités
            console.print(f"\n  Probabilités :")
            for classe, prob in details['probabilities'].items():
                color = "green" if prob > 50 else "yellow" if prob > 20 else "dim"
                bar = "█" * int(prob / 5)
                console.print(f"    [{color}]{classe:15} {prob:5.1f}% {bar}")

            # Résultat
            correct = details['predicted_class'] == token['expected']
            if correct:
                console.print(f"\n[green][OK] CORRECT\n")
            else:
                console.print(f"\n[red][X] INCORRECT (attendu: {token['expected']})\n")

            results.append({
                "name": token['name'],
                "expected": token['expected'],
                "predicted": details['predicted_class'],
                "confidence": details['confidence'],
                "correct": correct
            })

        except Exception as e:
            console.print(f"[red][X] Erreur : {e}\n")

    await extractor.close()

    # Résumé
    if results:
        console.print("\n" + "="*60)
        console.print(Panel.fit("[bold cyan]RÉSUMÉ DES TESTS[/]", border_style="cyan"))

        # Table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Token", style="dim")
        table.add_column("Attendu", style="yellow")
        table.add_column("Prédit", style="yellow")
        table.add_column("Confiance", justify="right")
        table.add_column("Résultat", justify="center")

        for r in results:
            table.add_row(
                r['name'][:20],
                r['expected'],
                r['predicted'],
                f"{r['confidence']:.1f}%",
                "[green][OK]" if r['correct'] else "[red][X]"
            )

        console.print(table)

        # Stats
        correct_count = sum(1 for r in results if r['correct'])
        total = len(results)
        accuracy = correct_count / total * 100

        console.print(f"\n[bold]Précision : {accuracy:.1f}% ({correct_count}/{total})")

        if accuracy >= 80:
            console.print("[green][OK] Excellent ! Le modèle fonctionne bien.")
        elif accuracy >= 60:
            console.print("[yellow]⚠️  Correct, mais peut être amélioré avec plus de données.")
        else:
            console.print("[red]⚠️  Précision faible. Ajoutez plus de tokens et réentraînez.")


async def main():
    await test_model()


if __name__ == "__main__":
    asyncio.run(main())
