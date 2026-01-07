"""
Example integration of ML predictions into the existing scanner
This shows how to combine rule-based scoring with ML predictions
"""

import asyncio
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from ml_module.predictor import TokenPredictor
from ml_module.feature_extractor import TokenFeatureExtractor
from rich.console import Console

console = Console()


class MLIntegratedScanner:
    """
    Enhanced scanner that combines rule-based analysis with ML predictions

    This is an example of how to integrate the ML module into your existing scanner.
    """

    def __init__(self):
        """Initialize scanner with ML capabilities"""

        # Try to load ML model
        try:
            self.ml_predictor = TokenPredictor()
            self.ml_enabled = True
            console.print("[green]ML predictor loaded successfully!")
        except FileNotFoundError:
            self.ml_predictor = None
            self.ml_enabled = False
            console.print("[yellow]ML model not found. Running in rule-based mode only.")
            console.print("[yellow]Train a model first: python ml_module/model_trainer.py")

        # Feature extractor
        self.feature_extractor = TokenFeatureExtractor()

    async def get_ml_prediction(self, token_data: dict) -> dict:
        """
        Get ML prediction for a token

        Args:
            token_data: Token data from your existing analysis

        Returns:
            Dictionary with ML prediction results
        """
        if not self.ml_enabled:
            return {
                "enabled": False,
                "ml_score": 50,  # Neutral score if ML not available
                "predicted_class": "UNKNOWN",
                "confidence": 0,
                "probabilities": {}
            }

        try:
            # Extract features from token data
            # This uses the feature extractor to get all 60+ features
            mint_address = token_data.get("mint_address")

            if not mint_address:
                return self._default_ml_result()

            features = await self.feature_extractor.extract_all_features(mint_address)

            if not features:
                return self._default_ml_result()

            # Get ML prediction
            risk_level, ml_score, details = self.ml_predictor.predict_with_score(features)

            return {
                "enabled": True,
                "ml_score": ml_score,
                "predicted_class": details["predicted_class"],
                "confidence": details["confidence"],
                "probabilities": details["probabilities"],
                "risk_level": risk_level
            }

        except Exception as e:
            console.print(f"[red]ML prediction error: {e}")
            return self._default_ml_result()

    def combine_scores(
        self,
        rule_based_score: int,
        ml_prediction: dict,
        ml_weight: float = 0.3
    ) -> dict:
        """
        Combine rule-based score with ML prediction

        Args:
            rule_based_score: Score from existing rule-based analysis (0-100)
            ml_prediction: ML prediction dictionary
            ml_weight: Weight for ML score (0.0-1.0), default 0.3 (30%)

        Returns:
            Dictionary with combined results
        """
        # If ML not enabled, use only rule-based score
        if not ml_prediction.get("enabled", False):
            return {
                "combined_score": rule_based_score,
                "rule_based_score": rule_based_score,
                "ml_score": None,
                "ml_enabled": False,
                "verdict": self._get_verdict(rule_based_score)
            }

        # Combine scores (weighted average)
        ml_score = ml_prediction["ml_score"]
        combined_score = int(
            (1 - ml_weight) * rule_based_score + ml_weight * ml_score
        )

        # Determine final verdict
        verdict = self._get_verdict(combined_score)

        return {
            "combined_score": combined_score,
            "rule_based_score": rule_based_score,
            "ml_score": ml_score,
            "ml_enabled": True,
            "ml_predicted_class": ml_prediction["predicted_class"],
            "ml_confidence": ml_prediction["confidence"],
            "verdict": verdict,
            "breakdown": {
                "rule_weight": 1 - ml_weight,
                "ml_weight": ml_weight
            }
        }

    def _get_verdict(self, score: int) -> str:
        """Get verdict based on score"""
        if score >= 75:
            return "EXTREME DANGER"
        elif score >= 50:
            return "HIGH RISK"
        elif score >= 25:
            return "MEDIUM RISK"
        else:
            return "LOW RISK"

    def _default_ml_result(self) -> dict:
        """Default ML result when prediction fails"""
        return {
            "enabled": False,
            "ml_score": 50,
            "predicted_class": "UNKNOWN",
            "confidence": 0,
            "probabilities": {}
        }

    async def close(self):
        """Close resources"""
        await self.feature_extractor.close()


# ============================================================
# Example Usage
# ============================================================

async def example_integration():
    """Example of how to use ML-integrated scanner"""

    scanner = MLIntegratedScanner()

    # Simulate token data from your existing analysis
    token_data = {
        "mint_address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC example
        "name": "Example Token",
        "symbol": "EX"
    }

    # Simulate rule-based score from your existing scanner
    rule_based_score = 65  # Example: existing scanner gave 65/100 risk

    console.print("[bold cyan]=== ML Integration Example ===[/]\n")

    # Get ML prediction
    console.print("[cyan]Getting ML prediction...")
    ml_prediction = await scanner.get_ml_prediction(token_data)

    # Combine scores
    console.print("[cyan]Combining scores...\n")
    result = scanner.combine_scores(rule_based_score, ml_prediction, ml_weight=0.3)

    # Display results
    console.print("[bold green]=== Analysis Results ===[/]")
    console.print(f"\n[yellow]Rule-Based Score: {result['rule_based_score']}/100")

    if result['ml_enabled']:
        console.print(f"[yellow]ML Score: {result['ml_score']}/100")
        console.print(f"[yellow]ML Predicted Class: {result['ml_predicted_class']}")
        console.print(f"[yellow]ML Confidence: {result['ml_confidence']:.1f}%")
        console.print(f"\n[bold cyan]Combined Score: {result['combined_score']}/100")
        console.print(f"[bold cyan]Verdict: {result['verdict']}")

        console.print(f"\n[cyan]Score Breakdown:")
        console.print(f"  Rule-based weight: {result['breakdown']['rule_weight']*100:.0f}%")
        console.print(f"  ML weight: {result['breakdown']['ml_weight']*100:.0f}%")
    else:
        console.print(f"[yellow]ML: Not available")
        console.print(f"\n[bold cyan]Final Score: {result['combined_score']}/100")
        console.print(f"[bold cyan]Verdict: {result['verdict']}")

    await scanner.close()


# ============================================================
# Integration with risk_scorer.py
# ============================================================

def integrate_with_risk_scorer():
    """
    Example of how to modify risk_scorer.py to include ML predictions

    Add this to your risk_scorer.py:
    """

    example_code = '''
# In risk_scorer.py, add ML integration:

from ml_module.predictor import TokenPredictor
from ml_module.feature_extractor import TokenFeatureExtractor

class RiskScorer:
    """Enhanced with ML predictions"""

    def __init__(self):
        # Try to load ML predictor
        try:
            self.ml_predictor = TokenPredictor()
            self.ml_enabled = True
        except FileNotFoundError:
            self.ml_predictor = None
            self.ml_enabled = False

    @staticmethod
    def calculate_risk(
        distribution_analysis,
        creator_analysis,
        liquidity_analysis,
        social_analysis,
        wallet_analysis=None,
        sniper_analysis=None,
        volume_analysis=None,
        distribution_metrics=None,
        onchain_data=None,
        pump_dump_analysis=None,
        ml_prediction=None  # NEW: Add ML prediction parameter
    ) -> RiskReport:
        """Calculate weighted overall risk score with ML"""

        # ... existing code for calculating overall_score ...

        # NEW: If ML prediction available, combine with rule-based score
        if ml_prediction and ml_prediction.get("enabled"):
            ml_score = ml_prediction["ml_score"]
            # Combine: 70% rule-based + 30% ML
            overall_score = int(0.7 * overall_score + 0.3 * ml_score)

        # ... rest of existing code ...

        return RiskReport(
            overall_risk_score=overall_score,
            ml_score=ml_prediction.get("ml_score") if ml_prediction else None,  # NEW
            ml_predicted_class=ml_prediction.get("predicted_class") if ml_prediction else None,  # NEW
            # ... rest of fields ...
        )
'''

    console.print("[cyan]Integration code for risk_scorer.py:")
    console.print(example_code)


if __name__ == "__main__":
    # Run example
    asyncio.run(example_integration())

    # Show integration guide
    console.print("\n" + "="*60 + "\n")
    integrate_with_risk_scorer()
