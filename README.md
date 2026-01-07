# 🛡️ SCAM AI - AI-Powered Solana Security Scanner

Advanced security scanner powered by Machine Learning for detecting rug pulls and scams on Solana tokens (Pump.fun & DexScreener).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![ML Accuracy](https://img.shields.io/badge/ML%20Accuracy-83%25-brightgreen.svg)](/)

## 🤖 Powered by Artificial Intelligence

Our scanner uses a **Machine Learning model trained on 559+ real Solana tokens** to predict rug pulls with **83.04% accuracy**.

### 📈 AI Model Statistics
- **Training Dataset**: 559 tokens (318 RUG, 241 SAFE)
- **Model Type**: Random Forest Classifier
- **Accuracy**: 83.04%
- **Precision**: 85.7%
- **Features Analyzed**: 61+ on-chain metrics per token
- **Constantly Evolving**: Model retrains automatically as new data is collected

### 🧠 What Makes Our AI Special?

✅ **Real-World Training**: Trained on actual rug pulls and successful tokens from Pump.fun
✅ **61+ Features**: Analyzes holder distribution, price patterns, liquidity, creator history, and more
✅ **Continuous Learning**: Dataset grows daily through automated collection
✅ **Dual-Model Approach**: Random Forest + Gradient Boosting for maximum accuracy
✅ **Confidence Scoring**: Tells you how confident the AI is in its prediction

## 🚀 Features

### 🎯 Core Detection Systems

#### 1. **AI/ML Prediction**
- Machine Learning model trained on 500+ tokens
- Predicts RUG/SAFE/SUCCESS with confidence score
- AI Score: 0-100 (higher = safer)
- Real-time prediction on every scan

#### 2. **Creator Analysis**
- Serial rugger detection (15+ tokens = EXTREME warning)
- Rug percentage analysis (80%+ = confirmed scammer)
- All previous tokens tracked
- Automatic rug detection based on:
  - Near-zero market cap
  - Liquidity removal
  - Bonding curve crashes
  - Price dumps >90%

#### 3. **Whale Dumping Detection**
- Detects when top holders are selling
- Coordinated exit warnings (3+ holders selling)
- Exchange detection in top 10
- Top 3 concentration analysis
- Holder age tracking

#### 4. **Advanced Pump & Dump Analysis**
- Pattern type detection:
  - Fast pump slow dump
  - Coordinated pumps
  - Dead cat bounce
  - Stairs pattern (bot trading)
- Pump/dump speed calculation
- Manipulation confidence score (0-100%)

#### 5. **Analysis Confidence Scoring**
- Confidence score: 0-100%
- Confidence levels: VERY LOW / LOW / MEDIUM / HIGH / VERY HIGH
- Factors affecting confidence:
  - Token age
  - Data completeness
  - Analyzer availability
- Dynamic color-coded display (RED/ORANGE/GREEN)

#### 6. **Traditional Detection**
- **Fake Holders Detection** - Sybil attacks and bot wallets
- **Insider Trading Analysis** - Snipers and coordinated buying
- **Wash Trading Scanner** - Fake volume detection
- **Social Media Verification** - Twitter, Telegram, Website checks
- **Real-Time Blockchain Data** - Live Solana RPC analysis

## 🎨 Web Interface

Beautiful terminal-style interface with:
- 🔴 **Red Theme**: Cybersecurity aesthetic
- 🤖 **AI Prediction Banner**: ML predictions displayed prominently
- 📊 **Risk Scores**: 0-100 comprehensive scoring
- 🚨 **Red Flags**: Detailed warnings and explanations
- 💡 **Recommendations**: Actionable advice
- 📈 **Confidence Indicators**: Know how reliable the analysis is
- ⚡ **Real-Time Scanning**: Instant results

## 🤖 Discord & Telegram Bots

Scan tokens directly from Discord or Telegram!

- **Discord Bot**: Slash commands with beautiful embeds
- **Telegram Bot**: Simple commands with formatted messages
- **Real-Time Analysis**: Powered by the same AI engine
- **Easy Setup**: Just add your bot token and run

📖 **See [README_BOTS.md](README_BOTS.md) for setup instructions**

### Quick Start Bots

```bash
# Install bot dependencies
pip install discord.py python-telegram-bot

# Configure tokens in .env
DISCORD_BOT_TOKEN=your_token
TELEGRAM_BOT_TOKEN=your_token

# Run Discord bot
python discord_bot.py

# Run Telegram bot
python telegram_bot.py
```

## 🔧 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/RugAIOfficial/rug-ai-scanner.git
cd "rug-ai-scanner"

# Install dependencies
pip install -r requirements.txt

# Start web server
python web_app.py
```

Access at: **http://localhost:5000**

### Using the Scanner

1. Go to http://localhost:5000
2. Paste a Solana token mint address
3. Click **"Scan Token"**
4. Get instant AI-powered analysis!

## 📊 Understanding the Scores

### Risk Score (0-100)
| Score | Level | Color | Description |
|-------|-------|-------|-------------|
| 0-24  | LOW | 🟢 Green | Relatively safe, low risk signals |
| 25-49 | MEDIUM | 🟡 Yellow | Proceed with extreme caution |
| 50-74 | HIGH | 🔴 Red | Very dangerous, multiple red flags |
| 75-100| EXTREME | ⛔ Dark Red | DO NOT BUY - Almost certain rug |

### AI Score (0-100)
| Score | Prediction | Meaning |
|-------|------------|---------|
| 0-30  | RUG | AI predicts this is a rug pull |
| 30-70 | SAFE | AI predicts moderate safety |
| 70-100| SUCCESS | AI predicts high potential success |

### Confidence Score (0-100)
| Score | Level | Color | Meaning |
|-------|-------|-------|---------|
| 0-30  | VERY LOW | 🔴 Red | Limited data, take with caution |
| 30-50 | LOW | 🔴 Red | Some missing data |
| 50-70 | MEDIUM | 🟡 Orange | Good data coverage |
| 70-85 | HIGH | 🟢 Green | Comprehensive analysis |
| 85-100| VERY HIGH | 🟢 Green | Full data, very reliable |

## 🧪 ML Model Training (Advanced)

Want to improve the AI yourself? You can retrain the model with new data:

### Automatic Data Collection
```bash
cd ml_module

# Collect 500 tokens from DexScreener (auto-labeled)
python collect_from_dexscreener_simple.py 500

# Retrain the model
python train_with_my_data.py
```

### Manual Training
```bash
cd ml_module

# View current dataset
python show_features.py

# Train from existing CSV
python train_from_csv.py
```

The model automatically:
- Extracts 61+ features per token
- Labels tokens as RUG/SAFE based on market behavior
- Trains Random Forest and Gradient Boosting models
- Saves the best performing model
- Updates the web scanner instantly

## 🔬 Technical Details

### Architecture
- **Backend**: Flask (Python)
- **ML Framework**: Scikit-learn
- **Blockchain**: Solana Web3.py + RPC
- **APIs**: Pump.fun, DexScreener, Helius
- **Frontend**: Vanilla JS + CSS (terminal theme)

### ML Pipeline
1. **Data Collection**: Automated scraping from DexScreener
2. **Feature Extraction**: 61 metrics from blockchain + market data
3. **Auto-Labeling**: Smart heuristics to label RUG vs SAFE
4. **Training**: Dual models (Random Forest + Gradient Boosting)
5. **Evaluation**: Cross-validation with precision/recall metrics
6. **Deployment**: Automatic model updates without downtime

### Analyzed Metrics (61+ Features)
- Holder distribution patterns
- Top holder concentration
- Whale selling behavior
- Fresh wallet detection
- Sniper activity
- Wash trading indicators
- Price volatility patterns
- Liquidity metrics
- Volume analysis
- Creator token history
- Social media presence
- Blockchain metadata
- And much more...

## 📈 Roadmap

### Current Version (v1.0 BETA)
✅ ML model trained on 559 tokens
✅ 83% accuracy
✅ Web interface
✅ Real-time scanning
✅ Advanced detection systems
✅ Confidence scoring

### Future Updates
🔜 **v1.1**: Expand dataset to 1,000+ tokens
🔜 **v1.2**: Add historical price chart analysis
🔜 **v1.3**: Multi-chain support (Ethereum, BSC)
🔜 **v1.4**: API endpoints for developers
🔜 **v1.5**: Mobile app

## ⚠️ Important Disclaimers

**Educational Purposes Only**: This tool is designed for research and education.

**Not Financial Advice**: Never invest based solely on automated analysis.

**No Guarantees**: Even with 83% accuracy, the model can make mistakes.

**DYOR**: Always Do Your Own Research before investing.

**Alpha Software**: This is BETA software. Use at your own risk.

## 🤝 Contributing

We welcome contributions! The model improves as the dataset grows.

### How to Help
1. **Report False Positives/Negatives**: Help us improve accuracy
2. **Contribute Data**: Run collection scripts and share labeled data
3. **Improve Detection**: Add new features or detection methods
4. **Documentation**: Help improve guides and tutorials

## 📞 Support

- **GitHub**: [RugAIOfficial](https://github.com/RugAIOfficial)

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Solana Foundation for blockchain infrastructure
- Pump.fun for revolutionizing token launches
- DexScreener for market data API
- The entire Solana community

---

**⚡ Built with AI, Trained by Real Data, Powered by the Community**

**Made with ❤️ for the Solana ecosystem**

---

**©SCAM AI 2025 - All Rights Reserved**
