# ML Module Architecture

## Vue d'ensemble du système

```
┌─────────────────────────────────────────────────────────────────┐
│                    SCAM AI DETECTOR                        │
│                   Enhanced with ML Predictions                  │
└─────────────────────────────────────────────────────────────────┘

                              │
                              ▼
                     ┌─────────────────┐
                     │  User Input     │
                     │  Token Mint     │
                     └────────┬────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
    ┌──────────────────────┐    ┌──────────────────────┐
    │  RULE-BASED SCANNER  │    │    ML PREDICTOR      │
    │   (Existing System)  │    │   (New Module)       │
    └──────────┬───────────┘    └──────────┬───────────┘
               │                           │
               ▼                           ▼
    ┌──────────────────────┐    ┌──────────────────────┐
    │  Component Scores    │    │  ML Prediction       │
    │  - Holder: 65/100    │    │  - Class: RUG        │
    │  - Creator: 80/100   │    │  - Score: 25/100     │
    │  - Sniper: 90/100    │    │  - Confidence: 92%   │
    │  - Liquidity: 40/100 │    │                      │
    │  - Volume: 70/100    │    │                      │
    │  - Pump&Dump: 85/100 │    │                      │
    └──────────┬───────────┘    └──────────┬───────────┘
               │                           │
               │  Rule Score: 75/100       │  ML Score: 25/100
               │                           │
               └────────────┬──────────────┘
                            │
                            ▼
                ┌────────────────────────┐
                │   SCORE COMBINER       │
                │  70% Rules + 30% ML    │
                │  = 60/100 (DANGER)     │
                └────────────┬───────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Final Report   │
                    │  + Red Flags    │
                    │  + Recommendations│
                    └─────────────────┘
```

## ML Module Components

### 1. Data Collection Pipeline

```
┌──────────────────────────────────────────────────────────────┐
│                    DATA COLLECTION                           │
└──────────────────────────────────────────────────────────────┘

    data_collector.py
         │
         ├─► Pump.fun API ────► Get recent tokens
         │                      (500+ tokens)
         │
         ├─► DexScreener API ──► Analyze outcomes
         │                      (market cap, price)
         │
         └─► Classify tokens
                │
                ├─► Rug: mcap dropped >90%
                ├─► Safe: stable, moderate
                └─► Success: >$5M mcap
                      │
                      ▼
              ┌─────────────────┐
              │  dataset/       │
              │  - rugs.json    │
              │  - success.json │
              └─────────────────┘
```

### 2. Feature Extraction Pipeline

```
┌──────────────────────────────────────────────────────────────┐
│                   FEATURE EXTRACTION                         │
└──────────────────────────────────────────────────────────────┘

    feature_extractor.py
         │
         ├─────────────────────────────────────────┐
         │                                         │
         ▼                                         ▼
    ┌─────────────┐                      ┌──────────────────┐
    │ Data Sources│                      │  Feature Groups  │
    ├─────────────┤                      ├──────────────────┤
    │             │                      │ 1. Holders (15)  │
    │ DexScreener ├─────────────────────►│ 2. Trading (12)  │
    │ Pump.fun    │                      │ 3. Snipers (10)  │
    │ Solana RPC  │                      │ 4. Pump&Dump (8) │
    │ Solscan     │                      │ 5. Liquidity (8) │
    │ InsightX    │                      │ 6. Creator (7)   │
    │ Helius      │                      │ 7. Authority (4) │
    │             │                      │ 8. Social (6)    │
    │             │                      │ 9. Temporal (5)  │
    └─────────────┘                      └──────────┬───────┘
                                                    │
                                                    ▼
                                          ┌──────────────────┐
                                          │  75+ Features    │
                                          │  features.csv    │
                                          └──────────────────┘
```

### 3. Model Training Pipeline

```
┌──────────────────────────────────────────────────────────────┐
│                     MODEL TRAINING                           │
└──────────────────────────────────────────────────────────────┘

    model_trainer.py
         │
         ▼
    Load features.csv
         │
         ├─► Labels:
         │   0 = RUG
         │   1 = SAFE
         │   2 = HIGH_POTENTIAL
         │
         ▼
    Split Dataset
    ┌──────────────┬──────────────┬──────────────┐
    │   Train 70%  │  Valid 15%   │   Test 15%   │
    └──────┬───────┴──────────────┴──────┬───────┘
           │                              │
           ▼                              │
    Feature Scaling                       │
    (StandardScaler)                      │
           │                              │
           ▼                              │
    Class Balancing                       │
    (SMOTE)                               │
           │                              │
           ▼                              │
    ┌──────────────────┐                 │
    │  Train Model     │                 │
    │  - Random Forest │                 │
    │  - XGBoost       │                 │
    │  - GradBoost     │                 │
    └────────┬─────────┘                 │
             │                           │
             └───────────┬───────────────┘
                         ▼
                  Evaluate Model
                  ┌────────────────┐
                  │ Accuracy       │
                  │ Precision      │
                  │ Recall         │
                  │ F1-Score       │
                  │ ROC-AUC        │
                  └───────┬────────┘
                          │
                          ▼
                    Save Model
                    ┌─────────────────────────────┐
                    │ models/                     │
                    │ - random_forest_latest.pkl  │
                    │ - scaler_latest.pkl         │
                    │ - metrics_YYMMDD.json       │
                    └─────────────────────────────┘
```

### 4. Prediction Pipeline

```
┌──────────────────────────────────────────────────────────────┐
│                      PREDICTION                              │
└──────────────────────────────────────────────────────────────┘

    predictor.py
         │
         ▼
    Load trained model
    + scaler
         │
         ▼
    ┌─────────────────┐
    │  Input: Token   │
    │  Features (75)  │
    └────────┬────────┘
             │
             ▼
    Scale features
             │
             ▼
    Model.predict()
             │
             ├─► Predicted Class
             │   (RUG/SAFE/HIGH_POTENTIAL)
             │
             ├─► Confidence
             │   (0-100%)
             │
             └─► Class Probabilities
                 ┌─────────────────────┐
                 │ RUG: 85%            │
                 │ SAFE: 12%           │
                 │ HIGH_POTENTIAL: 3%  │
                 └──────────┬──────────┘
                            │
                            ▼
                 Convert to 0-100 score
                 ┌──────────────────────┐
                 │ RUG (85%) → 15/100   │
                 │ SAFE (12%) → 35/100  │
                 │ HIGH_POT (3%)→ 75/100│
                 └──────────┬───────────┘
                            │
                            ▼
                      ML Prediction
                      ┌─────────────────┐
                      │ Score: 15/100   │
                      │ Class: RUG      │
                      │ Conf: 85%       │
                      └─────────────────┘
```

## Integration with Existing Scanner

### Current Architecture (Rule-Based)

```
Token → [Holder Analysis] → Score 1
     ↓  [Creator Check]   → Score 2
     ↓  [Sniper Detect]   → Score 3
     ↓  [Liquidity]       → Score 4
     ↓  [Volume]          → Score 5
     ↓  [Pump & Dump]     → Score 6
     ↓
     └─► Weighted Average → Final Score
```

### New Architecture (Hybrid: Rules + ML)

```
Token → ┌──────────────────────┐     ┌────────────────┐
        │  RULE-BASED ENGINE   │     │  ML ENGINE     │
        │                      │     │                │
        │  [Holder Analysis]   │     │  Extract       │
        │  [Creator Check]     │     │  75 features   │
        │  [Sniper Detect]     │     │      ↓         │
        │  [Liquidity]         │     │  ML Predict    │
        │  [Volume]            │     │      ↓         │
        │  [Pump & Dump]       │     │  ML Score      │
        │         ↓            │     │                │
        │  Weighted Average    │     │                │
        │         ↓            │     │                │
        │  Rule Score: 75/100  │     │  ML: 25/100    │
        └──────────┬───────────┘     └────────┬───────┘
                   │                          │
                   └────────┬─────────────────┘
                            │
                            ▼
                  ┌──────────────────┐
                  │  SCORE COMBINER  │
                  │  70% Rules       │
                  │  30% ML          │
                  │                  │
                  │  = 60/100        │
                  └────────┬─────────┘
                           │
                           ▼
                    Final Report
```

## Feature Categories Breakdown

```
┌─────────────────────────────────────────────────────────────┐
│                    75 FEATURES                              │
└─────────────────────────────────────────────────────────────┘

 1. HOLDER PATTERNS (15 features)
    ├─ fresh_wallet_percentage
    ├─ holder_count
    ├─ top_10_concentration
    ├─ top_1_concentration
    ├─ whale_count
    ├─ identical_balance_clusters
    ├─ low_activity_holders
    ├─ avg_holder_age_days
    ├─ holder_growth_rate
    ├─ nakamoto_coefficient
    ├─ gini_coefficient
    ├─ hhi_index
    ├─ holder_diversity_score
    ├─ bot_holder_percentage
    └─ organic_holder_estimate

 2. TRADING PATTERNS (12 features)
    ├─ volume_24h
    ├─ volume_to_mcap_ratio
    ├─ buy_sell_ratio
    ├─ unique_traders_24h
    ├─ avg_trade_size
    ├─ wash_trading_score
    ├─ trade_frequency
    ├─ volume_consistency
    ├─ price_impact_ratio
    ├─ liquidity_depth
    ├─ slippage_estimate
    └─ dex_distribution

 3. SNIPER ACTIVITY (10 features)
    ├─ instant_sniper_count (0-3s)
    ├─ early_sniper_count (0-10s)
    ├─ bundle_transaction_count
    ├─ sniper_holdings_percentage
    ├─ coordinated_wallet_clusters
    ├─ pre_launch_activity_detected
    ├─ sniper_sell_rate
    ├─ avg_sniper_profit_percentage
    ├─ insider_wallet_connections
    └─ first_10_buyers_concentration

 4. PUMP & DUMP (8 features)
    ├─ price_volatility_24h
    ├─ max_price_spike_percentage
    ├─ ath_to_current_ratio
    ├─ rapid_pump_count
    ├─ dump_after_pump_count
    ├─ price_stability_score
    ├─ current_vs_launch_price
    └─ sustained_growth_periods

 5. LIQUIDITY (8 features)
    ├─ market_cap_usd
    ├─ liquidity_usd
    ├─ liquidity_locked
    ├─ bonding_curve_complete
    ├─ raydium_migration_complete
    ├─ liquidity_to_mcap_ratio
    ├─ liquidity_stability
    └─ burn_liquidity_percentage

 6. CREATOR HISTORY (7 features)
    ├─ creator_token_count
    ├─ creator_rug_count
    ├─ creator_rug_rate
    ├─ creator_success_count
    ├─ creator_avg_token_lifespan_hours
    ├─ creator_total_volume_generated
    └─ creator_wallet_age_days

 7. AUTHORITY (4 features)
    ├─ mint_authority_renounced
    ├─ freeze_authority_renounced
    ├─ update_authority_renounced
    └─ authority_risk_score

 8. SOCIAL SIGNALS (6 features)
    ├─ twitter_exists
    ├─ telegram_exists
    ├─ website_exists
    ├─ description_quality_score
    ├─ social_engagement_score
    └─ legitimate_social_presence

 9. TEMPORAL (5 features)
    ├─ token_age_hours
    ├─ time_to_first_dump
    ├─ time_to_ath
    ├─ activity_decay_rate
    └─ survival_probability
```

## Data Flow

### Training Phase

```
Historical Tokens
       ↓
   Extract Features (75)
       ↓
   Label (0=Rug, 1=Safe, 2=Success)
       ↓
   features.csv
       ↓
   Train Model
       ↓
   Evaluate
       ↓
   Save Model (.pkl)
```

### Inference Phase

```
New Token
    ↓
Extract Features (75)
    ↓
Load Model
    ↓
Predict
    ↓
┌─────────────────┐
│ Class: RUG      │
│ Confidence: 92% │
│ Score: 15/100   │
└─────────────────┘
    ↓
Combine with Rule-Based Score
    ↓
Final Score & Report
```

## File Structure

```
ml_module/
│
├── __init__.py                      # Module init
│
├── Documentation
│   ├── README_ML.md                 # Complete documentation
│   ├── QUICKSTART.md                # Quick start guide
│   ├── ARCHITECTURE.md              # This file
│   └── ML_FEATURES_SPEC.md          # Feature specifications
│
├── Core Modules
│   ├── data_collector.py            # Collect historical tokens
│   ├── feature_extractor.py         # Extract 75 features
│   ├── model_trainer.py             # Train ML models
│   └── predictor.py                 # Make predictions
│
├── Integration
│   ├── integration_example.py       # How to integrate with scanner
│   └── complete_workflow.py         # Complete ML workflow
│
├── Data
│   ├── dataset/
│   │   ├── rugs.json               # Confirmed rugs
│   │   ├── success.json            # Successful tokens
│   │   └── features.csv            # Extracted features
│   │
│   └── models/
│       ├── random_forest_latest.pkl # Trained model
│       ├── scaler_latest.pkl        # Feature scaler
│       └── metrics_*.json           # Training metrics
│
└── Config
    └── requirements_ml.txt          # ML dependencies
```

## Model Performance Expectations

With **500+ tokens** (balanced dataset):

```
┌──────────────────────────────────────────────┐
│             MODEL PERFORMANCE                │
├──────────────────────────────────────────────┤
│ Metric          │ Expected    │ Excellent    │
├─────────────────┼─────────────┼──────────────┤
│ Accuracy        │ 85-90%      │ >90%         │
│ Precision (RUG) │ 85-92%      │ >92%         │
│ Recall (RUG)    │ 82-88%      │ >88%         │
│ F1-Score        │ 85-90%      │ >90%         │
│ ROC-AUC         │ 90-95%      │ >95%         │
└─────────────────┴─────────────┴──────────────┘

Key Metrics Explained:
- Precision: % of predicted rugs that are actual rugs
- Recall: % of actual rugs that are detected
- F1-Score: Balance between precision and recall
- ROC-AUC: Overall discrimination ability
```

## Advantages of Hybrid Approach

### Rule-Based Only
```
✅ Transparent
✅ Explainable
✅ Fast
❌ Misses novel patterns
❌ Fixed thresholds
❌ Manual tuning needed
```

### ML Only
```
✅ Learns patterns
✅ Adapts over time
✅ Handles complexity
❌ Black box
❌ Needs lots of data
❌ Can overfit
```

### Hybrid (70% Rules + 30% ML) ⭐
```
✅ Best of both worlds
✅ Transparent + Adaptive
✅ Catches known + novel patterns
✅ Robust to data quality
✅ Gradual ML integration
```

## Next Steps for Implementation

1. ✅ Install ML dependencies
2. 📊 Collect 500+ labeled tokens
3. 🔬 Extract features using your scanner
4. 🎯 Train initial model
5. 🧪 Test predictions
6. 🔧 Integrate with scanner (30% weight)
7. 📈 Monitor performance
8. 🔄 Retrain weekly
9. ⚡ Increase ML weight as confidence grows
10. 🚀 Deploy to production

---

**Note**: This ML module complements your existing rule-based scanner. Start with low ML weight (30%) and increase as you gain confidence in the model's performance.
