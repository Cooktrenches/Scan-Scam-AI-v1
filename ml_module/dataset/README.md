# Dataset Directory

This directory contains the training data for the ML model.

## Files

### `rugs.json` (Required)
List of confirmed rug pull tokens. These are tokens that:
- Market cap dropped >90% in short time
- Developer pulled liquidity
- Confirmed scams by community

**Format:**
```json
[
  {
    "mint": "TOKEN_MINT_ADDRESS",
    "name": "Token Name",
    "symbol": "SYMBOL",
    "creator": "CREATOR_WALLET_ADDRESS",
    "created_timestamp": 1234567890,
    "notes": "Why this is a rug (optional)"
  }
]
```

### `success.json` (Required)
List of successful tokens. These are tokens that:
- Reached market cap >$5M USD
- Sustained for 30+ days
- Active community and trading

**Format:**
```json
[
  {
    "mint": "TOKEN_MINT_ADDRESS",
    "name": "Token Name",
    "symbol": "SYMBOL",
    "creator": "CREATOR_WALLET_ADDRESS",
    "created_timestamp": 1234567890,
    "peak_mcap": 15000000,
    "notes": "Success story (optional)"
  }
]
```

### `features.csv` (Auto-generated)
This file is automatically created by `feature_extractor.py`. It contains:
- 75 features extracted from each token
- Label (0=rug, 1=safe, 2=success)
- Token metadata

**Do not create this manually** - it's generated automatically.

## How to Create Your Dataset

### Option 1: Manual Collection (RECOMMENDED)

**Step 1:** Create `rugs.json`
- Research Pump.fun tokens that rugged
- Check DexScreener for tokens with -90%+ crashes
- Look for community reports of scams
- Add their mint addresses to the file

**Step 2:** Create `success.json`
- Find Pump.fun tokens that succeeded
- Check DexScreener for tokens with >$5M mcap
- Verify they've been active for 30+ days
- Add their mint addresses to the file

**Example sources:**
- DexScreener (filter by Pump.fun, sort by age/mcap)
- Twitter/Telegram community reports
- Your own scanner results
- Manual tracking of tokens over time

### Option 2: Automated Collection

```bash
python data_collector.py
```

This will:
- Fetch 500+ recent tokens from Pump.fun
- Analyze their outcomes using DexScreener
- Auto-classify as rug/safe/success
- Save to rugs.json and success.json

**Note:** Automated collection is less accurate than manual verification.

## Data Quality Tips

### For Rugs
✅ **Good:**
- Confirmed liquidity pulls
- Market cap -95%+ drops
- Creator has rug history
- Community confirmed scams

❌ **Avoid:**
- Tokens that just failed naturally
- Low volume tokens that died slowly
- Unverified claims

### For Success
✅ **Good:**
- Peak mcap >$5M USD
- Active for 30+ days
- Graduated to Raydium
- Strong community

❌ **Avoid:**
- Short-lived pumps
- Tokens still on bonding curve
- Recent tokens (<7 days old)

## Recommended Dataset Size

| Size | Precision | Status |
|------|-----------|--------|
| 100 tokens | ~70% | Minimum (50 rugs + 50 success) |
| 300 tokens | ~80% | Good (150 rugs + 150 success) |
| **500 tokens** | **~88%** | **Recommended** (250 rugs + 250 success) |
| 1000+ tokens | ~92% | Excellent (500 rugs + 500 success) |

## Class Balance

Aim for balanced dataset:
- **40%** Rugs
- **30%** Safe
- **30%** Success

Example for 500 tokens:
- 200 rugs
- 150 safe
- 150 success

## Examples

See example files:
- `rugs_EXAMPLE.json` - Example rug entries
- `success_EXAMPLE.json` - Example success entries

Rename to `rugs.json` and `success.json` after filling with real data.

## Next Steps

1. Create `rugs.json` with real rug tokens
2. Create `success.json` with real success tokens
3. Run feature extraction: `python feature_extractor.py`
4. Train model: `python model_trainer.py`
5. Start predicting!

## Important Notes

- **Quality over Quantity**: 100 verified tokens > 500 unverified
- **Update Regularly**: Add new rugs/successes weekly
- **Verify Labels**: Double-check that rugs are really rugs
- **Track Sources**: Add notes field to remember why you labeled each token

---

**Need Help?** Check [README_FR.md](../README_FR.md) for detailed instructions in French.
