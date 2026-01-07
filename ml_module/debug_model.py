"""Debug script to understand model structure"""
import pickle
from pathlib import Path

models_dir = Path(__file__).parent / "models"
model_path = models_dir / "random_forest_latest.pkl"

with open(model_path, "rb") as f:
    model = pickle.load(f)

print("=" * 60)
print("MODEL DEBUG INFO")
print("=" * 60)

print(f"\nModel type: {type(model)}")
print(f"Model classes: {model.classes_}")
print(f"Number of classes: {len(model.classes_)}")

print("\n" + "=" * 60)
