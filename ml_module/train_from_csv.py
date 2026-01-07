"""
Entraîne le modèle ML directement depuis features.csv
NO emojis - Windows compatible
"""
import pandas as pd
from pathlib import Path
from model_trainer import TokenClassifierTrainer

print("="*80)
print("ENTRAINEMENT DU MODELE ML DEPUIS CSV")
print("="*80)

# Charger le dataset
csv_path = Path(__file__).parent / "dataset" / "features.csv"

if not csv_path.exists():
    print(f"\n[X] ERREUR: {csv_path} not found!")
    exit(1)

print(f"\n[*] Loading dataset from {csv_path}...")
df = pd.read_csv(csv_path)

print(f"\n[OK] Dataset loaded successfully!")
print(f"    Total tokens: {len(df)}")
print(f"    RUG tokens:  {(df['label']==1).sum()}")
print(f"    SAFE tokens: {(df['label']==0).sum()}")
print(f"    Features:    {len(df.columns) - 3} (excluding label, token_mint, timestamp)")

# Préparer les données
print(f"\n[*] Preparing data for training...")

# Colonnes à exclure
exclude_cols = ['label', 'token_mint', 'timestamp', 'label_reason', 'collected_at']
feature_cols = [col for col in df.columns if col not in exclude_cols]

X = df[feature_cols].values
y = df['label'].values

print(f"[OK] Data prepared:")
print(f"    X shape: {X.shape}")
print(f"    y shape: {y.shape}")

# Entraîner le modèle
print(f"\n[*] Training model...")
trainer = TokenClassifierTrainer()

# Set feature names for the trainer
trainer.feature_names = feature_cols

# Prepare data
X_train, X_test, y_train, y_test = trainer.preprocess_data(X, y)

# Train Random Forest
print(f"[*] Training Random Forest...")
rf_model = trainer.train_random_forest(X_train, y_train)

# Evaluate Random Forest
print(f"[*] Evaluating Random Forest...")
rf_metrics = trainer.evaluate_model(rf_model, X_test, y_test)

# Save Random Forest model
print(f"\n[*] Saving Random Forest model...")
trainer.save_model(rf_model, trainer.scaler, rf_metrics, model_name="random_forest")

# Train Gradient Boosting
print(f"\n[*] Training Gradient Boosting...")
gb_model = trainer.train_gradient_boosting(X_train, y_train)

# Evaluate Gradient Boosting
print(f"[*] Evaluating Gradient Boosting...")
gb_metrics = trainer.evaluate_model(gb_model, X_test, y_test)

# Save Gradient Boosting model
print(f"\n[*] Saving Gradient Boosting model...")
trainer.save_model(gb_model, trainer.scaler, gb_metrics, model_name="gradient_boosting")

print("\n" + "="*80)
print("TRAINING COMPLETE!")
print("="*80)
print(f"\nRandom Forest Results:")
print(f"  Accuracy:  {rf_metrics['accuracy']:.2%}")
print(f"  Precision: {rf_metrics['precision']:.2%}")
print(f"  Recall:    {rf_metrics['recall']:.2%}")
print(f"  F1-Score:  {rf_metrics['f1_score']:.2%}")

print(f"\nGradient Boosting Results:")
print(f"  Accuracy:  {gb_metrics['accuracy']:.2%}")
print(f"  Precision: {gb_metrics['precision']:.2%}")
print(f"  Recall:    {gb_metrics['recall']:.2%}")
print(f"  F1-Score:  {gb_metrics['f1_score']:.2%}")

print(f"\n[OK] Models saved to models/")
print("="*80)
