"""
Model Trainer - Trains ML models to classify tokens as rug/safe/high-potential
"""

import json
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, List
from datetime import datetime

from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_recall_fscore_support,
    roc_auc_score
)
from imblearn.over_sampling import SMOTE

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class TokenClassifierTrainer:
    """Trains ML models to classify tokens"""

    def __init__(self):
        self.dataset_dir = Path(__file__).parent / "dataset"
        self.models_dir = Path(__file__).parent / "models"
        self.models_dir.mkdir(exist_ok=True)

        self.model = None
        self.scaler = None
        self.feature_names = None

        # Label mapping
        self.label_map = {
            "rug": 0,
            "safe": 1,
            "success": 2
        }
        self.inverse_label_map = {v: k for k, v in self.label_map.items()}

    def load_training_data(self) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Load and prepare training data from dataset files

        Returns:
            (features_df, labels_array)
        """
        console.print("[cyan]Loading training data...")

        features_csv = self.dataset_dir / "features.csv"

        if not features_csv.exists():
            console.print(f"[red]Error: {features_csv} not found!")
            console.print("[yellow]Please run feature extraction first.")
            return None, None

        # Load features
        df = pd.read_csv(features_csv)

        # Separate features and labels
        if "label" not in df.columns:
            console.print("[red]Error: 'label' column not found in dataset!")
            return None, None

        X = df.drop(columns=["label", "token_mint", "timestamp"], errors="ignore")
        y = df["label"].values

        console.print(f"[green]Loaded {len(df)} samples with {len(X.columns)} features")

        # Display class distribution
        unique, counts = np.unique(y, return_counts=True)
        table = Table(title="Class Distribution")
        table.add_column("Class", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Percentage", style="yellow")

        for label, count in zip(unique, counts):
            label_name = self.inverse_label_map.get(label, "unknown")
            pct = count / len(y) * 100
            table.add_row(label_name, str(count), f"{pct:.1f}%")

        console.print(table)

        self.feature_names = X.columns.tolist()

        return X, y

    def preprocess_data(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        test_size: float = 0.2,
        balance_classes: bool = True
    ) -> Tuple:
        """
        Preprocess data: split, scale, balance

        Args:
            X: Features dataframe
            y: Labels array
            test_size: Test set proportion
            balance_classes: Whether to use SMOTE for class balancing

        Returns:
            (X_train, X_test, y_train, y_test, scaler)
        """
        console.print("[cyan]Preprocessing data...")

        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=42,
            stratify=y
        )

        console.print(f"[green]Train set: {len(X_train)} samples")
        console.print(f"[green]Test set: {len(X_test)} samples")

        # Feature scaling
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Class balancing with SMOTE
        if balance_classes:
            console.print("[cyan]Balancing classes with SMOTE...")
            smote = SMOTE(random_state=42)
            X_train_scaled, y_train = smote.fit_resample(X_train_scaled, y_train)
            console.print(f"[green]Balanced train set: {len(X_train_scaled)} samples")

        self.scaler = scaler

        return X_train_scaled, X_test_scaled, y_train, y_test

    def train_random_forest(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        tune_hyperparameters: bool = False
    ) -> RandomForestClassifier:
        """
        Train Random Forest classifier

        Args:
            X_train: Training features
            y_train: Training labels
            tune_hyperparameters: Whether to perform hyperparameter tuning

        Returns:
            Trained model
        """
        console.print("[cyan]Training Random Forest model...")

        if tune_hyperparameters:
            console.print("[yellow]Performing hyperparameter tuning...")

            param_grid = {
                'n_estimators': [100, 200, 300],
                'max_depth': [10, 20, 30, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'max_features': ['sqrt', 'log2']
            }

            rf = RandomForestClassifier(random_state=42)
            grid_search = GridSearchCV(
                rf,
                param_grid,
                cv=5,
                scoring='f1_weighted',
                n_jobs=-1,
                verbose=1
            )

            grid_search.fit(X_train, y_train)
            model = grid_search.best_estimator_

            console.print(f"[green]Best parameters: {grid_search.best_params_}")

        else:
            # Default parameters
            model = RandomForestClassifier(
                n_estimators=200,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                max_features='sqrt',
                random_state=42,
                n_jobs=-1
            )

            model.fit(X_train, y_train)

        console.print("[green]Model trained successfully!")

        return model

    def train_gradient_boosting(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray
    ) -> GradientBoostingClassifier:
        """
        Train Gradient Boosting classifier

        Args:
            X_train: Training features
            y_train: Training labels

        Returns:
            Trained model
        """
        console.print("[cyan]Training Gradient Boosting model...")

        model = GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )

        model.fit(X_train, y_train)

        console.print("[green]Model trained successfully!")

        return model

    def evaluate_model(
        self,
        model,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict:
        """
        Evaluate model performance

        Args:
            model: Trained model
            X_test: Test features
            y_test: Test labels

        Returns:
            Dictionary of evaluation metrics
        """
        console.print("\n[cyan]Evaluating model...")

        # Predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)

        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average='weighted'
        )

        # Try to calculate ROC AUC (only for binary/multiclass)
        try:
            roc_auc = roc_auc_score(y_test, y_pred_proba, multi_class='ovr', average='weighted')
        except:
            roc_auc = None

        # Display results
        console.print(f"\n[bold green]=== Model Evaluation ===[/]")
        console.print(f"Accuracy:  {accuracy:.3f}")
        console.print(f"Precision: {precision:.3f}")
        console.print(f"Recall:    {recall:.3f}")
        console.print(f"F1-Score:  {f1:.3f}")
        if roc_auc:
            console.print(f"ROC-AUC:   {roc_auc:.3f}")

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        console.print("\n[cyan]Confusion Matrix:")
        console.print(cm)

        # Classification report
        console.print("\n[cyan]Classification Report:")
        # Only use classes present in the test set
        unique_classes = sorted(set(y_test) | set(y_pred))
        target_names = [self.inverse_label_map[i] for i in unique_classes if i in self.inverse_label_map]
        report = classification_report(
            y_test,
            y_pred,
            labels=unique_classes,
            target_names=target_names
        )
        console.print(report)

        # Feature importance
        if hasattr(model, 'feature_importances_'):
            self._display_feature_importance(model)

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'roc_auc': roc_auc,
            'confusion_matrix': cm.tolist()
        }

    def _display_feature_importance(self, model, top_n: int = 15):
        """Display top N most important features"""
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1][:top_n]

        table = Table(title=f"Top {top_n} Most Important Features")
        table.add_column("Rank", style="cyan")
        table.add_column("Feature", style="green")
        table.add_column("Importance", style="yellow")

        for rank, idx in enumerate(indices, 1):
            feature_name = self.feature_names[idx]
            importance = importances[idx]
            table.add_row(str(rank), feature_name, f"{importance:.4f}")

        console.print(table)

    def save_model(self, model, scaler, metrics: Dict, model_name: str = "token_classifier"):
        """
        Save trained model and scaler

        Args:
            model: Trained model
            scaler: Fitted scaler
            metrics: Evaluation metrics
            model_name: Name for saved model
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_file = self.models_dir / f"{model_name}_{timestamp}.pkl"
        scaler_file = self.models_dir / f"scaler_{timestamp}.pkl"
        metrics_file = self.models_dir / f"metrics_{timestamp}.json"

        # Save model
        with open(model_file, "wb") as f:
            pickle.dump(model, f)
        console.print(f"[green]Model saved to {model_file.name}")

        # Save scaler
        with open(scaler_file, "wb") as f:
            pickle.dump(scaler, f)
        console.print(f"[green]Scaler saved to {scaler_file.name}")

        # Save metrics
        with open(metrics_file, "w") as f:
            json.dump(metrics, f, indent=2)
        console.print(f"[green]Metrics saved to {metrics_file.name}")

        # Save also as "latest" for easy loading
        latest_model = self.models_dir / f"{model_name}_latest.pkl"
        latest_scaler = self.models_dir / "scaler_latest.pkl"

        with open(latest_model, "wb") as f:
            pickle.dump(model, f)
        with open(latest_scaler, "wb") as f:
            pickle.dump(scaler, f)

        console.print(f"[green]Also saved as latest versions")

    def train_full_pipeline(
        self,
        model_type: str = "random_forest",
        tune_hyperparameters: bool = False
    ):
        """
        Complete training pipeline

        Args:
            model_type: "random_forest" or "gradient_boosting"
            tune_hyperparameters: Whether to tune hyperparameters
        """
        console.print("[bold cyan]=== ML Model Training Pipeline ===[/]\n")

        # Load data
        X, y = self.load_training_data()
        if X is None:
            return

        # Preprocess
        X_train, X_test, y_train, y_test = self.preprocess_data(X, y)

        # Train model
        if model_type == "random_forest":
            model = self.train_random_forest(X_train, y_train, tune_hyperparameters)
        elif model_type == "gradient_boosting":
            model = self.train_gradient_boosting(X_train, y_train)
        else:
            console.print(f"[red]Unknown model type: {model_type}")
            return

        # Evaluate
        metrics = self.evaluate_model(model, X_test, y_test)

        # Save
        self.save_model(model, self.scaler, metrics, model_name=model_type)

        console.print("\n[bold green]=== Training Complete! ===[/]")


def main():
    """Main entry point for model training"""
    trainer = TokenClassifierTrainer()

    # Train Random Forest (default)
    trainer.train_full_pipeline(
        model_type="random_forest",
        tune_hyperparameters=False  # Set to True for hyperparameter tuning
    )


if __name__ == "__main__":
    main()
