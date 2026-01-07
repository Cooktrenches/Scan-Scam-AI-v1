"""
SCAM AI - AI-Powered Solana Security Scanner
Flask Web Application & API
"""
from flask import Flask, render_template, request, jsonify, Response
import json
import sys
from io import StringIO
from contextlib import contextmanager
import threading

# Import scanner components
from liquidity_analyzer import LiquidityAnalyzer
from creator_checker import CreatorChecker
from social_checker import SocialChecker
from wallet_analyzer import WalletAnalyzer
from onchain_analyzer import OnChainAnalyzer
from sniper_detector import SniperDetector
from volume_analyzer import VolumeAnalyzer
from risk_scorer import RiskScorer
from insightx_api import InsightXAPI
from pump_dump_detector import PumpDumpDetector
from authority_checker import AuthorityChecker
from stats import tracker
from database import db

# Import ML module
import asyncio
from ml_module.predictor import TokenPredictor
from ml_module.feature_extractor import TokenFeatureExtractor

app = Flask(__name__)

# Initialize ML predictor (once at startup)
try:
    ml_predictor = TokenPredictor()
    ml_extractor = TokenFeatureExtractor()
    ml_enabled = True
    print("[ML] Modele ML charge avec succes!")
except Exception as e:
    ml_predictor = None
    ml_extractor = None
    ml_enabled = False
    print(f"[ML] Erreur chargement modele ML: {e}")

# Store for active scans
active_scans = {}
scan_lock = threading.Lock()


@contextmanager
def capture_output():
    """Capture stdout for progress updates"""
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        yield sys.stdout
    finally:
        sys.stdout = old_stdout


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/docs')
def docs():
    """Documentation page"""
    return render_template('docs.html')

@app.route('/bots')
def bots():
    """Discord & Telegram Bots page"""
    return render_template('bots.html')


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get scan statistics"""
    # Use database stats instead of file-based tracker
    db_stats = db.get_stats()
    db_stats['ml_enabled'] = ml_enabled  # Add ML status
    return jsonify(db_stats), 200


@app.route('/api/scan', methods=['POST'])
def scan_token():
    """
    Scan a token for rug pull indicators

    Request body:
    {
        "mint_address": "TOKEN_ADDRESS"
    }
    """
    try:
        data = request.get_json()
        mint_address = data.get('mint_address', '').strip()

        if not mint_address:
            return jsonify({"error": "Mint address is required"}), 400

        # Validate address format
        if len(mint_address) < 32 or len(mint_address) > 44:
            return jsonify({"error": "Invalid Solana address format"}), 400

        # Run analysis
        result = analyze_token_api(mint_address)

        # Increment old tracker (for compatibility)
        tracker.increment_scan()

        # Save scan to database
        if result.get("success"):
            token_info = result.get("token_info", {})
            risk_assessment = result.get("risk_assessment", {})
            ml_prediction = result.get("ml_prediction", {})

            db.add_scan(
                token_address=mint_address,
                token_name=token_info.get("name"),
                token_symbol=token_info.get("symbol"),
                risk_score=risk_assessment.get("overall_score"),
                risk_level=risk_assessment.get("risk_level"),
                ai_score=ml_prediction.get("score"),
                source="web",
                user_agent=request.headers.get('User-Agent'),
                ip_address=request.remote_addr
            )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scan/<mint_address>', methods=['GET'])
def scan_token_get(mint_address):
    """
    Scan a token for rug pull indicators (GET version for bots)
    URL parameter: mint_address (Solana token address)
    """
    try:
        mint_address = mint_address.strip()

        if not mint_address:
            return jsonify({"error": "Mint address is required"}), 400

        # Validate address format
        if len(mint_address) < 32 or len(mint_address) > 44:
            return jsonify({"error": "Invalid Solana address format"}), 400

        # Run analysis
        result = analyze_token_api(mint_address)

        # Increment old tracker (for compatibility)
        tracker.increment_scan()

        # Save scan to database
        if result.get("success"):
            token_info = result.get("token_info", {})
            risk_assessment = result.get("risk_assessment", {})
            ml_prediction = result.get("ml_prediction", {})

            db.add_scan(
                token_address=mint_address,
                token_name=token_info.get("name"),
                token_symbol=token_info.get("symbol"),
                risk_score=risk_assessment.get("overall_score"),
                risk_level=risk_assessment.get("risk_level"),
                ai_score=ml_prediction.get("score"),
                source="web",
                user_agent=request.headers.get('User-Agent'),
                ip_address=request.remote_addr
            )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def format_token_age(created_timestamp):
    """Format token age from timestamp"""
    if not created_timestamp:
        return "Unknown"

    import time
    from datetime import datetime, timezone

    # Handle milliseconds timestamp
    if created_timestamp > 10000000000:
        created_timestamp = created_timestamp / 1000

    now = time.time()
    age_seconds = int(now - created_timestamp)

    if age_seconds < 60:
        return f"{age_seconds} seconds"
    elif age_seconds < 3600:
        minutes = age_seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''}"
    elif age_seconds < 86400:
        hours = age_seconds // 3600
        minutes = (age_seconds % 3600) // 60
        return f"{hours} hour{'s' if hours > 1 else ''} {minutes} min"
    else:
        days = age_seconds // 86400
        hours = (age_seconds % 86400) // 3600
        return f"{days} day{'s' if days > 1 else ''} {hours} hour{'s' if hours > 1 else ''}"


def analyze_token_api(mint_address: str) -> dict:
    """
    Run full token analysis and return results as JSON
    """
    # Initialize analyzers
    liq_analyzer = LiquidityAnalyzer()
    creator_checker = CreatorChecker()
    social_checker = SocialChecker()
    wallet_analyzer = WalletAnalyzer()
    onchain_analyzer = OnChainAnalyzer()
    sniper_detector = SniperDetector()
    volume_analyzer = VolumeAnalyzer()
    insightx = InsightXAPI()
    pump_dump_detector = PumpDumpDetector()
    authority_checker = AuthorityChecker()

    try:
        # Fetch token data
        token_data = liq_analyzer.get_token_data(mint_address)

        if not token_data:
            return {
                "error": "Could not fetch token data. Token may not exist.",
                "mint_address": mint_address
            }

        creator_address = token_data.get("creator")

        # Run analyses
        liquidity_analysis = liq_analyzer.analyze_liquidity(mint_address)

        creator_analysis = None
        if creator_address:
            creator_analysis = creator_checker.analyze_creator(creator_address)

        social_analysis = social_checker.analyze_social(token_data)

        # On-chain data (get this FIRST as it's most reliable)
        onchain_data = None
        try:
            onchain_data = onchain_analyzer.get_token_holders(mint_address)
        except Exception:
            pass

        # Wallet analysis (try Pump.fun API first, fallback to onchain data)
        wallet_analysis = None
        try:
            holder_response = wallet_analyzer.client.get(
                f"https://frontend-api.pump.fun/coins/{mint_address}/holders",
                timeout=10.0
            )
            if holder_response.status_code == 200:
                holders_data = holder_response.json()
                if holders_data and len(holders_data) > 0:
                    wallet_analysis = wallet_analyzer.analyze_holders(
                        holders_data,
                        creator_address,
                        mint_address
                    )
        except Exception:
            pass

        # FALLBACK: If wallet_analysis failed but onchain_data worked, create synthetic wallet_analysis
        if not wallet_analysis and onchain_data and onchain_data.can_analyze:
            from wallet_analyzer import SybilAnalysis
            # Calculate fresh wallet percentage from top 20 holders
            fresh_count = sum(1 for h in onchain_data.holders if h.get("is_fresh", False))
            fresh_pct = (fresh_count / len(onchain_data.holders) * 100) if onchain_data.holders else 0

            wallet_analysis = SybilAnalysis(
                total_holders=onchain_data.total_holders,
                fresh_wallet_count=fresh_count,
                fresh_wallet_percentage=fresh_pct,
                suspected_dev_wallets=0,  # Can't determine from blockchain alone
                wallets_buying_same_creator=0,
                batch_created_wallets=onchain_data.fresh_wallet_count_top10,
                wallets_created_same_minute=0,
                low_activity_wallets=0,
                never_sold_wallets=0,
                identical_balance_clusters=0,
                risk_score=min(fresh_pct * 0.8, 100),  # Basic risk based on fresh wallets
                red_flags=[f"[!] {fresh_pct:.0f}% of top holders are fresh wallets (<7 days)"] if fresh_pct > 30 else [],
                suspicious_wallets=[]
            )

        # Sniper analysis
        sniper_analysis = None
        try:
            token_creation_time = token_data.get("created_timestamp")
            sniper_analysis = sniper_detector.analyze_snipers(mint_address, token_creation_time)
        except Exception:
            pass

        # Volume analysis
        volume_analysis = None
        try:
            liquidity = liquidity_analysis.liquidity_usd if liquidity_analysis else 0
            volume_analysis = volume_analyzer.analyze_volume(token_data, liquidity)
        except Exception:
            pass

        # InsightX metrics
        distribution_metrics = None
        try:
            distribution_metrics = insightx.get_distribution_metrics(mint_address, network="sol")
        except Exception:
            pass

        # Pump & dump analysis
        pump_dump_analysis = None
        try:
            pump_dump_analysis = pump_dump_detector.analyze_pump_dump(mint_address, token_data)
        except Exception:
            pass

        # Authority check (CRITICAL!)
        authority_analysis = None
        try:
            authority_analysis = authority_checker.check_authority(mint_address)
        except Exception:
            pass

        # ML Prediction (NEW!)
        ml_prediction = None
        if ml_enabled:
            try:
                print(f"[ML] Starting prediction for {mint_address[:8]}...")
                # Extract features asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                features = loop.run_until_complete(ml_extractor.extract_all_features(mint_address))
                loop.close()

                if features:
                    print(f"[ML] Features extracted successfully, making prediction...")

                    # Filter out non-numeric columns (metadata)
                    exclude_cols = ['label', 'token_mint', 'timestamp', 'label_reason', 'collected_at']
                    clean_features = {k: v for k, v in features.items() if k not in exclude_cols}

                    # Make prediction
                    risk_level, ml_score, details = ml_predictor.predict_with_score(clean_features)

                    ml_prediction = {
                        "enabled": True,
                        "score": ml_score,  # 0-100: 0=RUG, 100=SUCCESS
                        "predicted_class": details['predicted_class'],
                        "confidence": details['confidence'],
                        "risk_level": risk_level,
                        "probabilities": details['probabilities']
                    }
                    print(f"[ML] Prediction complete: {details['predicted_class']} ({ml_score}/100)")
                else:
                    print(f"[ML] ERROR: Could not extract features for {mint_address[:8]}")
                    ml_prediction = {"enabled": False, "error": "Could not extract features"}
            except Exception as e:
                import traceback
                print(f"[ML] ERROR during prediction: {e}")
                traceback.print_exc()
                ml_prediction = {"enabled": False, "error": str(e)}

        # Calculate token age (for display and confidence)
        token_age = format_token_age(token_data.get("created_timestamp"))

        # Calculate token age in hours (for confidence calculation)
        token_age_hours = None
        created_timestamp = token_data.get("created_timestamp")
        if created_timestamp:
            import time
            # Handle milliseconds timestamp
            if created_timestamp > 10000000000:
                created_timestamp = created_timestamp / 1000
            now = time.time()
            age_seconds = now - created_timestamp
            token_age_hours = age_seconds / 3600  # Convert to hours

        # Calculate risk
        risk_report = RiskScorer.calculate_risk(
            None,  # distribution_analysis
            creator_analysis,
            liquidity_analysis,
            social_analysis,
            wallet_analysis,
            sniper_analysis,
            volume_analysis,
            distribution_metrics,
            onchain_data,
            pump_dump_analysis,
            token_age_hours  # NEW: Pass token age for confidence calculation
        )

        # CRITICAL: Apply additional penalties for missed red flags
        additional_risk = 0

        # Penalty 1: Fresh wallets in top 10 (CRITICAL!)
        if onchain_data and onchain_data.can_analyze:
            fresh_top10 = onchain_data.fresh_wallet_count_top10
            if fresh_top10 >= 8:
                additional_risk += 40  # 80%+ fresh wallets = HUGE red flag!
            elif fresh_top10 >= 5:
                additional_risk += 25  # 50%+ fresh wallets = Major red flag
            elif fresh_top10 >= 3:
                additional_risk += 15  # 30%+ fresh wallets = Warning

        # Penalty 2: Small market cap (< $100K = very risky on Pump.fun)
        if liquidity_analysis:
            mcap = liquidity_analysis.market_cap_usd
            if mcap < 50000:
                additional_risk += 20  # Under $50K = extreme risk
            elif mcap < 100000:
                additional_risk += 10  # Under $100K = high risk

        # Penalty 3: High top holder concentration
        if onchain_data and onchain_data.can_analyze:
            top_holder_pct = onchain_data.top_holder_percentage
            if top_holder_pct > 30:
                additional_risk += 15  # One person controls 30%+
            elif top_holder_pct > 20:
                additional_risk += 10  # One person controls 20%+

        # Apply additional risk (cap at 100)
        final_risk_score = min(risk_report.overall_risk_score + additional_risk, 100)

        # Convert risk score to safety score (INVERTED for better UX)
        # Risk: 0 = safe, 100 = danger
        # Safety: 100 = safe, 0 = danger
        safety_score = 100 - final_risk_score

        # Determine safety level based on safety score
        if safety_score >= 70:
            safety_level = "SAFE"
            safety_emoji = "[OK]"
            safety_verdict = "[OK] SAFE - Low risk detected. Relatively safe investment."
        elif safety_score >= 30:
            safety_level = "MODERATE"
            safety_emoji = "[!]"
            safety_verdict = "[!] MODERATE RISK - Proceed with caution. Some concerns detected."
        else:
            safety_level = "DANGER"
            safety_emoji = "[X]"
            safety_verdict = "[!!] DANGER - High risk! Multiple red flags detected. DO NOT BUY without thorough research."

        # Format response
        response = {
            "success": True,
            "mint_address": mint_address,
            "token_info": {
                "name": token_data.get("name", "N/A"),
                "symbol": token_data.get("symbol", "N/A"),
                "creator": creator_address or "N/A",
                "age": token_age,
                "created_timestamp": token_data.get("created_timestamp")
            },
            "metadata": {
                "twitter": token_data.get("twitter"),
                "telegram": token_data.get("telegram"),
                "website": token_data.get("website"),
                "description": token_data.get("description")
            },
            "risk_assessment": {
                "overall_score": safety_score,  # NOW INVERTED: 100 = safe
                "risk_level": safety_level,  # SAFE, MODERATE, DANGER
                "verdict": safety_verdict,
                "component_scores": {
                    "liquidity": risk_report.liquidity_score,
                    "creator_history": risk_report.creator_score,
                    "social_presence": risk_report.social_score,
                    "wallet_analysis": risk_report.wallet_score,
                    "sniper_detection": risk_report.sniper_score,
                    "volume_analysis": risk_report.volume_score,
                    "pump_dump": risk_report.pump_dump_score,
                    "holder_analysis": risk_report.holder_score,  # NEW
                    "distribution": risk_report.insightx_score
                },
                "confidence": {  # NEW: Confidence scoring
                    "score": risk_report.confidence_score,
                    "level": risk_report.confidence_level,
                    "factors": risk_report.confidence_factors
                }
            },
            "market_data": {
                "market_cap": f"${liquidity_analysis.market_cap_usd:,.2f}" if liquidity_analysis else "N/A",
                "liquidity": f"${liquidity_analysis.liquidity_usd:,.2f}" if liquidity_analysis else "N/A",
                "price": f"${liquidity_analysis.price_usd:.8f}" if liquidity_analysis else "N/A",
                "volume_24h": f"${volume_analysis.volume_24h:,.0f}" if volume_analysis and volume_analysis.volume_24h else "N/A",
                "bonding_curve_complete": liquidity_analysis.bonding_curve_complete if liquidity_analysis else False
            },
            "holder_stats": {
                "total_holders": onchain_data.total_holders if onchain_data and onchain_data.can_analyze else (wallet_analysis.total_holders if wallet_analysis else 0),
                "top_holder_percentage": f"{onchain_data.top_holder_percentage:.2f}%" if onchain_data and onchain_data.can_analyze else "N/A",
                "top_10_percentage": f"{onchain_data.top_10_percentage:.2f}%" if onchain_data and onchain_data.can_analyze else "N/A",
                "fresh_wallets_top10": onchain_data.fresh_wallet_count_top10 if onchain_data and onchain_data.can_analyze else 0,
                "fresh_wallets_top20": onchain_data.fresh_wallet_count_top20 if onchain_data and onchain_data.can_analyze else 0
            },
            "red_flags": risk_report.all_red_flags,
            "recommendations": risk_report.recommendations,
            "detailed_analysis": {
                "sniper_analysis": {
                    "instant_snipers": sniper_analysis.instant_snipers if sniper_analysis else 0,
                    "instant_sniper_percentage": f"{sniper_analysis.instant_sniper_percentage:.1f}%" if sniper_analysis else "0%",
                    "total_snipers": sniper_analysis.sniper_count if sniper_analysis else 0,
                    "sniper_percentage": f"{sniper_analysis.sniper_percentage:.1f}%" if sniper_analysis else "0%",
                    "coordinated_buying": sniper_analysis.coordinated_buy_detected if sniper_analysis else False
                },
                "volume_analysis": {
                    "is_wash_trading": volume_analysis.is_wash_trading if volume_analysis else False,
                    "is_fake_volume": volume_analysis.is_fake_volume if volume_analysis else False,
                    "volume_to_mcap_ratio": f"{volume_analysis.volume_to_mcap_ratio:.1f}x" if volume_analysis else "N/A",
                    "buy_volume_percentage": f"{volume_analysis.buy_volume_percentage:.0f}%" if volume_analysis else "N/A"
                },
                "pump_dump_analysis": {
                    "is_pump_dump": pump_dump_analysis.is_pump_dump if pump_dump_analysis else False,
                    "price_volatility": f"{pump_dump_analysis.price_volatility:.0f}%" if pump_dump_analysis else "0%",
                    "max_price_spike": f"{pump_dump_analysis.max_price_spike:.0f}%" if pump_dump_analysis else "0%",
                    # NEW: Advanced pattern detection fields
                    "pattern_type": pump_dump_analysis.pattern_type if pump_dump_analysis else None,
                    "coordinated_pumps_count": pump_dump_analysis.coordinated_pumps_count if pump_dump_analysis else 0,
                    "time_at_peak": pump_dump_analysis.time_at_peak if pump_dump_analysis else None,
                    "pump_speed": pump_dump_analysis.pump_speed if pump_dump_analysis else 0,
                    "dump_speed": pump_dump_analysis.dump_speed if pump_dump_analysis else 0,
                    "stairs_pattern_detected": pump_dump_analysis.stairs_pattern_detected if pump_dump_analysis else False,
                    "dead_cat_bounce_detected": pump_dump_analysis.dead_cat_bounce_detected if pump_dump_analysis else False,
                    "manipulation_confidence": pump_dump_analysis.manipulation_confidence if pump_dump_analysis else 0
                },
                "wallet_analysis": {
                    "fresh_wallet_percentage": f"{wallet_analysis.fresh_wallet_percentage:.0f}%" if wallet_analysis else "0%",
                    "suspected_dev_wallets": wallet_analysis.suspected_dev_wallets if wallet_analysis else 0,
                    "low_activity_wallets": wallet_analysis.low_activity_wallets if wallet_analysis else 0
                },
                "authority_analysis": {
                    "mint_authority_renounced": authority_analysis.mint_authority_renounced if authority_analysis else False,
                    "freeze_authority_renounced": authority_analysis.freeze_authority_renounced if authority_analysis else False,
                    "authority_red_flags": authority_analysis.red_flags if authority_analysis else []
                },
                "holder_analysis": {
                    "total_holders": onchain_data.total_holders if onchain_data and onchain_data.can_analyze else 0,
                    "top_holder_percentage": f"{onchain_data.top_holder_percentage:.1f}%" if onchain_data and onchain_data.can_analyze else "0%",
                    "top_3_percentage": f"{onchain_data.top_3_percentage:.1f}%" if onchain_data and onchain_data.can_analyze else "0%",
                    "top_10_percentage": f"{onchain_data.top_10_percentage:.1f}%" if onchain_data and onchain_data.can_analyze else "0%",
                    "exchanges_in_top_10": onchain_data.exchanges_in_top_10 if onchain_data and onchain_data.can_analyze else 0,
                    "fresh_wallets_in_top_10": onchain_data.fresh_wallet_count_top10 if onchain_data and onchain_data.can_analyze else 0,
                    "whale_dumping_detected": onchain_data.whale_dumping_detected if onchain_data and onchain_data.can_analyze else False,
                    "coordinated_exit_detected": onchain_data.coordinated_exit_detected if onchain_data and onchain_data.can_analyze else False,
                    "holders_selling_count": onchain_data.holders_selling_count if onchain_data and onchain_data.can_analyze else 0,
                    "average_holder_age_days": f"{onchain_data.average_holder_age_days:.1f}" if onchain_data and onchain_data.can_analyze else "N/A",
                    "risk_score": onchain_data.risk_score if onchain_data and onchain_data.can_analyze else 0,
                    "red_flags": onchain_data.red_flags if onchain_data and onchain_data.can_analyze else []
                }
            },
            "ml_prediction": ml_prediction if ml_prediction else {"enabled": False}
        }

        return response

    finally:
        # Cleanup
        liq_analyzer.close()
        creator_checker.close()
        social_checker.close()
        wallet_analyzer.close()
        onchain_analyzer.close()
        sniper_detector.close()
        insightx.close()
        pump_dump_detector.close()
        authority_checker.close()


if __name__ == '__main__':
    # Fix Windows encoding
    import sys
    import os
    if sys.platform == "win32":
        os.system("chcp 65001 >nul 2>&1")
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')

    # Get port from environment (for Render deployment) or default to 5000
    port = int(os.environ.get('PORT', 5000))

    print("Starting SCAM AI Web Server...")
    print(f"Access at: http://localhost:{port}")
    print(f"Documentation: http://localhost:{port}/docs")
    app.run(debug=False, host='0.0.0.0', port=port)
