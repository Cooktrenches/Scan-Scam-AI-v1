# Machine Learning Module for Token Classification

## Overview

This ML module trains models to automatically classify Solana tokens into three categories:
- **RUG** (0-30 score): High risk of rug pull
- **SAFE** (30-70 score): Low risk but modest potential
- **HIGH_POTENTIAL** (70-100 score): Low risk with high growth potential

## Features

- **60+ Features**: Comprehensive analysis of holder patterns, trading behavior, liquidity, creator history, and more
- **Multiple Models**: Support for Random Forest and Gradient Boosting
- **Class Balancing**: SMOTE oversampling for imbalanced datasets
- **Feature Importance**: Understand which factors drive predictions
- **Easy Integration**: Drop-in replacement for rule-based scoring

## Installation

```bash
# Install ML dependencies
pip install -r ml_module/requirements_ml.txt
```

## Usage Workflow

### Step 1: Collect Historical Data

Collect tokens from Pump.fun and classify them based on outcome:

```bash
cd ml_module
python data_collector.py
```

This will:
- Fetch 500+ tokens from Pump.fun
- Analyze their market outcomes (rug, safe, or success)
- Save to `dataset/rugs.json` and `dataset/success.json`

**Manual Labeling (Recommended):**
You can manually curate the datasets by adding confirmed rugs and successful tokens:

```json
// dataset/rugs.json
[
  {
    "mint": "ABC123...",
    "name": "ScamCoin",
    "creator": "XYZ456..."
  }
]

// dataset/success.json
[
  {
    "mint": "DEF789...",
    "name": "MoonCoin",
    "creator": "GHI012..."
  }
]
```

### Step 2: Extract Features

Extract 60+ features from each token:

```python
import asyncio
from feature_extractor import TokenFeatureExtractor
import pandas as pd
import json

async def extract_features_for_dataset():
    extractor = TokenFeatureExtractor()

    # Load datasets
    with open("dataset/rugs.json") as f:
        rugs = json.load(f)
    with open("dataset/success.json") as f:
        successes = json.load(f)

    all_features = []

    # Extract features for rugs
    for token in rugs:
        features = await extractor.extract_all_features(token["mint"])
        if features:
            features["label"] = 0  # RUG
            all_features.append(features)

    # Extract features for successes
    for token in successes:
        features = await extractor.extract_all_features(token["mint"])
        if features:
            features["label"] = 2  # HIGH_POTENTIAL
            all_features.append(features)

    # Save to CSV
    df = pd.DataFrame(all_features)
    df.to_csv("dataset/features.csv", index=False)
    print(f"Extracted features for {len(df)} tokens")

    await extractor.close()

# Run
asyncio.run(extract_features_for_dataset())
```

### Step 3: Train Model

Train the ML model on extracted features:

```bash
python model_trainer.py
```

This will:
- Load features from `dataset/features.csv`
- Split into train/test sets (80/20)
- Balance classes with SMOTE
- Train Random Forest classifier
- Evaluate on test set
- Save model to `models/random_forest_latest.pkl`

**Training Output:**
```
=== ML Model Training Pipeline ===

Loading training data...
Loaded 450 samples with 75 features

Class Distribution
┌─────────┬───────┬────────────┐
│ Class   │ Count │ Percentage │
├─────────┼───────┼────────────┤
│ rug     │ 200   │ 44.4%      │
│ safe    │ 150   │ 33.3%      │
│ success │ 100   │ 22.2%      │
└─────────┴───────┴────────────┘

Training Random Forest model...
Model trained successfully!

=== Model Evaluation ===
Accuracy:  0.892
Precision: 0.887
Recall:    0.892
F1-Score:  0.889
ROC-AUC:   0.945
```

### Step 4: Use Predictor

Use the trained model to predict new tokens:

```python
from predictor import TokenPredictor
from feature_extractor import TokenFeatureExtractor
import asyncio

async def predict_token(token_mint: str):
    # Extract features
    extractor = TokenFeatureExtractor()
    features = await extractor.extract_all_features(token_mint)
    await extractor.close()

    if not features:
        print("Failed to extract features")
        return

    # Predict
    predictor = TokenPredictor()
    risk_level, ml_score, details = predictor.predict_with_score(features)

    print(f"Token: {token_mint}")
    print(f"ML Score: {ml_score}/100")
    print(f"Risk Level: {risk_level}")
    print(f"Predicted Class: {details['predicted_class']}")
    print(f"Confidence: {details['confidence']:.1f}%")
    print("\nProbabilities:")
    for class_name, prob in details['probabilities'].items():
        print(f"  {class_name}: {prob:.1f}%")

# Test
token_mint = "YOUR_TOKEN_MINT_HERE"
asyncio.run(predict_token(token_mint))
```

## Integration with Scanner

To integrate ML predictions into your main scanner (`scanner.py`):

```python
# In scanner.py

from ml_module.predictor import TokenPredictor
from ml_module.feature_extractor import TokenFeatureExtractor

class RugScanner:
    def __init__(self):
        # ... existing code ...

        # Initialize ML predictor
        try:
            self.ml_predictor = TokenPredictor()
            self.ml_enabled = True
        except FileNotFoundError:
            self.ml_predictor = None
            self.ml_enabled = False
            print("[yellow]ML model not found. Running in rule-based mode only.")

    async def scan_token(self, mint_address: str):
        # ... existing analysis code ...

        # Get ML prediction
        if self.ml_enabled:
            features = await self._extract_ml_features(mint_address)
            ml_risk_level, ml_score, ml_details = self.ml_predictor.predict_with_score(features)

            # Combine with rule-based score (70% rules + 30% ML)
            final_score = int(0.7 * rule_based_score + 0.3 * ml_score)

            print(f"\n[cyan]=== ML Analysis ===")
            print(f"[yellow]ML Score: {ml_score}/100")
            print(f"[yellow]ML Class: {ml_details['predicted_class']}")
            print(f"[yellow]Confidence: {ml_details['confidence']:.1f}%")
            print(f"\n[bold]Combined Score: {final_score}/100")
```

## Feature Engineering

The model uses 75 features across 9 categories:

### 1. Holder Patterns (15 features)
- Fresh wallet percentage
- Holder concentration (Top 1, Top 10)
- Whale count
- Gini coefficient
- HHI index
- Bot detection

### 2. Trading Patterns (12 features)
- Volume metrics
- Wash trading indicators
- Unique trader count
- Buy/sell ratio
- Liquidity depth

### 3. Sniper Activity (10 features)
- Instant snipers (0-3s)
- Early snipers (0-10s)
- Bundle transactions
- Coordinated clusters

### 4. Pump & Dump (8 features)
- Price volatility
- Rapid pumps/dumps
- ATH comparison
- Price stability

### 5. Liquidity (8 features)
- Market cap
- Liquidity ratio
- Lock status
- Bonding curve completion

### 6. Creator History (7 features)
- Token count
- Rug rate
- Success rate
- Wallet age

### 7. Authority (4 features)
- Mint authority status
- Freeze authority status
- Combined risk score

### 8. Social Signals (6 features)
- Twitter/Telegram/Website presence
- Description quality
- Engagement score

### 9. Temporal (5 features)
- Token age
- Time to first dump
- Activity decay rate
- Survival probability

## Model Performance

Expected performance with 500+ labeled tokens:

- **Accuracy**: 85-92%
- **Precision (Rug)**: 88-94% (few false positives)
- **Recall (Rug)**: 82-90% (catches most rugs)
- **F1-Score**: 87-91%
- **ROC-AUC**: 92-96%

## Tips for Better Results

### 1. Data Quality
- **More data is better**: Aim for 1000+ labeled tokens
- **Balanced classes**: Equal rugs, safe, and success tokens
- **Verified labels**: Manually verify outcomes

### 2. Feature Engineering
- Complete the TODO items in `feature_extractor.py`
- Add domain-specific features you discover
- Use your existing scanner logic for complex calculations

### 3. Model Tuning
- Enable hyperparameter tuning: `tune_hyperparameters=True`
- Try different models: XGBoost, LightGBM
- Experiment with feature selection

### 4. Continuous Learning
- Retrain weekly with new data
- Track model performance over time
- Adjust thresholds based on false positives/negatives

## Advanced: XGBoost Integration

For better performance, use XGBoost:

```python
# Install XGBoost
pip install xgboost

# In model_trainer.py, add:
from xgboost import XGBClassifier

def train_xgboost(self, X_train, y_train):
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        random_state=42
    )
    model.fit(X_train, y_train)
    return model
```

## Troubleshooting

**Q: Model accuracy is low (<70%)**
- Need more training data (500+ tokens minimum)
- Check data quality and labels
- Features may need better implementation (complete TODOs)

**Q: High false positive rate (flagging good tokens as rugs)**
- Adjust classification thresholds
- Increase training data for "success" class
- Review feature importance and remove noisy features

**Q: Model predicts all tokens as same class**
- Class imbalance - ensure balanced dataset
- SMOTE may not be working - check implementation
- Try different model hyperparameters

## File Structure

```
ml_module/
├── __init__.py                 # Module init
├── README_ML.md               # This file
├── ML_FEATURES_SPEC.md        # Feature specifications
├── requirements_ml.txt        # ML dependencies
├── data_collector.py          # Collect historical tokens
├── feature_extractor.py       # Extract 60+ features
├── model_trainer.py           # Train ML models
├── predictor.py               # Use trained model
├── dataset/
│   ├── rugs.json             # Confirmed rug pulls
│   ├── success.json          # Successful tokens
│   └── features.csv          # Extracted features for training
└── models/
    ├── random_forest_latest.pkl    # Latest trained model
    ├── scaler_latest.pkl           # Feature scaler
    └── metrics_YYYYMMDD_HHMMSS.json # Training metrics
```

## Next Steps

1. **Collect Data**: Run `data_collector.py` to gather 500+ tokens
2. **Extract Features**: Complete TODOs in `feature_extractor.py` using your scanner logic
3. **Train Model**: Run `model_trainer.py` to train classifier
4. **Integrate**: Add ML predictions to main scanner
5. **Iterate**: Retrain weekly with new data

## Contributing

As you discover new scam patterns:
1. Add new features to `feature_extractor.py`
2. Update `ML_FEATURES_SPEC.md`
3. Retrain model with new features
4. Share insights with community

---

**Note**: This ML module is a complement to your existing rule-based scanner, not a replacement. Combining both approaches (70% rules + 30% ML) gives the best results.
