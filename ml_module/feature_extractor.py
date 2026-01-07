"""
Feature Extractor - Extracts 60+ features from token data for ML training
INTEGRATED WITH REAL ANALYZERS
"""

import json
import httpx
import asyncio
import numpy as np
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add parent directory to path to import analyzers
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import real analyzers
from sniper_detector import SniperDetector
from wallet_analyzer import WalletAnalyzer
from liquidity_analyzer import LiquidityAnalyzer
from pump_dump_detector import PumpDumpDetector
from volume_analyzer import VolumeAnalyzer
from authority_checker import AuthorityChecker
from onchain_analyzer import OnChainAnalyzer

console = Console()


class TokenFeatureExtractor:
    """Extracts comprehensive features from token data using REAL analyzers"""

    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url
        self.client = httpx.AsyncClient(timeout=30.0)

        # Initialize real analyzers
        self.sniper_detector = SniperDetector()
        self.wallet_analyzer = WalletAnalyzer()
        self.liquidity_analyzer = LiquidityAnalyzer()
        self.pump_dump_detector = PumpDumpDetector()
        self.volume_analyzer = VolumeAnalyzer()
        self.authority_checker = AuthorityChecker()
        self.onchain_analyzer = OnChainAnalyzer()

    async def extract_all_features(self, token_mint: str) -> Optional[Dict]:
        """
        Extract all 75+ features from a token using REAL analyzers

        Args:
            token_mint: Token mint address

        Returns:
            Dictionary of features or None if failed
        """
        try:
            # Fetch basic data
            dex_data = await self._fetch_dexscreener_data(token_mint)
            if not dex_data:
                return None

            pump_data = await self._fetch_pump_fun_data(token_mint)

            # Get token data for analyzers
            token_data = self.liquidity_analyzer.get_token_data(token_mint)
            if not token_data:
                return None

            # Run REAL analyzers
            liquidity_analysis = self.liquidity_analyzer.analyze_liquidity(token_mint)

            # Onchain data (holders)
            onchain_data = None
            try:
                onchain_data = self.onchain_analyzer.get_token_holders(token_mint)
            except:
                pass

            # Sniper analysis
            sniper_analysis = None
            try:
                token_creation_time = token_data.get("created_timestamp")
                sniper_analysis = self.sniper_detector.analyze_snipers(token_mint, token_creation_time)
            except:
                pass

            # Volume analysis
            volume_analysis = None
            try:
                liquidity = liquidity_analysis.liquidity_usd if liquidity_analysis else 0
                volume_analysis = self.volume_analyzer.analyze_volume(token_data, liquidity)
            except:
                pass

            # Pump & dump analysis
            pump_dump_analysis = None
            try:
                pump_dump_analysis = self.pump_dump_detector.analyze_pump_dump(token_mint, token_data)
            except:
                pass

            # Authority check
            authority_analysis = None
            try:
                authority_analysis = self.authority_checker.check_authority(token_mint)
            except:
                pass

            # Extract features from REAL analyses
            features = {}

            features.update(self._extract_holder_features_real(onchain_data))
            features.update(self._extract_trading_features_real(volume_analysis, dex_data))
            features.update(self._extract_sniper_features_real(sniper_analysis))
            features.update(self._extract_pump_dump_features_real(pump_dump_analysis))
            features.update(self._extract_liquidity_features_real(liquidity_analysis))
            features.update(self._extract_authority_features_real(authority_analysis))
            features.update(self._extract_temporal_features(dex_data, pump_data))

            # Add metadata
            features["token_mint"] = token_mint
            features["timestamp"] = datetime.utcnow().isoformat()

            return features

        except Exception as e:
            console.print(f"[red]Error extracting features for {token_mint}: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _fetch_dexscreener_data(self, token_mint: str) -> Optional[Dict]:
        """Fetch token data from DexScreener"""
        try:
            response = await self.client.get(
                f"https://api.dexscreener.com/latest/dex/tokens/{token_mint}"
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("pairs", [{}])[0] if data.get("pairs") else None
            return None
        except:
            return None

    async def _fetch_pump_fun_data(self, token_mint: str) -> Optional[Dict]:
        """Fetch token data from Pump.fun"""
        try:
            response = await self.client.get(
                f"https://frontend-api-v2.pump.fun/coins/{token_mint}"
            )
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None

    async def _fetch_holder_data(self, token_mint: str) -> List[Dict]:
        """Fetch holder data (simplified - use your existing scanner logic)"""
        # TODO: Integrate with your existing holder analysis from scanner.py
        return []

    # ============================================================
    # FEATURE EXTRACTION METHODS
    # ============================================================

    def _extract_holder_features(self, holder_data: List[Dict]) -> Dict:
        """Extract 15 holder-related features"""
        if not holder_data:
            return self._default_holder_features()

        total_holders = len(holder_data)

        # Calculate concentrations
        balances = sorted([h.get("balance", 0) for h in holder_data], reverse=True)
        total_supply = sum(balances)

        top_1_pct = (balances[0] / total_supply * 100) if total_supply > 0 else 0
        top_10_pct = (sum(balances[:10]) / total_supply * 100) if total_supply > 0 else 0

        return {
            "fresh_wallet_percentage": 0,  # TODO: Calculate from wallet creation dates
            "holder_count": total_holders,
            "top_10_concentration": top_10_pct,
            "top_1_concentration": top_1_pct,
            "whale_count": sum(1 for b in balances if b/total_supply > 0.05),
            "identical_balance_clusters": 0,  # TODO: Calculate clusters
            "low_activity_holders": 0,  # TODO: Calculate from transaction history
            "avg_holder_age_days": 30,  # TODO: Calculate from wallet ages
            "holder_growth_rate": 0,  # TODO: Calculate growth rate
            "nakamoto_coefficient": 0,  # TODO: Calculate
            "gini_coefficient": self._calculate_gini(balances),
            "hhi_index": self._calculate_hhi(balances),
            "holder_diversity_score": 0,  # TODO: Calculate entropy
            "bot_holder_percentage": 0,  # TODO: Estimate bots
            "organic_holder_estimate": total_holders * 0.7,  # Rough estimate
        }

    def _extract_trading_features(self, dex_data: Optional[Dict]) -> Dict:
        """Extract 12 trading-related features"""
        if not dex_data:
            return self._default_trading_features()

        volume_24h = float(dex_data.get("volume", {}).get("h24", 0))
        market_cap = float(dex_data.get("marketCap", 1))
        liquidity = float(dex_data.get("liquidity", {}).get("usd", 0))

        return {
            "volume_24h": volume_24h,
            "volume_to_mcap_ratio": volume_24h / market_cap if market_cap > 0 else 0,
            "buy_sell_ratio": 1.0,  # TODO: Calculate from transactions
            "unique_traders_24h": 0,  # TODO: Calculate unique wallets
            "avg_trade_size": volume_24h / 100,  # Rough estimate
            "wash_trading_score": 0,  # TODO: Calculate
            "trade_frequency": 0,  # TODO: Calculate trades per hour
            "volume_consistency": 0,  # TODO: Calculate std dev
            "price_impact_ratio": 0,  # TODO: Calculate
            "liquidity_depth": liquidity,
            "slippage_estimate": 0,  # TODO: Calculate
            "dex_distribution": 1,  # Usually Raydium for Pump.fun
        }

    def _extract_sniper_features(self, holder_data: List[Dict]) -> Dict:
        """Extract 10 sniper-related features"""
        return {
            "instant_sniper_count": 0,  # TODO: Calculate from first 3s buyers
            "early_sniper_count": 0,  # TODO: Calculate from first 10s buyers
            "bundle_transaction_count": 0,  # TODO: Calculate
            "sniper_holdings_percentage": 0,  # TODO: Calculate
            "coordinated_wallet_clusters": 0,  # TODO: Calculate
            "pre_launch_activity_detected": 0,  # Boolean
            "sniper_sell_rate": 0,  # TODO: Calculate
            "avg_sniper_profit_percentage": 0,  # TODO: Calculate
            "insider_wallet_connections": 0,  # TODO: Calculate
            "first_10_buyers_concentration": 0,  # TODO: Calculate
        }

    def _extract_pump_dump_features(self, dex_data: Optional[Dict]) -> Dict:
        """Extract 8 pump & dump features"""
        if not dex_data:
            return self._default_pump_dump_features()

        price_change_5m = float(dex_data.get("priceChange", {}).get("m5", 0))
        price_change_1h = float(dex_data.get("priceChange", {}).get("h1", 0))
        price_change_24h = float(dex_data.get("priceChange", {}).get("h24", 0))

        return {
            "price_volatility_24h": abs(price_change_24h),
            "max_price_spike_percentage": max(abs(price_change_5m), abs(price_change_1h)),
            "ath_to_current_ratio": 1.0,  # TODO: Calculate from historical high
            "rapid_pump_count": 0,  # TODO: Count pumps >50% in 1h
            "dump_after_pump_count": 0,  # TODO: Count dumps after pumps
            "price_stability_score": 100 - abs(price_change_24h),
            "current_vs_launch_price": 1.0,  # TODO: Calculate
            "sustained_growth_periods": 0,  # TODO: Calculate
        }

    def _extract_liquidity_features(self, dex_data: Optional[Dict]) -> Dict:
        """Extract 8 liquidity features"""
        if not dex_data:
            return self._default_liquidity_features()

        market_cap = float(dex_data.get("marketCap", 0))
        liquidity = float(dex_data.get("liquidity", {}).get("usd", 0))

        return {
            "market_cap_usd": market_cap,
            "liquidity_usd": liquidity,
            "liquidity_locked": 0,  # TODO: Check if locked
            "bonding_curve_complete": 1,  # Assume yes if on DEX
            "raydium_migration_complete": 1,  # Assume yes if on Raydium
            "liquidity_to_mcap_ratio": liquidity / market_cap if market_cap > 0 else 0,
            "liquidity_stability": 0,  # TODO: Calculate std dev
            "burn_liquidity_percentage": 0,  # TODO: Check burn
        }

    def _extract_creator_features(self, pump_data: Optional[Dict]) -> Dict:
        """Extract 7 creator history features"""
        if not pump_data:
            return self._default_creator_features()

        creator = pump_data.get("creator", "")

        return {
            "creator_token_count": 1,  # TODO: Query creator's token count
            "creator_rug_count": 0,  # TODO: Query creator's rug count
            "creator_rug_rate": 0,  # TODO: Calculate
            "creator_success_count": 0,  # TODO: Query successes
            "creator_avg_token_lifespan_hours": 168,  # Default 1 week
            "creator_total_volume_generated": 0,  # TODO: Calculate
            "creator_wallet_age_days": 30,  # TODO: Calculate
        }

    def _extract_authority_features(self, token_mint: str) -> Dict:
        """Extract 4 authority features"""
        return {
            "mint_authority_renounced": 0,  # TODO: Check on-chain
            "freeze_authority_renounced": 0,  # TODO: Check on-chain
            "update_authority_renounced": 0,  # TODO: Check on-chain
            "authority_risk_score": 50,  # TODO: Calculate
        }

    def _extract_social_features(self, pump_data: Optional[Dict]) -> Dict:
        """Extract 6 social signal features"""
        if not pump_data:
            return self._default_social_features()

        twitter = pump_data.get("twitter", "")
        telegram = pump_data.get("telegram", "")
        website = pump_data.get("website", "")
        description = pump_data.get("description", "")

        return {
            "twitter_exists": 1 if twitter else 0,
            "telegram_exists": 1 if telegram else 0,
            "website_exists": 1 if website else 0,
            "description_quality_score": len(description) if description else 0,
            "social_engagement_score": 0,  # TODO: Calculate
            "legitimate_social_presence": 1 if (twitter or telegram) else 0,
        }

    def _extract_temporal_features(self, dex_data: Optional[Dict], pump_data: Optional[Dict]) -> Dict:
        """Extract 5 temporal features"""
        return {
            "token_age_hours": 24,  # TODO: Calculate from creation time
            "time_to_first_dump": 0,  # TODO: Calculate
            "time_to_ath": 0,  # TODO: Calculate
            "activity_decay_rate": 0,  # TODO: Calculate
            "survival_probability": 0.5,  # TODO: Predict
        }

    # ============================================================
    # HELPER METHODS
    # ============================================================

    def _calculate_gini(self, values: List[float]) -> float:
        """Calculate Gini coefficient"""
        if not values or sum(values) == 0:
            return 0

        sorted_values = sorted(values)
        n = len(sorted_values)
        index = np.arange(1, n + 1)
        return (2 * np.sum(index * sorted_values)) / (n * np.sum(sorted_values)) - (n + 1) / n

    def _calculate_hhi(self, values: List[float]) -> float:
        """Calculate Herfindahl-Hirschman Index"""
        if not values or sum(values) == 0:
            return 0

        total = sum(values)
        shares = [v / total for v in values]
        return sum(s ** 2 for s in shares) * 10000

    # Default feature sets for missing data
    def _default_holder_features(self) -> Dict:
        return {f: 0 for f in [
            "fresh_wallet_percentage", "holder_count", "top_10_concentration",
            "top_1_concentration", "whale_count", "identical_balance_clusters",
            "low_activity_holders", "avg_holder_age_days", "holder_growth_rate",
            "nakamoto_coefficient", "gini_coefficient", "hhi_index",
            "holder_diversity_score", "bot_holder_percentage", "organic_holder_estimate"
        ]}

    def _default_trading_features(self) -> Dict:
        return {f: 0 for f in [
            "volume_24h", "volume_to_mcap_ratio", "buy_sell_ratio",
            "unique_traders_24h", "avg_trade_size", "wash_trading_score",
            "trade_frequency", "volume_consistency", "price_impact_ratio",
            "liquidity_depth", "slippage_estimate", "dex_distribution"
        ]}

    def _default_pump_dump_features(self) -> Dict:
        return {f: 0 for f in [
            "price_volatility_24h", "max_price_spike_percentage",
            "ath_to_current_ratio", "rapid_pump_count", "dump_after_pump_count",
            "price_stability_score", "current_vs_launch_price", "sustained_growth_periods"
        ]}

    def _default_liquidity_features(self) -> Dict:
        return {f: 0 for f in [
            "market_cap_usd", "liquidity_usd", "liquidity_locked",
            "bonding_curve_complete", "raydium_migration_complete",
            "liquidity_to_mcap_ratio", "liquidity_stability", "burn_liquidity_percentage"
        ]}

    def _default_creator_features(self) -> Dict:
        return {f: 0 for f in [
            "creator_token_count", "creator_rug_count", "creator_rug_rate",
            "creator_success_count", "creator_avg_token_lifespan_hours",
            "creator_total_volume_generated", "creator_wallet_age_days"
        ]}

    def _default_social_features(self) -> Dict:
        return {f: 0 for f in [
            "twitter_exists", "telegram_exists", "website_exists",
            "description_quality_score", "social_engagement_score",
            "legitimate_social_presence"
        ]}

    # ============================================================
    # REAL FEATURE EXTRACTION METHODS (Using actual analyzers)
    # ============================================================

    def _extract_holder_features_real(self, onchain_data) -> Dict:
        """Extract holder features from REAL onchain analysis"""
        if not onchain_data or not onchain_data.can_analyze:
            return {
                "fresh_wallet_percentage": 0,
                "holder_count": 0,
                "top_10_concentration": 0,
                "top_1_concentration": 0,
                "whale_count": 0,
                "identical_balance_clusters": 0,
                "low_activity_holders": 0,
                "avg_holder_age_days": 0,
                "holder_growth_rate": 0,
                "nakamoto_coefficient": 0,
                "gini_coefficient": 0,
                "hhi_index": 0,
                "holder_diversity_score": 0,
                "bot_holder_percentage": 0,
                "organic_holder_estimate": 0
            }

        return {
            "fresh_wallet_percentage": onchain_data.fresh_wallet_count_top10 * 10,  # Convert to %
            "holder_count": onchain_data.total_holders,
            "top_10_concentration": onchain_data.top_10_percentage,
            "top_1_concentration": onchain_data.top_holder_percentage,
            "whale_count": sum(1 for h in onchain_data.holders if h.get("balance_usd", 0) > 10000),
            "identical_balance_clusters": 0,  # TODO: Implement clustering
            "low_activity_holders": sum(1 for h in onchain_data.holders if h.get("is_fresh", False)),
            "avg_holder_age_days": 7,  # TODO: Calculate from holder creation dates
            "holder_growth_rate": 0,  # TODO: Track over time
            "nakamoto_coefficient": 10,  # TODO: Calculate properly
            "gini_coefficient": onchain_data.top_10_percentage / 100,  # Approximation
            "hhi_index": (onchain_data.top_holder_percentage ** 2) / 100,
            "holder_diversity_score": 100 - onchain_data.top_10_percentage,
            "bot_holder_percentage": onchain_data.fresh_wallet_count_top10 * 10,
            "organic_holder_estimate": 100 - (onchain_data.fresh_wallet_count_top10 * 10)
        }

    def _extract_sniper_features_real(self, sniper_analysis) -> Dict:
        """Extract sniper features from REAL sniper detector"""
        if not sniper_analysis:
            return {
                "instant_sniper_count": 0,
                "early_sniper_count": 0,
                "bundle_transaction_count": 0,
                "sniper_holdings_percentage": 0,
                "coordinated_wallet_clusters": 0,
                "pre_launch_activity_detected": 0,
                "sniper_sell_rate": 0,
                "avg_sniper_profit_percentage": 0,
                "insider_wallet_connections": 0,
                "sniper_dominance_score": 0
            }

        return {
            "instant_sniper_count": sniper_analysis.instant_snipers,
            "early_sniper_count": sniper_analysis.sniper_count,
            "bundle_transaction_count": 0,  # TODO: Add to sniper detector
            "sniper_holdings_percentage": sniper_analysis.sniper_percentage,
            "coordinated_wallet_clusters": 1 if sniper_analysis.coordinated_buy_detected else 0,
            "pre_launch_activity_detected": 0,  # TODO: Add to sniper detector
            "sniper_sell_rate": 0,  # TODO: Track sell activity
            "avg_sniper_profit_percentage": 0,  # TODO: Calculate profits
            "insider_wallet_connections": 0,  # TODO: Graph analysis
            "sniper_dominance_score": sniper_analysis.instant_sniper_percentage
        }

    def _extract_trading_features_real(self, volume_analysis, dex_data) -> Dict:
        """Extract trading features from REAL volume analyzer"""
        if not volume_analysis:
            return {
                "volume_24h": float(dex_data.get("volume", {}).get("h24", 0) or 0) if dex_data else 0,
                "volume_to_mcap_ratio": 0,
                "buy_sell_ratio": 0,
                "unique_traders_24h": 0,
                "avg_trade_size": 0,
                "wash_trading_score": 0,
                "trade_frequency": 0,
                "volume_consistency": 0,
                "price_impact_ratio": 0,
                "liquidity_depth": 0,
                "slippage_estimate": 0,
                "dex_distribution": 0
            }

        return {
            "volume_24h": volume_analysis.volume_24h,
            "volume_to_mcap_ratio": volume_analysis.volume_to_mcap_ratio,
            "buy_sell_ratio": volume_analysis.buy_volume_percentage / 50 if volume_analysis.buy_volume_percentage else 1,
            "unique_traders_24h": 0,  # TODO: Add to volume analyzer
            "avg_trade_size": 0,  # TODO: Add to volume analyzer
            "wash_trading_score": 100 if volume_analysis.is_wash_trading else 0,
            "trade_frequency": 0,  # TODO: Add to volume analyzer
            "volume_consistency": 0,  # TODO: Track over time
            "price_impact_ratio": 0,  # TODO: Calculate
            "liquidity_depth": float(dex_data.get("liquidity", {}).get("usd", 0) or 0) if dex_data else 0,
            "slippage_estimate": 0,  # TODO: Calculate
            "dex_distribution": 1  # Mostly PumpSwap for Pump.fun tokens
        }

    def _extract_pump_dump_features_real(self, pump_dump_analysis) -> Dict:
        """Extract pump&dump features from REAL pump_dump_detector"""
        if not pump_dump_analysis:
            return {
                "max_price_spike_24h": 0,
                "max_price_drop_24h": 0,
                "price_volatility_24h": 0,
                "suspicious_pump_pattern": 0,
                "coordinated_dump_detected": 0,
                "volume_spike_correlation": 0,
                "price_stability_score": 50,
                "max_price_spike_percentage": 0
            }

        return {
            "max_price_spike_24h": pump_dump_analysis.max_price_spike,
            "max_price_drop_24h": abs(pump_dump_analysis.price_dump_after_spike) if pump_dump_analysis.price_dump_after_spike else 0,
            "price_volatility_24h": pump_dump_analysis.price_volatility,
            "suspicious_pump_pattern": 100 if pump_dump_analysis.is_pump_dump else 0,
            "coordinated_dump_detected": 0,  # TODO: Add to pump_dump_detector
            "volume_spike_correlation": 0,  # TODO: Correlate volume with price
            "price_stability_score": max(0, 100 - pump_dump_analysis.price_volatility),
            "max_price_spike_percentage": pump_dump_analysis.max_price_spike
        }

    def _extract_liquidity_features_real(self, liquidity_analysis) -> Dict:
        """Extract liquidity features from REAL liquidity analyzer"""
        if not liquidity_analysis:
            return {
                "liquidity_usd": 0,
                "liquidity_locked_percentage": 0,
                "liquidity_to_mcap_ratio": 0,
                "liquidity_depth": 0,
                "bonding_curve_progress": 0,
                "rug_pull_liquidity_risk": 100,
                "liquidity_stability_score": 0,
                "market_cap_usd": 0
            }

        return {
            "liquidity_usd": liquidity_analysis.liquidity_usd,
            "liquidity_locked_percentage": 0,  # TODO: Check if locked
            "liquidity_to_mcap_ratio": (liquidity_analysis.liquidity_usd / liquidity_analysis.market_cap_usd * 100) if liquidity_analysis.market_cap_usd > 0 else 0,
            "liquidity_depth": liquidity_analysis.liquidity_usd,
            "bonding_curve_progress": 100 if liquidity_analysis.bonding_curve_complete else 50,
            "rug_pull_liquidity_risk": 0 if liquidity_analysis.bonding_curve_complete else 50,
            "liquidity_stability_score": 100 if liquidity_analysis.liquidity_usd > 10000 else 50,
            "market_cap_usd": liquidity_analysis.market_cap_usd
        }

    def _extract_authority_features_real(self, authority_analysis) -> Dict:
        """Extract authority features from REAL authority checker"""
        if not authority_analysis:
            return {
                "mint_authority_renounced": 0,
                "freeze_authority_renounced": 0,
                "update_authority_renounced": 0,
                "authority_risk_score": 100
            }

        return {
            "mint_authority_renounced": 100 if authority_analysis.mint_authority_renounced else 0,
            "freeze_authority_renounced": 100 if authority_analysis.freeze_authority_renounced else 0,
            "update_authority_renounced": 0,  # TODO: Check update authority
            "authority_risk_score": 0 if (authority_analysis.mint_authority_renounced and authority_analysis.freeze_authority_renounced) else 100
        }

    async def close(self):
        """Close HTTP client and analyzers"""
        await self.client.aclose()
        self.sniper_detector.close()
        self.wallet_analyzer.close()
        self.liquidity_analyzer.close()
        self.pump_dump_detector.close()
        # VolumeAnalyzer doesn't have close() method
        self.authority_checker.close()
        self.onchain_analyzer.close()


async def main():
    """Test feature extraction"""
    extractor = TokenFeatureExtractor()

    # Test with a sample token
    test_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC for testing

    console.print(f"[cyan]Extracting features for: {test_mint}")
    features = await extractor.extract_all_features(test_mint)

    if features:
        console.print(f"[green]Extracted {len(features)} features:")
        for key, value in list(features.items())[:10]:
            console.print(f"  {key}: {value}")

    await extractor.close()


if __name__ == "__main__":
    asyncio.run(main())
