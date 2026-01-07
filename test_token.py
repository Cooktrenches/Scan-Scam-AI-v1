"""Test script to scan a specific token"""
import requests
import json
import time

def test_token(mint_address):
    print(f"\n{'='*80}")
    print(f"TESTING TOKEN: {mint_address}")
    print(f"{'='*80}\n")

    url = "http://localhost:5000/api/scan"

    print("Sending scan request...")
    start_time = time.time()

    try:
        response = requests.post(
            url,
            json={"mint_address": mint_address},
            timeout=60
        )

        elapsed = time.time() - start_time
        print(f"Response received in {elapsed:.2f}s\n")

        if response.status_code == 200:
            data = response.json()

            if not data.get("success"):
                print(f"[X] SCAN FAILED: {data.get('error', 'Unknown error')}")
                return

            # Token Info
            print(f"{'='*80}")
            print(f"TOKEN INFORMATION")
            print(f"{'='*80}")
            token_info = data.get("token_info", {})
            print(f"Name: {token_info.get('name')}")
            print(f"Symbol: {token_info.get('symbol')}")
            print(f"Age: {token_info.get('age')}")
            print(f"Creator: {token_info.get('creator')}")

            # Metadata
            metadata = data.get("metadata", {})
            print(f"\nSocial Links:")
            print(f"  Twitter: {metadata.get('twitter') or 'None'}")
            print(f"  Telegram: {metadata.get('telegram') or 'None'}")
            print(f"  Website: {metadata.get('website') or 'None'}")

            # Risk Assessment
            print(f"\n{'='*80}")
            print(f"RISK ASSESSMENT")
            print(f"{'='*80}")
            risk = data.get("risk_assessment", {})
            print(f"Overall Score: {risk.get('overall_score')}/100")
            print(f"Risk Level: {risk.get('risk_level')}")
            print(f"Verdict: {risk.get('verdict')}")

            # NEW: Confidence Score
            confidence = risk.get("confidence", {})
            if confidence:
                print(f"\n{'='*80}")
                print(f"CONFIDENCE ASSESSMENT (NEW!)")
                print(f"{'='*80}")
                print(f"Confidence Score: {confidence.get('score')}/100")
                print(f"Confidence Level: {confidence.get('level')}")
                print(f"\nFactors:")
                for factor in confidence.get('factors', []):
                    print(f"  {factor}")

            # Component Scores
            print(f"\n{'='*80}")
            print(f"COMPONENT SCORES")
            print(f"{'='*80}")
            components = risk.get("component_scores", {})
            for name, score in components.items():
                print(f"  {name}: {score}/100")

            # Market Data
            print(f"\n{'='*80}")
            print(f"MARKET DATA")
            print(f"{'='*80}")
            market = data.get("market_data", {})
            print(f"Market Cap: {market.get('market_cap')}")
            print(f"Liquidity: {market.get('liquidity')}")
            print(f"Price: {market.get('price')}")
            print(f"24h Volume: {market.get('volume_24h')}")

            # Creator Analysis
            creator_analysis = data.get("detailed_analysis", {}).get("creator_analysis", {})
            if creator_analysis.get("total_tokens_created", 0) > 0:
                print(f"\n{'='*80}")
                print(f"CREATOR HISTORY (ENHANCED!)")
                print(f"{'='*80}")
                print(f"Total Tokens Created: {creator_analysis.get('total_tokens_created')}")
                print(f"Potential Rugs: {creator_analysis.get('potential_rugs')}")
                print(f"Active Tokens: {creator_analysis.get('active_tokens')}")
                print(f"Rug Percentage: {creator_analysis.get('rug_percentage'):.1f}%")
                print(f"\nRed Flags:")
                for flag in creator_analysis.get('red_flags', []):
                    print(f"  {flag}")

            # NEW: Pump & Dump Advanced Analysis
            pump_dump = data.get("detailed_analysis", {}).get("pump_dump_analysis", {})
            if pump_dump:
                print(f"\n{'='*80}")
                print(f"ADVANCED PUMP & DUMP ANALYSIS (NEW!)")
                print(f"{'='*80}")
                if pump_dump.get("pattern_type"):
                    print(f"Pattern Detected: {pump_dump.get('pattern_type')}")
                if pump_dump.get("manipulation_confidence", 0) > 0:
                    print(f"Manipulation Confidence: {pump_dump.get('manipulation_confidence'):.1f}%")
                if pump_dump.get("pump_speed", 0) > 0:
                    print(f"Pump Speed: {pump_dump.get('pump_speed'):.1f}%/hour")
                if pump_dump.get("dump_speed", 0) > 0:
                    print(f"Dump Speed: {pump_dump.get('dump_speed'):.1f}%/hour")
                if pump_dump.get("coordinated_pumps_count", 0) > 0:
                    print(f"Coordinated Pumps: {pump_dump.get('coordinated_pumps_count')}")
                if pump_dump.get("time_at_peak"):
                    print(f"Time at Peak: {pump_dump.get('time_at_peak')} minutes")
                if pump_dump.get("stairs_pattern_detected"):
                    print("[!!] STAIRS PATTERN DETECTED (Bot Trading)")
                if pump_dump.get("dead_cat_bounce_detected"):
                    print("[!!] DEAD CAT BOUNCE DETECTED")

            # NEW: Holder Analysis
            holder_analysis = data.get("detailed_analysis", {}).get("holder_analysis", {})
            if holder_analysis and holder_analysis.get("total_holders", 0) > 0:
                print(f"\n{'='*80}")
                print(f"TOP HOLDERS ANALYSIS (NEW!)")
                print(f"{'='*80}")
                print(f"Total Holders: {holder_analysis.get('total_holders')}")
                print(f"Top Holder: {holder_analysis.get('top_holder_percentage')}")
                print(f"Top 3 Holders: {holder_analysis.get('top_3_percentage')}")
                print(f"Top 10 Holders: {holder_analysis.get('top_10_percentage')}")
                print(f"Exchanges in Top 10: {holder_analysis.get('exchanges_in_top_10')}")
                print(f"Fresh Wallets in Top 10: {holder_analysis.get('fresh_wallets_in_top_10')}")
                print(f"Average Holder Age: {holder_analysis.get('average_holder_age_days')} days")
                print(f"Holder Risk Score: {holder_analysis.get('risk_score')}/100")

                if holder_analysis.get('whale_dumping_detected'):
                    print("[!!] WHALE DUMPING DETECTED")
                if holder_analysis.get('coordinated_exit_detected'):
                    print(f"[!!] COORDINATED EXIT DETECTED ({holder_analysis.get('holders_selling_count')} holders selling)")

                holder_flags = holder_analysis.get('red_flags', [])
                if holder_flags:
                    print(f"\nHolder Red Flags:")
                    for flag in holder_flags[:5]:  # Show first 5
                        print(f"  {flag}")

            # ML Prediction
            ml = data.get("ml_prediction", {})
            if ml.get("enabled"):
                print(f"\n{'='*80}")
                print(f"AI PREDICTION")
                print(f"{'='*80}")
                print(f"Predicted Class: {ml.get('predicted_class')}")
                print(f"AI Score: {ml.get('score')}/100")
                print(f"Confidence: {ml.get('confidence'):.1f}%")

            # Red Flags Summary
            all_flags = data.get("detailed_analysis", {}).get("all_red_flags", [])
            if all_flags:
                print(f"\n{'='*80}")
                print(f"ALL RED FLAGS ({len(all_flags)} total)")
                print(f"{'='*80}")
                for flag in all_flags[:15]:  # Show first 15
                    print(f"  {flag}")
                if len(all_flags) > 15:
                    print(f"  ... and {len(all_flags) - 15} more")

            print(f"\n{'='*80}")
            print(f"[OK] SCAN COMPLETED SUCCESSFULLY")
            print(f"{'='*80}\n")

        else:
            print(f"[X] HTTP Error {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.Timeout:
        print("[X] REQUEST TIMEOUT (>60s)")
    except Exception as e:
        print(f"[X] ERROR: {e}")

if __name__ == "__main__":
    # Test the token
    mint_address = "7N61kfG6ejeyog4yyyCfhr3GJ5w8ShQLGaymdt3Xpump"
    test_token(mint_address)
