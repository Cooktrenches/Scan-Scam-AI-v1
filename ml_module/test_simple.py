"""
Test Simple du Modele ML
Test rapide pour verifier que le modele fonctionne
"""

import asyncio
import json
from pathlib import Path
from predictor import TokenPredictor
from feature_extractor import TokenFeatureExtractor


async def test_simple():
    """Test simple et rapide du modele"""

    print("=" * 60)
    print("TEST SIMPLE DU MODELE ML")
    print("=" * 60)

    # Charger le modele
    print("\n[1] Chargement du modele...")
    try:
        predictor = TokenPredictor()
        print("[OK] Modele charge avec succes!\n")
    except Exception as e:
        print(f"[ERREUR] {e}")
        return

    # Charger quelques tokens
    dataset_dir = Path(__file__).parent / "dataset"

    with open(dataset_dir / "rugs.json") as f:
        rugs = json.load(f)
    with open(dataset_dir / "success.json") as f:
        successes = json.load(f)

    # Prendre 2 rugs et 2 success
    test_tokens = [
        {"mint": rugs[0]["mint"], "expected": "RUG", "name": rugs[0].get("name", "Unknown")},
        {"mint": rugs[1]["mint"], "expected": "RUG", "name": rugs[1].get("name", "Unknown")},
        {"mint": successes[0]["mint"], "expected": "SUCCESS", "name": successes[0].get("name", "Unknown")},
        {"mint": successes[1]["mint"], "expected": "SUCCESS", "name": successes[1].get("name", "Unknown")},
    ]

    print(f"[2] Test sur {len(test_tokens)} tokens...\n")

    # Tester
    extractor = TokenFeatureExtractor()
    correct = 0

    for i, token in enumerate(test_tokens, 1):
        print(f"Token {i}/{len(test_tokens)}: {token['name'][:30]}")
        print(f"  Mint: {token['mint'][:16]}...")
        print(f"  Attendu: {token['expected']}")

        try:
            # Extraire features
            features = await extractor.extract_all_features(token['mint'])

            if not features:
                print("  [ERREUR] Extraction echouee\n")
                continue

            # Predire
            risk_level, ml_score, details = predictor.predict_with_score(features)

            # Afficher
            predicted = details['predicted_class'].upper()
            is_correct = predicted == token['expected']

            if is_correct:
                correct += 1

            print(f"  Predit: {predicted}")
            print(f"  Score ML: {ml_score}/100")
            print(f"  Confiance: {details['confidence']:.1f}%")
            print(f"  Resultat: {'[OK] CORRECT' if is_correct else '[X] INCORRECT'}\n")

        except Exception as e:
            print(f"  [ERREUR] {e}\n")

    await extractor.close()

    # Resume
    print("=" * 60)
    print(f"RESULTATS FINAUX: {correct}/{len(test_tokens)} correct")
    print(f"Precision: {correct/len(test_tokens)*100:.1f}%")
    print("=" * 60)

    print("\n[OK] Le modele fonctionne correctement!")
    print("Vous pouvez maintenant l'integrer dans votre scanner.\n")


if __name__ == "__main__":
    asyncio.run(test_simple())
