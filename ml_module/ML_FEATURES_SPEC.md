# ML Features Specification for Token Classification

## Overview
This document specifies the 60+ features used to train the ML model for detecting rugs and identifying high-potential tokens.

## Feature Categories

### 1. HOLDER PATTERNS (15 features)
- `fresh_wallet_percentage` - % of holders with wallets < 7 days old
- `holder_count` - Total number of unique holders
- `top_10_concentration` - % of supply held by top 10 wallets
- `top_1_concentration` - % held by largest holder
- `whale_count` - Number of wallets holding > 5% supply
- `identical_balance_clusters` - Number of wallet groups with same balance
- `low_activity_holders` - % of holders who never sold
- `avg_holder_age_days` - Average age of holder wallets
- `holder_growth_rate` - Rate of new holders per hour
- `nakamoto_coefficient` - Wallets needed to control 51% supply
- `gini_coefficient` - Wealth inequality metric
- `hhi_index` - Herfindahl-Hirschman Index (concentration)
- `holder_diversity_score` - Entropy of holder distribution
- `bot_holder_percentage` - Estimated % of bot/sybil holders
- `organic_holder_estimate` - Estimated real human holders

### 2. TRADING PATTERNS (12 features)
- `volume_24h` - 24h trading volume
- `volume_to_mcap_ratio` - Volume / Market Cap ratio
- `buy_sell_ratio` - Buy transactions / Sell transactions
- `unique_traders_24h` - Unique wallets trading in 24h
- `avg_trade_size` - Average transaction size
- `wash_trading_score` - Likelihood of wash trading (0-100)
- `trade_frequency` - Trades per hour
- `volume_consistency` - Std deviation of hourly volume
- `price_impact_ratio` - Price change per $1k volume
- `liquidity_depth` - Total available liquidity
- `slippage_estimate` - Expected slippage for $1k trade
- `dex_distribution` - Number of DEXs where token trades

### 3. SNIPER & INSIDER ACTIVITY (10 features)
- `instant_sniper_count` - Buyers within 0-3 seconds
- `early_sniper_count` - Buyers within 0-10 seconds
- `bundle_transaction_count` - Multi-buyer transactions
- `sniper_holdings_percentage` - % supply held by snipers
- `coordinated_wallet_clusters` - Groups with identical purchase times
- `pre_launch_activity_detected` - Boolean (0/1)
- `sniper_sell_rate` - % of snipers who already sold
- `avg_sniper_profit_percentage` - Average profit of snipers
- `insider_wallet_connections` - Wallets linked to creator
- `first_10_buyers_concentration` - % held by first 10 buyers

### 4. PUMP & DUMP INDICATORS (8 features)
- `price_volatility_24h` - Price std deviation
- `max_price_spike_percentage` - Largest single pump
- `ath_to_current_ratio` - All-time high / Current price
- `rapid_pump_count` - Number of >50% pumps in 1 hour
- `dump_after_pump_count` - Pumps followed by >30% dumps
- `price_stability_score` - Inverse of volatility
- `current_vs_launch_price` - Current / Launch price ratio
- `sustained_growth_periods` - Hours of steady growth

### 5. LIQUIDITY METRICS (8 features)
- `market_cap_usd` - Current market capitalization
- `liquidity_usd` - Total liquidity in USD
- `liquidity_locked` - Boolean (0/1)
- `bonding_curve_complete` - Boolean (0/1)
- `raydium_migration_complete` - Boolean (0/1)
- `liquidity_to_mcap_ratio` - Liquidity / Market Cap
- `liquidity_stability` - Std dev of liquidity over time
- `burn_liquidity_percentage` - % of liquidity burned

### 6. CREATOR HISTORY (7 features)
- `creator_token_count` - Total tokens created by wallet
- `creator_rug_count` - Number of confirmed rugs
- `creator_rug_rate` - Rug count / Total tokens
- `creator_success_count` - Tokens reaching >$1M mcap
- `creator_avg_token_lifespan_hours` - Average before rug/death
- `creator_total_volume_generated` - Cumulative volume of all tokens
- `creator_wallet_age_days` - Age of creator's wallet

### 7. TOKEN AUTHORITY (4 features)
- `mint_authority_renounced` - Boolean (0/1)
- `freeze_authority_renounced` - Boolean (0/1)
- `update_authority_renounced` - Boolean (0/1)
- `authority_risk_score` - Combined authority risk (0-100)

### 8. SOCIAL SIGNALS (6 features)
- `twitter_exists` - Boolean (0/1)
- `telegram_exists` - Boolean (0/1)
- `website_exists` - Boolean (0/1)
- `description_quality_score` - NLP-based quality (0-100)
- `social_engagement_score` - Estimated engagement level
- `legitimate_social_presence` - Boolean (0/1)

### 9. TEMPORAL FEATURES (5 features)
- `token_age_hours` - Hours since token creation
- `time_to_first_dump` - Hours until first >20% dump
- `time_to_ath` - Hours to reach all-time high
- `activity_decay_rate` - Rate of declining activity
- `survival_probability` - Likelihood of lasting 30+ days

## Target Labels

### Classification
- **0 = RUG** - Token that dumped >90% or creator pulled liquidity
- **1 = SAFE** - Token stable, no rug, but modest growth
- **2 = HIGH_POTENTIAL** - Token reached >$5M mcap and sustained

### Regression (Alternative)
- **continuous_score** - 0-100 score where:
  - 0-30 = High rug risk
  - 30-70 = Safe but low potential
  - 70-100 = High potential for success

## Data Collection Strategy

### Confirmed Rugs
- Tokens where market cap dropped >90% in <48 hours
- Creator withdrew liquidity
- Token marked as scam on multiple sources

### Success Stories
- Tokens that reached $5M+ market cap
- Sustained volume for 30+ days
- Active community and development

### Data Sources
- DexScreener historical data
- Pump.fun API (token creation data)
- Solana blockchain (on-chain analysis)
- Manual labeling (community reports)

## Model Training Notes

### Recommended Models
1. **XGBoost** - Best for tabular data, feature importance
2. **Random Forest** - Good interpretability, robust
3. **LightGBM** - Fast training, good for large datasets
4. **Neural Network** - Deep patterns (requires more data)

### Training Strategy
- 70% training, 15% validation, 15% test
- Class balancing (SMOTE for minority class)
- Feature scaling (StandardScaler)
- Hyperparameter tuning (GridSearchCV)
- Cross-validation (5-fold)

### Evaluation Metrics
- **Accuracy** - Overall correctness
- **Precision** - Avoid false rug predictions
- **Recall** - Catch all actual rugs
- **F1-Score** - Balance precision/recall
- **ROC-AUC** - Model discrimination ability
- **Confusion Matrix** - Detailed error analysis

## Feature Engineering Pipeline

```python
token_data -> raw_features -> scaling -> feature_selection -> model_input
```

### Feature Importance
After training, rank features by importance to:
1. Remove low-impact features
2. Simplify model
3. Improve interpretability
4. Speed up inference
