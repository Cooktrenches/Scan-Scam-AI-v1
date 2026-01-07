# 🛡️ SCAM AI - Web Interface

## 🤖 Powered by Machine Learning

This web scanner uses an **AI model trained on 559+ real tokens** to predict rug pulls with **83% accuracy**. Every scan includes real-time ML predictions alongside traditional detection methods.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Web Server

```bash
python web_app.py
```

You should see:
```
ML Model loaded successfully from random_forest_latest.pkl
[ML] Modele ML charge avec succes!
Starting SCAM AI Web Server...
Access at: http://localhost:5000
Documentation: http://localhost:5000/docs
```

### 3. Open Your Browser

Visit: **http://localhost:5000**

---

## 📖 How to Use

1. **Enter Token Address**: Paste the Solana token mint address
2. **Click "SCAN TOKEN"**: Analysis takes 10-30 seconds
3. **Review AI Prediction**: Check the red ML prediction banner
4. **Check Confidence**: See how reliable the analysis is
5. **Read Red Flags**: Review detailed warnings
6. **Follow Recommendations**: Get actionable advice

---

## 🌐 Web Interface Features

### 🎨 New Red Theme Design
- **Terminal-style cybersecurity aesthetic**
- **Red color scheme** matching modern security tools
- **Clean, professional layout**
- **Real-time loading animations**

### 🤖 AI/ML Prediction Banner- **Prominent red banner** displaying ML predictions
- **AI Score (0-100)**: Higher = safer
- **Predicted Class**: RUG / SAFE / SUCCESS
- **Confidence Level**: How sure the AI is
- **Probabilities**: Detailed breakdown of predictions

### 📊 Confidence Scoring- **Dynamic color-coded banner**:
  - 🔴 **RED** (LOW confidence): Limited data available
  - 🟡 **ORANGE** (MEDIUM confidence): Good data coverage
  - 🟢 **GREEN** (HIGH confidence): Comprehensive analysis
- **Confidence factors** explaining what affects reliability
- **Token age consideration** (new tokens = lower confidence)

### 🖥️ Main Scanner Results
- **Overall Risk Score (0-100)** with color-coded display
- **Market Data**: Price, liquidity, volume, market cap
- **Holder Statistics**: Total holders, top holder %, distribution
- **Creator Analysis** (ENHANCED):
  - Serial rugger detection
  - Previous token history
  - Rug percentage analysis
- **Whale Activity** (NEW):
  - Whale dumping detection
  - Coordinated exit warnings
  - Top 3 concentration analysis
- **Pump & Dump Analysis** (ENHANCED):
  - Pattern type detection
  - Manipulation confidence score
  - Pump/dump speed calculations
- **Red Flags List**: All warnings in one place
- **Recommendations**: What to do next

---

## 🔌 API Endpoints

### POST `/api/scan`

Scan a token with AI-powered analysis.

**Request:**
```json
{
  "mint_address": "BDuWXaAcs8SguisXQWvdiDGDVNn7eR7Wxw5Q5KLgpump"
}
```

**Response:**
```json
{
  "success": true,
  "mint_address": "...",
  "token_info": {
    "name": "Token Name",
    "symbol": "SYMBOL",
    "creator": "..."
  },
  "risk_assessment": {
    "overall_score": 37,
    "risk_level": "MEDIUM",
    "verdict": "...",
    "confidence": {
      "score": 65,
      "level": "MEDIUM",
      "factors": [
        "[+] Social media presence verified",
        "[!] Token less than 2h old - limited data"
      ]
    }
  },
  "ml_prediction": {
    "enabled": true,
    "score": 45,
    "predicted_class": "SAFE",
    "confidence": 76.3,
    "risk_level": "MODERATE",
    "probabilities": {
      "RUG": 23.7,
      "SAFE": 76.3
    }
  },
  "market_data": { ... },
  "holder_stats": { ... },
  "creator_analysis": {
    "total_tokens_created": 3,
    "potential_rugs": 1,
    "rug_percentage": 33.3,
    "active_tokens": 2,
    "risk_score": 45,
    "red_flags": [...]
  },
  "onchain_analysis": {
    "top_holder_percentage": 15.2,
    "top_3_percentage": 35.8,
    "whale_dumping_detected": false,
    "coordinated_exit_detected": false,
    "holders_selling_count": 0,
    "risk_score": 20,
    "red_flags": [...]
  },
  "pump_dump_analysis": {
    "is_pump_dump": false,
    "pattern_type": null,
    "manipulation_confidence": 15.2,
    "pump_speed": 0,
    "dump_speed": 0,
    "risk_score": 15,
    "red_flags": [...]
  },
  "red_flags": [ ... ],
  "recommendations": [ ... ]
}
```

### GET `/api/stats`

Get scanner statistics.

**Response:**
```json
{
  "total_scans": 1234,
  "total_high_risk": 456,
  "total_medium_risk": 389,
  "total_low_risk": 389,
  "ml_enabled": true
}
```

### Example with cURL:
```bash
curl -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"mint_address": "YOUR_TOKEN_ADDRESS"}'
```

### Example with Python:
```python
import requests

response = requests.post('http://localhost:5000/api/scan', json={
    'mint_address': 'BDuWXaAcs8SguisXQWvdiDGDVNn7eR7Wxw5Q5KLgpump'
})

data = response.json()

# Check AI prediction
ml = data['ml_prediction']
print(f"AI Score: {ml['score']}/100")
print(f"Prediction: {ml['predicted_class']}")
print(f"Confidence: {ml['confidence']}%")

# Check risk score
risk = data['risk_assessment']
print(f"Risk Score: {risk['overall_score']}/100")
print(f"Risk Level: {risk['risk_level']}")
```

---

## 🎨 Detection Features

### 1. 🤖 **AI/ML Prediction**Our machine learning model analyzes 61+ on-chain features to predict:
- **RUG** (0-30 score): Likely scam
- **SAFE** (30-70 score): Moderate safety
- **SUCCESS** (70-100 score): High potential

**Training Data:**
- 559 real Solana tokens
- 318 confirmed rugs
- 241 safe/successful tokens
- 83.04% accuracy
- Continuously improving

**Model Details:**
- Random Forest Classifier
- 61+ features analyzed
- Precision: 85.7%
- Real-time predictions
- Confidence scoring

### 2. 👤 **Enhanced Creator Analysis**
- **Serial Rugger Detection**:
  - 15+ tokens = EXTREME WARNING
  - 10+ tokens = High risk
  - Tracks entire creator history
- **Rug Percentage Analysis**:
  - 80%+ = Confirmed scammer
  - 60%+ = Known rugger
  - 40%+ = High rug rate
- **Automatic Rug Detection**:
  - Near-zero market cap
  - Liquidity removal
  - Price dumps >90%
  - Bonding curve crashes

### 3. 🐋 **Whale Dumping Detection**- Detects when top holders are selling
- Coordinated exit warnings (3+ sellers = RUG LIKELY)
- Exchange detection in top 10
- Top 3 concentration analysis
- Average holder age tracking
- Real-time selling pattern detection

### 4. 📈 **Advanced Pump & Dump Analysis**- **Pattern Type Detection**:
  - Fast pump slow dump
  - Coordinated multiple pumps
  - Dead cat bounce
  - Stairs pattern (bot trading)
  - Flash pump dump
- **Manipulation Confidence**: 0-100% how likely it's manipulation
- **Pump/Dump Speed**: % per hour
- **Time at Peak**: Minutes spent at ATH
- **Coordinated Pumps Counter**: Number of suspicious pumps

### 5. 📊 **Analysis Confidence Scoring**Dynamic confidence system that tells you how reliable the scan is:

**Factors Considered:**
- **Token Age**: Older = more reliable
- **Data Completeness**: More data = higher confidence
- **Analyzer Availability**: More analyzers = better
- **Social Media**: Verified links increase confidence
- **On-chain Data**: Full blockchain access improves confidence

**Confidence Levels:**
- **VERY LOW** (0-30%): Take with extreme caution
- **LOW** (30-50%): Some missing data
- **MEDIUM** (50-70%): Good coverage
- **HIGH** (70-85%): Comprehensive analysis
- **VERY HIGH** (85-100%): Full data, very reliable

### 6. 🤖 **Fake Holders & Sybil Attacks**
- Fresh wallets (<7 days old)
- Wallets created in same minute
- Low activity wallets (<5 transactions)
- Identical balance patterns

### 7. 🎯 **Insider Trading & Snipers**
- Instant snipers (first 3 seconds) ⚠️
- Early snipers (first 10 seconds)
- Coordinated buying
- Bundle transactions

### 8. 📊 **Wash Trading & Fake Volume**
- Volume/Market Cap ratio
- Fake buy pressure (>85% buys)
- Mass selling (<15% buys)
- Impossible volume patterns

### 9. 👥 **Holder Distribution Analysis**
- Total holders count
- Top holder percentage
- Top 10 concentration
- Fresh wallets in top holders
- Exchange detection

### 10. 🌐 **Social Media Verification**
- Twitter verification
- Telegram presence
- Website checks
- Blockchain metadata

---

## 📊 Understanding the Scores

### Risk Score (0-100)
| Score | Level | Color | Banner | Description |
|-------|-------|-------|--------|-------------|
| 0-24 | LOW | 🟢 Green | No banner | Relatively safe, few red flags |
| 25-49 | MEDIUM | 🟡 Yellow | Yellow banner | Proceed with extreme caution |
| 50-74 | HIGH | 🔴 Red | Red banner | Very dangerous, many red flags |
| 75-100 | EXTREME | ⛔ Dark Red | Dark red banner | DO NOT BUY - Clear scam |

### AI Score (0-100)
| Score | Prediction | Color | Meaning |
|-------|------------|-------|---------|
| 0-30 | RUG | 🔴 Red | AI predicts this is a rug pull |
| 30-70 | SAFE | 🟡 Yellow | AI predicts moderate safety |
| 70-100 | SUCCESS | 🟢 Green | AI predicts high potential |

### Confidence Score (0-100)
| Score | Level | Banner Color | Reliability |
|-------|-------|--------------|-------------|
| 0-30 | VERY LOW | 🔴 Red | Limited data - be very cautious |
| 30-50 | LOW | 🔴 Red | Some missing data |
| 50-70 | MEDIUM | 🟡 Orange | Good data coverage |
| 70-85 | HIGH | 🟢 Green | Comprehensive analysis |
| 85-100 | VERY HIGH | 🟢 Green | Full data - very reliable |

---

## 📁 File Structure

```
rug coin/
├── web_app.py                      # Flask backend with ML integration
├── templates/
│   ├── index.html                  # Main scanner (red theme)
│   └── docs.html                   # Documentation page
├── static/
│   ├── css/
│   │   └── style.css               # Red cybersecurity theme
│   └── js/
│       └── scanner.js              # Frontend with ML display
├── ml_module/
│   ├── predictor.py                # ML prediction engine
│   ├── model_trainer.py            # Training pipeline
│   ├── models/
│   │   └── random_forest_latest.pkl # Trained AI model
│   └── dataset/
│       └── features.csv            # 559+ labeled tokens
├── feature_extractor.py            # Extract 61+ features
├── creator_checker.py              # Enhanced creator analysis
├── onchain_analyzer.py             # Whale dumping detection
├── pump_dump_detector.py           # Advanced P&D analysis
├── risk_scorer.py                  # Confidence scoring
└── README_WEB.md                   # This file
```

---

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Optional - for enhanced features
HELIUS_API_KEY=your_key_here
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
```

### Change Port
Edit `web_app.py` at the bottom:
```python
app.run(debug=True, host='0.0.0.0', port=5000)  # Change port here
```

### Production Deployment
For production, use Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

Or deploy to Render/PythonAnywhere (see DEPLOYMENT_*.md guides)

---

## 🛡️ Security Notes

- ✅ Only analyzes public blockchain data
- ✅ No private keys or seed phrases needed
- ✅ All data is on-chain and verifiable
- ⚠️ Results are informational, not financial advice
- ⚠️ Always DYOR (Do Your Own Research)
- ⚠️ Even with 83% accuracy, the AI can make mistakes

---

## 🐛 Troubleshooting

### ML Model Not Loading
If you see `[ML] ML module disabled`:
1. Check `ml_module/models/` folder exists
2. Ensure `random_forest_latest.pkl` is present
3. Run `python ml_module/train_with_my_data.py` to train

### "Address already in use" error
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID [PID] /F

# Linux/Mac
lsof -i :5000
kill -9 [PID]
```

### Scanner Takes Too Long
- Normal: 10-30 seconds
- Slow: Check internet connection
- Very slow: Token might have huge holder count (>10,000)

### ML Prediction Not Showing
1. Check server logs for ML loading message
2. Verify model file exists in `ml_module/models/`
3. Restart server: `python web_app.py`

### API Returns Error
Check:
- Token address is valid (32-44 characters)
- Internet connection is active
- Server is running on port 5000

---

## 🧪 Advanced: Improving the AI

Want better predictions? Retrain the model with more data!

### Collect More Training Data
```bash
cd ml_module

# Collect 500 tokens from DexScreener
python collect_from_dexscreener_simple.py 500

# Check dataset size
python show_features.py

# Retrain model
python train_with_my_data.py
```

The web scanner will automatically use the updated model!

---

## 📞 Support

- **GitHub Issues**: Report bugs
- **GitHub Discussions**: Ask questions
- **Documentation**: Check `/docs` page on the web interface

---

## ⚠️ Disclaimer

**Educational Purposes Only**: This tool is designed for research and education.

**Not Financial Advice**: Never invest based solely on automated analysis, even AI.

**No Guarantees**: 83% accuracy means 17% error rate. False positives and negatives can occur.

**DYOR**: Always Do Your Own Research before investing in any token.

**Beta Software**: This is BETA. Use at your own risk.

---

## 🎯 What's New in This Version

### Latest Updates (v1.0)
✅ **AI/ML Integration**: 559 tokens, 83% accuracy
✅ **Confidence Scoring**: Know how reliable each scan is
✅ **Whale Dumping Detection**: Catch coordinated exits
✅ **Advanced P&D Analysis**: 6 pattern types detected
✅ **Enhanced Creator Analysis**: Serial rugger detection
✅ **Red Theme UI**: Professional cybersecurity aesthetic
✅ **Dynamic Colors**: Confidence banners change color
✅ **Improved API**: More data in responses

### Coming Soon
🔜 Historical price charts
🔜 Expand to 1,000+ training tokens
🔜 Multi-chain support
🔜 API rate limiting
🔜 WebSocket real-time updates

---

**⚡ Powered by AI | Built with Flask | Trained on Real Data**

**Made with ❤️ for the Solana community**

---

**©SCAM AI 2025 - All Rights Reserved**
