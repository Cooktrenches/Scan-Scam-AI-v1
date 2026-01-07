"""
Complete ML Workflow - From data collection to prediction
This script demonstrates the full ML pipeline for token classification
"""

import asyncio
import json
import pandas as pd
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from data_collector import HistoricalDataCollector
from feature_extractor import TokenFeatureExtractor
from model_trainer import TokenClassifierTrainer
from predictor import TokenPredictor

console = Console()


class MLWorkflowManager:
    """Manages the complete ML workflow"""

    def __init__(self):
        self.dataset_dir = Path(__file__).parent / "dataset"
        self.dataset_dir.mkdir(exist_ok=True)

    async def step1_collect_data(self, num_tokens: int = 500):
        """
        Step 1: Collect historical token data

        Args:
            num_tokens: Number of tokens to collect
        """
        console.print(Panel.fit(
            "[bold cyan]STEP 1: Collecting Historical Data[/]",
            border_style="cyan"
        ))

        collector = HistoricalDataCollector()

        try:
            await collector.collect_training_data(num_tokens=num_tokens)
            console.print("[green]Data collection complete!")
        finally:
            await collector.close()

    async def step2_extract_features(self):
        """
        Step 2: Extract features from collected tokens
        """
        console.print(Panel.fit(
            "[bold cyan]STEP 2: Extracting Features[/]",
            border_style="cyan"
        ))

        # Load datasets
        rugs_file = self.dataset_dir / "rugs.json"
        success_file = self.dataset_dir / "success.json"

        if not rugs_file.exists() or not success_file.exists():
            console.print("[red]Error: Dataset files not found!")
            console.print("[yellow]Please run step 1 first: collect_data()")
            return

        with open(rugs_file) as f:
            rugs = json.load(f)
        with open(success_file) as f:
            successes = json.load(f)

        console.print(f"[cyan]Loaded {len(rugs)} rugs and {len(successes)} successes")

        # Extract features
        extractor = TokenFeatureExtractor()
        all_features = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                "Extracting features...",
                total=len(rugs) + len(successes)
            )

            # Process rugs
            for token in rugs:
                mint = token.get("mint")
                if mint:
                    features = await extractor.extract_all_features(mint)
                    if features:
                        features["label"] = 0  # RUG
                        all_features.append(features)
                    progress.update(task, advance=1)
                    await asyncio.sleep(0.3)  # Rate limiting

            # Process successes
            for token in successes:
                mint = token.get("mint")
                if mint:
                    features = await extractor.extract_all_features(mint)
                    if features:
                        features["label"] = 2  # HIGH_POTENTIAL
                        all_features.append(features)
                    progress.update(task, advance=1)
                    await asyncio.sleep(0.3)  # Rate limiting

        await extractor.close()

        # Save to CSV
        if all_features:
            df = pd.DataFrame(all_features)
            features_file = self.dataset_dir / "features.csv"
            df.to_csv(features_file, index=False)
            console.print(f"[green]Saved {len(df)} feature sets to {features_file.name}")
        else:
            console.print("[red]No features extracted!")

    def step3_train_model(self, model_type: str = "random_forest"):
        """
        Step 3: Train ML model

        Args:
            model_type: "random_forest" or "gradient_boosting"
        """
        console.print(Panel.fit(
            "[bold cyan]STEP 3: Training ML Model[/]",
            border_style="cyan"
        ))

        trainer = TokenClassifierTrainer()
        trainer.train_full_pipeline(model_type=model_type)

    async def step4_test_prediction(self, test_mint: str = None):
        """
        Step 4: Test model predictions

        Args:
            test_mint: Token mint address to test (optional)
        """
        console.print(Panel.fit(
            "[bold cyan]STEP 4: Testing Predictions[/]",
            border_style="cyan"
        ))

        try:
            predictor = TokenPredictor()
            extractor = TokenFeatureExtractor()

            # If no test mint provided, use a sample from dataset
            if test_mint is None:
                rugs_file = self.dataset_dir / "rugs.json"
                if rugs_file.exists():
                    with open(rugs_file) as f:
                        rugs = json.load(f)
                        if rugs:
                            test_mint = rugs[0].get("mint")

            if not test_mint:
                console.print("[yellow]No test token available")
                return

            console.print(f"[cyan]Testing prediction for: {test_mint}\n")

            # Extract features
            features = await extractor.extract_all_features(test_mint)

            if not features:
                console.print("[red]Failed to extract features")
                await extractor.close()
                return

            # Predict
            risk_level, ml_score, details = predictor.predict_with_score(features)

            # Display results
            console.print("[bold green]=== Prediction Results ===[/]")
            console.print(f"[yellow]ML Score: {ml_score}/100")
            console.print(f"[yellow]Risk Level: {risk_level}")
            console.print(f"[yellow]Predicted Class: {details['predicted_class']}")
            console.print(f"[yellow]Confidence: {details['confidence']:.1f}%\n")

            console.print("[cyan]Class Probabilities:")
            for class_name, prob in details['probabilities'].items():
                color = "green" if prob > 50 else "yellow" if prob > 20 else "red"
                console.print(f"  [{color}]{class_name}: {prob:.1f}%")

            await extractor.close()

        except FileNotFoundError:
            console.print("[red]Model not found! Please train a model first.")

    async def run_complete_workflow(
        self,
        num_tokens: int = 500,
        model_type: str = "random_forest",
        test_after: bool = True
    ):
        """
        Run complete workflow from data collection to prediction

        Args:
            num_tokens: Number of tokens to collect
            model_type: ML model to train
            test_after: Whether to test predictions after training
        """
        console.print(Panel.fit(
            "[bold yellow]Starting Complete ML Workflow[/]\n"
            f"Tokens: {num_tokens} | Model: {model_type}",
            border_style="yellow"
        ))

        # Step 1: Collect data
        await self.step1_collect_data(num_tokens=num_tokens)

        # Step 2: Extract features
        await self.step2_extract_features()

        # Step 3: Train model
        self.step3_train_model(model_type=model_type)

        # Step 4: Test predictions
        if test_after:
            await self.step4_test_prediction()

        console.print("\n" + "="*60)
        console.print(Panel.fit(
            "[bold green]Workflow Complete![/]\n"
            "You can now use the trained model in your scanner.",
            border_style="green"
        ))


async def main():
    """Main entry point"""

    manager = MLWorkflowManager()

    console.print("""
[bold cyan]ML Workflow Manager[/]

This script helps you set up the ML system for token classification.

[yellow]Options:[/]
1. Run complete workflow (collect + extract + train + test)
2. Collect data only
3. Extract features only
4. Train model only
5. Test predictions only

[cyan]Enter your choice (1-5):[/]
    """)

    # For automated demo, run option 1
    choice = "5"  # Change this to test different steps

    if choice == "1":
        await manager.run_complete_workflow(num_tokens=500)
    elif choice == "2":
        await manager.step1_collect_data(num_tokens=500)
    elif choice == "3":
        await manager.step2_extract_features()
    elif choice == "4":
        manager.step3_train_model()
    elif choice == "5":
        await manager.step4_test_prediction()

    console.print("\n[green]Done!")


if __name__ == "__main__":
    asyncio.run(main())
