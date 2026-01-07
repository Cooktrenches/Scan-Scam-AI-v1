"""
Script to wait for collection completion and automatically retrain model
"""
import time
import subprocess
import os

print("[*] Waiting for collection to complete...")
print("[*] Monitoring output every 10 seconds...\n")

max_wait = 600  # 10 minutes max
elapsed = 0
collection_complete = False

while elapsed < max_wait:
    # Check if features.csv exists and get line count
    csv_path = "dataset/features.csv"
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = sum(1 for _ in f)
        print(f"[INFO] Current dataset size: {lines-1} tokens")

        # If we have 500+ tokens, assume collection is done
        if lines >= 501:  # 500 tokens + 1 header line
            collection_complete = True
            print("\n[OK] Collection appears complete!")
            break

    time.sleep(10)
    elapsed += 10

if collection_complete:
    print("\n" + "="*80)
    print("STARTING AUTOMATIC MODEL RETRAINING")
    print("="*80 + "\n")

    # Show final dataset stats
    print("[*] Running dataset analysis...")
    subprocess.run(["python", "show_features.py"], cwd=os.path.dirname(__file__))

    print("\n[*] Starting model training...")
    subprocess.run(["python", "train_with_my_data.py"], cwd=os.path.dirname(__file__))

    print("\n" + "="*80)
    print("TRAINING COMPLETE!")
    print("="*80)
else:
    print("\n[X] Timeout waiting for collection to complete")
    print("[!] Check collection status manually")
