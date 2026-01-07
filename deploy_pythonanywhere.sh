#!/bin/bash
# PythonAnywhere Deployment Script
# Run this script in PythonAnywhere Bash console

echo "=========================================="
echo "SCAM AI - PythonAnywhere Setup"
echo "=========================================="

# Clone repository
echo "[1/5] Cloning repository..."
cd ~
git clone https://github.com/RugAIOfficial/rug-ai-scanner.git
cd rug-ai-scanner

# Create virtual environment
echo "[2/5] Creating virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies (without gunicorn for PythonAnywhere)
echo "[3/5] Installing dependencies..."
pip install --upgrade pip
pip install flask solana solders httpx python-dotenv rich
pip install pandas numpy scikit-learn joblib imbalanced-learn

# Test ML model loading
echo "[4/5] Testing ML model..."
python -c "from ml_module.predictor import TokenPredictor; print('ML model OK!')"

echo "[5/5] Setup complete!"
echo "=========================================="
echo "Next steps:"
echo "1. Go to Web tab in PythonAnywhere"
echo "2. Create new web app (Flask/Python 3.11)"
echo "3. Set source code: /home/YOUR_USERNAME/Scan-Beta-V1"
echo "4. Set virtualenv: /home/YOUR_USERNAME/Scan-Beta-V1/venv"
echo "5. Edit WSGI file (see instructions)"
echo "=========================================="
