"""
ML Predictor - Uses trained model to predict rug/safe/high-potential for tokens
"""

import pickle
from pathlib import Path
from typing import Dict, Optional, Tuple
import numpy as np
from rich.console import Console
from .models.feature_names import FEATURE_NAMES

console = Console()


class TokenPredictor:
    """Predicts token classification using trained ML model"""

    def __init__(self, model_path: Optional[str] = None, scaler_path: Optional[str] = None):
        """
        Initialize predictor with trained model

        Args:
            model_path: Path to trained model pickle file (defaults to latest)
            scaler_path: Path to fitted scaler pickle file (defaults to latest)
        """
        self.models_dir = Path(__file__).parent / "models"

        # Load model
        if model_path is None:
            model_path = self.models_dir / "random_forest_latest.pkl"
        else:
            model_path = Path(model_path)

        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        with open(model_path, "rb") as f:
            self.model = pickle.load(f)

        # Load scaler
        if scaler_path is None:
            scaler_path = self.models_dir / "scaler_latest.pkl"
        else:
            scaler_path = Path(scaler_path)

        if not scaler_path.exists():
            raise FileNotFoundError(f"Scaler not found: {scaler_path}")

        with open(scaler_path, "rb") as f:
            self.scaler = pickle.load(f)

        # Label mapping - detect from model's classes
        model_classes = self.model.classes_
        if len(model_classes) == 2:
            # Binary classification (RUG vs SUCCESS)
            self.label_map = {
                model_classes[0]: "RUG",
                model_classes[1]: "SUCCESS"
            }
        else:
            # 3-class classification
            self.label_map = {
                0: "RUG",
                1: "SAFE",
                2: "HIGH_POTENTIAL"
            }

        console.print(f"[green]ML Model loaded successfully from {model_path.name}")

    def predict(self, features: Dict) -> Tuple[str, float, Dict[str, float]]:
        """
        Predict token classification

        Args:
            features: Dictionary of extracted features

        Returns:
            (predicted_class, confidence, class_probabilities)
        """
        # Convert features dict to array (must match training feature order)
        feature_vector = self._prepare_feature_vector(features)

        # Scale features
        feature_vector_scaled = self.scaler.transform([feature_vector])

        # Predict
        prediction = self.model.predict(feature_vector_scaled)[0]
        probabilities = self.model.predict_proba(feature_vector_scaled)[0]

        # Get class name and confidence
        predicted_class = self.label_map[prediction]
        # Find index of predicted class in model.classes_
        pred_idx = list(self.model.classes_).index(prediction)
        confidence = probabilities[pred_idx] * 100

        # Create probability dict using actual model classes
        prob_dict = {
            self.label_map[class_label]: prob * 100
            for class_label, prob in zip(self.model.classes_, probabilities)
        }

        return predicted_class, confidence, prob_dict

    def predict_with_score(self, features: Dict) -> Tuple[str, int, Dict]:
        """
        Predict and convert to 0-100 score format

        Args:
            features: Dictionary of extracted features

        Returns:
            (risk_level, ml_score, details)
        """
        predicted_class, confidence, probabilities = self.predict(features)

        # Convert to 0-100 score
        # RUG = 0-30, SAFE = 30-70, HIGH_POTENTIAL/SUCCESS = 70-100
        if predicted_class == "RUG":
            ml_score = int(30 * (1 - probabilities["RUG"] / 100))
        elif predicted_class == "SAFE":
            ml_score = int(30 + 40 * (probabilities.get("SAFE", 0) / 100))
        else:  # HIGH_POTENTIAL or SUCCESS
            # For binary model, SUCCESS means high potential
            success_prob = probabilities.get("SUCCESS", probabilities.get("HIGH_POTENTIAL", 100))
            ml_score = int(70 + 30 * (success_prob / 100))

        # Determine risk level
        if ml_score >= 70:
            risk_level = "SAFE"
        elif ml_score >= 30:
            risk_level = "MODERATE"
        else:
            risk_level = "DANGER"

        details = {
            "predicted_class": predicted_class,
            "confidence": round(confidence, 2),
            "probabilities": {k: round(v, 2) for k, v in probabilities.items()},
            "ml_score": ml_score,
            "risk_level": risk_level
        }

        return risk_level, ml_score, details

    def _prepare_feature_vector(self, features: Dict) -> np.ndarray:
        """
        Prepare feature vector from features dict

        Args:
            features: Dictionary of features

        Returns:
            Numpy array of feature values
        """
        # Use explicit feature names from trained model (61 features)
        # This ensures we only use the features the model was trained on
        expected_features = FEATURE_NAMES

        # Extract values in correct order
        feature_vector = []
        for feature_name in expected_features:
            value = features.get(feature_name, 0)  # Default to 0 if missing
            feature_vector.append(value)

        return np.array(feature_vector)

    def explain_prediction(self, features: Dict) -> str:
        """
        Generate human-readable explanation of prediction

        Args:
            features: Dictionary of extracted features

        Returns:
            Explanation string
        """
        risk_level, ml_score, details = self.predict_with_score(features)

        explanation = f"\n[bold cyan]=== ML Prediction ===[/]\n"
        explanation += f"[yellow]Predicted Class: {details['predicted_class']}\n"
        explanation += f"[yellow]Confidence: {details['confidence']:.1f}%\n"
        explanation += f"[yellow]ML Score: {ml_score}/100\n"
        explanation += f"[yellow]Risk Level: {risk_level}\n\n"

        explanation += "[cyan]Class Probabilities:\n"
        for class_name, prob in details['probabilities'].items():
            color = "green" if prob > 50 else "yellow" if prob > 20 else "red"
            explanation += f"  [{color}]{class_name}: {prob:.1f}%\n"

        # Top risk factors (features with high values indicating risk)
        risk_factors = self._get_top_risk_factors(features)
        if risk_factors:
            explanation += "\n[red]Top Risk Factors:\n"
            for factor, value in risk_factors[:5]:
                explanation += f"  - {factor}: {value}\n"

        return explanation

    def _get_top_risk_factors(self, features: Dict) -> list:
        """
        Identify top risk factors from features

        Args:
            features: Dictionary of features

        Returns:
            List of (feature_name, value) tuples sorted by risk
        """
        # Features that indicate risk when high
        risk_indicators = {
            "fresh_wallet_percentage": features.get("fresh_wallet_percentage", 0),
            "top_1_concentration": features.get("top_1_concentration", 0),
            "wash_trading_score": features.get("wash_trading_score", 0),
            "creator_rug_rate": features.get("creator_rug_rate", 0),
            "instant_sniper_count": features.get("instant_sniper_count", 0),
            "bot_holder_percentage": features.get("bot_holder_percentage", 0),
            "volume_to_mcap_ratio": features.get("volume_to_mcap_ratio", 0),
            "price_volatility_24h": features.get("price_volatility_24h", 0)
        }

        # Sort by value (descending)
        sorted_factors = sorted(
            risk_indicators.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_factors


def main():
    """Test predictor"""
    console.print("[cyan]Testing ML Predictor...\n")

    try:
        predictor = TokenPredictor()

        # Test with dummy features
        test_features = {
            "fresh_wallet_percentage": 45,
            "holder_count": 150,
            "top_10_concentration": 75,
            "volume_to_mcap_ratio": 30,
            "creator_rug_rate": 0.8,
            "wash_trading_score": 85,
            # ... other features would be here
        }

        risk_level, ml_score, details = predictor.predict_with_score(test_features)

        console.print(f"[yellow]Risk Level: {risk_level}")
        console.print(f"[yellow]ML Score: {ml_score}/100")
        console.print(f"[yellow]Predicted Class: {details['predicted_class']}")
        console.print(f"[yellow]Confidence: {details['confidence']:.1f}%")

        explanation = predictor.explain_prediction(test_features)
        console.print(explanation)

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}")
        console.print("[yellow]Please train a model first using model_trainer.py")


if __name__ == "__main__":
    main()
