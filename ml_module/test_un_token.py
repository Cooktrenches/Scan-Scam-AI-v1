"""
Test avec UN seul token
Entrez l'adresse du token et le modele va predire si c'est un RUG ou SUCCESS
"""

import asyncio
from predictor import TokenPredictor
from feature_extractor import TokenFeatureExtractor


async def test_un_token(token_mint: str):
    """Test un seul token"""

    print("=" * 60)
    print("TEST D'UN TOKEN SPECIFIQUE")
    print("=" * 60)

    print(f"\nToken: {token_mint}")
    print("\n[1] Chargement du modele...")

    try:
        predictor = TokenPredictor()
        print("[OK] Modele charge!\n")
    except Exception as e:
        print(f"[ERREUR] {e}")
        return

    print("[2] Extraction des features (75 features)...")
    extractor = TokenFeatureExtractor()

    try:
        features = await extractor.extract_all_features(token_mint)

        if not features:
            print("[ERREUR] Impossible d'extraire les features")
            print("Le token n'existe peut-etre pas ou n'a pas de donnees")
            await extractor.close()
            return

        print("[OK] Features extraites!\n")

        # Predire
        print("[3] Prediction...")
        risk_level, ml_score, details = predictor.predict_with_score(features)

        # Afficher resultats
        print("\n" + "=" * 60)
        print("RESULTAT DE LA PREDICTION")
        print("=" * 60)

        predicted = details['predicted_class']

        if predicted == "RUG":
            print(f"\n[!!!] ATTENTION: Ce token est predit comme un RUG")
            print(f"     Score ML: {ml_score}/100 (0 = RUG)")
        else:
            print(f"\n[OK] Ce token est predit comme SUCCESS/HIGH POTENTIAL")
            print(f"    Score ML: {ml_score}/100 (100 = SUCCESS)")

        print(f"\nConfiance: {details['confidence']:.1f}%")

        print(f"\nProbabilites:")
        for classe, prob in details['probabilities'].items():
            bar_length = int(prob / 5)
            bar = "#" * bar_length
            print(f"  {classe:12} {prob:5.1f}% {bar}")

        print("\n" + "=" * 60)

        # Interpretation
        print("\nINTERPRETATION:")
        if ml_score < 30:
            print("  [DANGER] Score tres bas - Risque eleve de RUG")
            print("  Recommandation: NE PAS INVESTIR")
        elif ml_score < 70:
            print("  [MODERE] Score moyen - Token incertain")
            print("  Recommandation: Prudence, faire plus de recherches")
        else:
            print("  [BON] Score eleve - Token prometteur")
            print("  Recommandation: Potentiel interessant")

        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n[ERREUR] {e}")
        import traceback
        traceback.print_exc()

    await extractor.close()


async def main():
    """Point d'entree"""

    print("\n" + "=" * 60)
    print("TEST IA RUG DETECTOR")
    print("=" * 60)

    # Demander l'adresse du token
    print("\nEntrez l'adresse du token a analyser:")
    token_mint = input("> ").strip()

    if not token_mint:
        print("[ERREUR] Adresse vide!")
        return

    print()
    await test_un_token(token_mint)


if __name__ == "__main__":
    asyncio.run(main())
