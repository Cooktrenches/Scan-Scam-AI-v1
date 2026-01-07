"""Calculate overall risk score and generate report"""
from dataclasses import dataclass
from typing import List
from config import RISK_WEIGHTS


@dataclass
class RiskReport:
    """Complete risk assessment report"""
    overall_risk_score: int  # 0-100 (100 = extreme danger)
    risk_level: str  # "LOW", "MEDIUM", "HIGH", "EXTREME"
    verdict: str
    all_red_flags: List[str]
    recommendations: List[str]

    # Individual component scores
    distribution_score: int
    creator_score: int
    liquidity_score: int
    social_score: int
    wallet_score: int
    sniper_score: int
    volume_score: int
    insightx_score: int
    pump_dump_score: int  # NEW
    holder_score: int  # NEW: Holder analysis (whale dumping, coordinated exits)

    # NEW: Confidence scoring
    confidence_score: int  # 0-100 (100 = very confident in the assessment)
    confidence_level: str  # "VERY LOW", "LOW", "MEDIUM", "HIGH", "VERY HIGH"
    confidence_factors: List[str]  # Explanation of what affects confidence


class RiskScorer:
    """Calculates overall risk score from all analyses"""

    @staticmethod
    def calculate_confidence(
        token_age_hours,
        liquidity_analysis,
        creator_analysis,
        distribution_analysis,
        social_analysis,
        wallet_analysis,
        sniper_analysis,
        volume_analysis,
        distribution_metrics,
        onchain_data,
        pump_dump_analysis
    ) -> tuple:
        """
        Calculate confidence score (0-100) based on data availability and quality
        Returns: (confidence_score, confidence_level, confidence_factors)
        """
        confidence = 100
        factors = []

        # 1. TOKEN AGE - Very important for confidence
        if token_age_hours is not None:
            if token_age_hours < 0.5:  # Less than 30 minutes
                confidence -= 30
                factors.append("[!] Token less than 30min old - insufficient data history")
            elif token_age_hours < 2:  # Less than 2 hours
                confidence -= 20
                factors.append("[!] Token less than 2h old - limited historical data")
            elif token_age_hours < 12:  # Less than 12 hours
                confidence -= 10
                factors.append("[-] Token less than 12h old - moderate data coverage")
            else:
                factors.append("[+] Token age sufficient for reliable analysis")

        # 2. DATA COMPLETENESS - Check if major analyzers ran successfully
        analyzers_available = 0
        total_analyzers = 9

        if liquidity_analysis and liquidity_analysis.market_cap_usd > 0:
            analyzers_available += 1
        else:
            confidence -= 15
            factors.append("[!] Missing liquidity data - reducing confidence")

        if creator_analysis and creator_analysis.total_tokens_created > 0:
            analyzers_available += 1
            factors.append("[+] Creator history analyzed")
        else:
            confidence -= 10
            factors.append("[-] No creator history available")

        if distribution_analysis and distribution_analysis.total_holders > 0:
            analyzers_available += 1
            factors.append("[+] Holder distribution analyzed")
        else:
            confidence -= 10
            factors.append("[-] Holder distribution unavailable")

        if social_analysis:
            analyzers_available += 1
            if social_analysis.has_twitter or social_analysis.has_telegram:
                factors.append("[+] Social media presence verified")
        else:
            confidence -= 5

        if wallet_analysis and wallet_analysis.total_holders > 0:
            analyzers_available += 1
            factors.append("[+] Fresh wallet analysis complete")

        if sniper_analysis:
            analyzers_available += 1
            factors.append("[+] Sniper detection analyzed")

        if volume_analysis:
            analyzers_available += 1

        if distribution_metrics:
            analyzers_available += 1
            factors.append("[+] On-chain distribution metrics available")

        if pump_dump_analysis:
            analyzers_available += 1
            if pump_dump_analysis.price_volatility > 0:
                factors.append("[+] Price history analyzed for pump & dump")

        # 3. VOLUME DATA QUALITY
        if liquidity_analysis and liquidity_analysis.volume_24h is not None and liquidity_analysis.volume_24h > 0:
            factors.append("[+] 24h volume data available")
        else:
            confidence -= 5
            factors.append("[-] No 24h volume data")

        # 4. MARKET CAP SIZE (affects reliability)
        if liquidity_analysis:
            if liquidity_analysis.market_cap_usd < 1000:
                confidence -= 10
                factors.append("[!] Very low market cap - data may be unreliable")
            elif liquidity_analysis.market_cap_usd < 5000:
                confidence -= 5
                factors.append("[-] Low market cap - limited data reliability")

        # 5. BLOCKCHAIN METADATA AVAILABILITY
        if social_analysis and (social_analysis.has_twitter or social_analysis.has_telegram or social_analysis.has_website):
            factors.append("[+] Blockchain metadata retrieved successfully")
        else:
            confidence -= 5
            factors.append("[-] Limited on-chain metadata")

        # Ensure confidence doesn't go below 0
        confidence = max(confidence, 0)

        # Determine confidence level
        if confidence >= 85:
            level = "VERY HIGH"
        elif confidence >= 70:
            level = "HIGH"
        elif confidence >= 50:
            level = "MEDIUM"
        elif confidence >= 30:
            level = "LOW"
        else:
            level = "VERY LOW"

        return confidence, level, factors

    @staticmethod
    def calculate_risk(
        distribution_analysis,
        creator_analysis,
        liquidity_analysis,
        social_analysis,
        wallet_analysis=None,
        sniper_analysis=None,
        volume_analysis=None,
        distribution_metrics=None,
        onchain_data=None,
        pump_dump_analysis=None,  # NEW
        token_age_hours=None  # NEW: For confidence calculation
    ) -> RiskReport:
        """Calculate weighted overall risk score with confidence assessment"""

        # Get individual scores
        dist_score = distribution_analysis.risk_score if distribution_analysis else 0
        creator_score = creator_analysis.risk_score if creator_analysis else 0
        liq_score = liquidity_analysis.risk_score if liquidity_analysis else 0
        social_score = social_analysis.risk_score if social_analysis else 0
        wallet_score = wallet_analysis.risk_score if wallet_analysis else 0

        # Sniper analysis score
        sniper_score = sniper_analysis.risk_score if sniper_analysis else 0

        # Volume analysis score
        volume_score = volume_analysis.risk_score if volume_analysis else 0

        # InsightX distribution metrics score
        insightx_score = RiskScorer._calculate_insightx_score(distribution_metrics, onchain_data)

        # NEW: Pump & Dump analysis score
        pump_dump_score = pump_dump_analysis.risk_score if pump_dump_analysis else 0

        # NEW: Holder analysis score (whale dumping, coordinated exits, exchange detection)
        holder_score = onchain_data.risk_score if (onchain_data and onchain_data.can_analyze) else 0

        # Calculate weighted average with OPTIMIZED weights for Pump.fun
        overall_score = (
            dist_score * (RISK_WEIGHTS.get("whale_concentration", 15) + RISK_WEIGHTS.get("holder_distribution", 12)) / 100 +
            creator_score * RISK_WEIGHTS.get("creator_history", 15) / 100 +
            liq_score * RISK_WEIGHTS.get("liquidity", 10) / 100 +
            social_score * RISK_WEIGHTS.get("social_presence", 8) / 100 +
            wallet_score * RISK_WEIGHTS.get("fresh_wallets", 20) / 100 +
            sniper_score * RISK_WEIGHTS.get("sniper_detection", 25) / 100 +
            volume_score * RISK_WEIGHTS.get("wash_trading", 15) / 100 +
            insightx_score * RISK_WEIGHTS.get("distribution_metrics", 10) / 100 +
            pump_dump_score * RISK_WEIGHTS.get("pump_dump", 18) / 100 +  # NEW
            holder_score * RISK_WEIGHTS.get("holder_analysis", 15) / 100  # NEW: Whale/coordinated exit detection
        )

        overall_score = min(int(overall_score), 100)

        # Collect all red flags
        all_flags = []
        if distribution_analysis:
            all_flags.extend(distribution_analysis.red_flags)
        if creator_analysis:
            all_flags.extend(creator_analysis.red_flags)
        if liquidity_analysis:
            all_flags.extend(liquidity_analysis.red_flags)
        if social_analysis:
            all_flags.extend(social_analysis.red_flags)
        if wallet_analysis:
            all_flags.extend(wallet_analysis.red_flags)
        if sniper_analysis:
            all_flags.extend(sniper_analysis.red_flags)
        if volume_analysis:
            all_flags.extend(volume_analysis.red_flags)
        if pump_dump_analysis:  # NEW
            all_flags.extend(pump_dump_analysis.red_flags)
        if onchain_data and onchain_data.can_analyze:  # NEW: Holder analysis red flags
            all_flags.extend(onchain_data.red_flags)

        # Determine risk level and verdict
        if overall_score >= 75:
            risk_level = "EXTREME"
            verdict = "[!!] EXTREME DANGER - DO NOT BUY! This token shows multiple signs of a rug pull."
        elif overall_score >= 50:
            risk_level = "HIGH"
            verdict = "⛔ HIGH RISK - Very dangerous. Multiple red flags detected."
        elif overall_score >= 25:
            risk_level = "MEDIUM"
            verdict = "[!] MEDIUM RISK - Proceed with caution. Some concerns detected."
        else:
            risk_level = "LOW"
            verdict = "[OK] LOW RISK - Relatively safe, but always DYOR (Do Your Own Research)."

        # Generate recommendations
        recommendations = RiskScorer._generate_recommendations(
            overall_score,
            distribution_analysis,
            creator_analysis,
            liquidity_analysis,
            social_analysis,
            wallet_analysis,
            sniper_analysis,
            volume_analysis,
            distribution_metrics,
            onchain_data,
            pump_dump_analysis  # NEW
        )

        # NEW: Calculate confidence score
        confidence_score, confidence_level, confidence_factors = RiskScorer.calculate_confidence(
            token_age_hours,
            liquidity_analysis,
            creator_analysis,
            distribution_analysis,
            social_analysis,
            wallet_analysis,
            sniper_analysis,
            volume_analysis,
            distribution_metrics,
            onchain_data,
            pump_dump_analysis
        )

        return RiskReport(
            overall_risk_score=overall_score,
            risk_level=risk_level,
            verdict=verdict,
            all_red_flags=all_flags,
            recommendations=recommendations,
            distribution_score=dist_score,
            creator_score=creator_score,
            liquidity_score=liq_score,
            social_score=social_score,
            wallet_score=wallet_score,
            sniper_score=sniper_score,
            volume_score=volume_score,
            insightx_score=insightx_score,
            pump_dump_score=pump_dump_score,  # NEW
            holder_score=holder_score,  # NEW
            confidence_score=confidence_score,  # NEW
            confidence_level=confidence_level,  # NEW
            confidence_factors=confidence_factors  # NEW
        )

    @staticmethod
    def _calculate_insightx_score(distribution_metrics, onchain_data) -> int:
        """Calculate risk score from InsightX metrics and on-chain data"""
        score = 0

        if distribution_metrics:
            # Nakamoto coefficient (lower = more centralized = higher risk)
            nakamoto = distribution_metrics.get("nakamoto")
            if nakamoto:
                if nakamoto < 10:
                    score += 50  # EXTREME centralization
                elif nakamoto < 20:
                    score += 30
                elif nakamoto < 50:
                    score += 15

            # HHI (higher = more concentrated = higher risk)
            hhi = distribution_metrics.get("hhi")
            if hhi:
                if hhi > 0.8:
                    score += 40  # Monopoly level
                elif hhi > 0.5:
                    score += 25
                elif hhi > 0.25:
                    score += 10

        if onchain_data and onchain_data.can_analyze:
            # Fresh wallets in top 10 holders
            fresh_top10 = onchain_data.fresh_wallet_count_top10
            if fresh_top10:
                if fresh_top10 >= 7:
                    score += 40  # Most top holders are fresh
                elif fresh_top10 >= 5:
                    score += 25
                elif fresh_top10 >= 3:
                    score += 15

            # Top holder percentage
            top_holder = onchain_data.top_holder_percentage
            if top_holder:
                if top_holder > 50:
                    score += 30
                elif top_holder > 30:
                    score += 20
                elif top_holder > 20:
                    score += 10

        return min(score, 100)

    @staticmethod
    def _generate_recommendations(
        overall_score: int,
        distribution_analysis,
        creator_analysis,
        liquidity_analysis,
        social_analysis,
        wallet_analysis=None,
        sniper_analysis=None,
        volume_analysis=None,
        distribution_metrics=None,
        onchain_data=None,
        pump_dump_analysis=None  # NEW
    ) -> List[str]:
        """Generate actionable recommendations"""

        recommendations = []

        if overall_score >= 60:
            recommendations.append("[X] DO NOT INVEST - Risk is EXTREME")
        elif overall_score >= 50:
            recommendations.append("[X] DO NOT INVEST - Risk is too high")
        else:
            recommendations.append("[OK] If you invest, only use money you can afford to lose")
            recommendations.append("[OK] Set a stop-loss at -20% to -30%")

        if distribution_analysis and distribution_analysis.top_holder_percentage > 15:
            recommendations.append("[!] Watch top holder wallets for dumps")

        if creator_analysis and creator_analysis.rug_percentage > 30:
            recommendations.append("[!!] Creator has history of rugs - avoid completely")

        if liquidity_analysis and liquidity_analysis.liquidity_usd < 10000:
            recommendations.append("[!] Low liquidity - expect high slippage")

        if social_analysis and not social_analysis.has_twitter:
            recommendations.append("[!] No social presence - hard to verify legitimacy")

        if wallet_analysis:
            if wallet_analysis.fresh_wallet_percentage > 50:
                recommendations.append("[!!] Majority are fresh wallets - LIKELY FAKE HOLDERS")
            if wallet_analysis.suspected_dev_wallets > 10:
                recommendations.append("[!!] Many wallets controlled by dev - AVOID!")

        # NEW: Sniper analysis recommendations
        if sniper_analysis:
            if sniper_analysis.sniper_percentage > 70:
                recommendations.append("[!!] INSIDER TRADING DETECTED - Over 70% bought in first 10 seconds!")
            elif sniper_analysis.sniper_percentage > 50:
                recommendations.append("[!] High sniper activity - possible insider coordination")

            if sniper_analysis.bundle_transactions > 5:
                recommendations.append("[!!] Bundle buying detected - likely dev's multiple wallets")

        # Volume analysis recommendations
        if volume_analysis:
            if volume_analysis.is_fake_volume:
                recommendations.append("[!!] FAKE VOLUME DETECTED - Volume numbers are impossible/fabricated")
            elif volume_analysis.is_wash_trading:
                recommendations.append("[!!] WASH TRADING DETECTED - Volume is artificially inflated")

        # NEW: Pump & Dump recommendations
        if pump_dump_analysis:
            if pump_dump_analysis.is_pump_dump:
                recommendations.append("[!!] PUMP & DUMP PATTERN DETECTED - Price manipulation in progress!")
            if pump_dump_analysis.price_volatility > 150:
                recommendations.append("[!] Extreme price volatility - high risk of manipulation")
            if pump_dump_analysis.current_vs_ath_percentage < 30:
                recommendations.append("[!] Token has been heavily dumped from ATH - likely rugpulled")

        # Distribution metrics recommendations
        if distribution_metrics:
            nakamoto = distribution_metrics.get("nakamoto")
            if nakamoto and nakamoto < 10:
                recommendations.append(f"[!!] EXTREME CENTRALIZATION - Only {nakamoto} wallets control 51%")

        # On-chain fresh wallet recommendations
        if onchain_data and onchain_data.can_analyze:
            if onchain_data.fresh_wallet_count_top10 >= 7:
                recommendations.append("[!!] Most top holders are fresh wallets (<7 days) - SYBIL ATTACK LIKELY")
            elif onchain_data.fresh_wallet_count_top10 >= 5:
                recommendations.append("[!] Many fresh wallets in top 10 - suspicious coordination")

        # Always remind DYOR
        recommendations.append("[i] Always do your own research (DYOR)")
        recommendations.append("[i] Never invest more than you can afford to lose")

        return recommendations
