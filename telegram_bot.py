"""
SCAM AI - Telegram Bot
Scan Solana tokens directly from Telegram
"""
import os
import httpx
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import re

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://localhost:5000")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """🛡️ <b>SCAM AI - Solana Token Scanner V1</b>

<b>AI-Powered Rug Pull Detection</b>
Your first line of defense against Solana scams

🤖 <b>87% Prediction Accuracy</b>
Advanced Machine Learning model trained on 800+ real pump.fun tokens

🔍 <b>What We Analyze:</b>
• AI Safety Score (ML Prediction)
• Fresh Wallet Detection
• Insider Trading Patterns
• Wash Trading & Volume Analysis
• Developer Wallet History
• Top Holder Distribution
• Coordinated Buying/Selling

📋 <b>How to Use:</b>
• /scan &lt;token_address&gt; - Scan a token
• /help - Show commands
• Or simply paste any Solana address!

⚠️ <i>Always DYOR | Not financial advice</i>"""

    # Create inline keyboard with buttons
    keyboard = [
        [
            InlineKeyboardButton("🌐 Website", url="https://scamai.fun"),
            InlineKeyboardButton("🐦 Twitter", url="https://twitter.com/ScamAiScan")
        ],
        [
            InlineKeyboardButton("📖 Documentation", url="https://scamai.fun/bots"),
            InlineKeyboardButton("💬 Support", url="https://t.me/CookOfTrenches")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """📖 <b>SCAM AI - How to Use</b>

<b>🔍 Scanning Tokens</b>
<b>Method 1:</b> Use /scan command
<code>/scan TOKEN_ADDRESS</code>

<b>Method 2:</b> Auto-detect
Simply paste any Solana address (32-44 characters)

<b>📝 Example:</b>
<code>/scan FRqRKQwVDiBtjm2QWBVFAGpdZboph54CkbCAGSmypump</code>

<b>🎯 What We Analyze:</b>
✅ AI Safety Score (87% ML Accuracy)
✅ Fresh Wallet Detection
✅ Insider Trading Patterns
✅ Sniper Bot Analysis
✅ Wash Trading Detection
✅ Developer Wallet History
✅ Top Holder Distribution
✅ Coordinated Buying/Selling

<b>⏱️ Analysis Time:</b>
Most scans complete in 15-30 seconds

<b>🌐 Links:</b>
Website: scamai.fun
Twitter: @ScamAiScan</b>"""

    # Create inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("🌐 Website", url="https://scamai.fun"),
            InlineKeyboardButton("🐦 Twitter", url="https://twitter.com/ScamAiScan")
        ],
        [
            InlineKeyboardButton("📖 Documentation", url="https://scamai.fun/bots")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        help_text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def scan_token(update: Update, token_address: str):
    # No emojis to avoid Windows encoding issues
    if not re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', token_address):
        await update.message.reply_text("Invalid Solana address format!")
        return

    scanning_msg = await update.message.reply_text(
        f"🔍 <b>Scanning Token</b>\n"
        f"<code>{token_address[:8]}...{token_address[-8:]}</code>\n\n"
        f"⏳ <i>Running AI analysis...</i>\n"
        f"🤖 Analyzing holders, creator history & ML prediction\n"
        f"⏱️ This may take 15-30 seconds for complete analysis",
        parse_mode='HTML'
    )

    try:
        # Use GET request to match our API endpoint
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(f"{API_URL}/api/scan/{token_address}")

        if response.status_code != 200:
            error_data = response.json()
            await scanning_msg.edit_text(f"Error: {error_data.get('error', 'API Error')}")
            return

        data = response.json()

        # Parse response (correct structure from web_app.py)
        token_info = data.get("token_info", {})
        token_name = token_info.get("name", "Unknown")
        token_symbol = token_info.get("symbol", "???")

        risk_assessment = data.get("risk_assessment", {})
        risk_score = risk_assessment.get("overall_score", 0)
        risk_level = risk_assessment.get("risk_level", "UNKNOWN")

        # Build response message with emojis
        lines = []
        lines.append("🛡️ SCAM AI SCAN RESULTS")
        lines.append("━━━━━━━━━━━━━━━━━")

        # Token Info
        if token_name != "Unknown":
            lines.append(f"📊 {token_name} (${token_symbol})")
        else:
            lines.append(f"📊 Token: {token_address[:8]}...{token_address[-8:]}")
        lines.append("")

        # Risk Score with emoji based on risk_level (not just score)
        # Map risk_level to emoji (risk_level is more accurate than just score)
        if risk_level == "SAFE" or risk_level == "LOW":
            risk_emoji = "🟢"
        elif risk_level == "MODERATE" or risk_level == "MEDIUM":
            risk_emoji = "🟡"
        elif risk_level == "HIGH" or risk_level == "DANGER":
            risk_emoji = "🔴"
        elif risk_level == "CRITICAL" or risk_level == "EXTREME":
            risk_emoji = "⛔"
        else:
            # Fallback to score-based if level is unknown
            risk_emoji = "🟢" if risk_score < 25 else "🟡" if risk_score < 50 else "🔴" if risk_score < 75 else "⛔"

        lines.append(f"{risk_emoji} RISK SCORE: {risk_score}/100")
        lines.append(f"   Level: {risk_level}")

        # AI Score (ML Prediction) - ALWAYS show if available
        ml_prediction = data.get("ml_prediction", {})
        if ml_prediction and ml_prediction.get("score") is not None:
            ai_score = int(ml_prediction.get("score", 0))
            ai_class = ml_prediction.get("predicted_class", "Unknown")
            confidence = ml_prediction.get("confidence", 0)

            # AI emoji based on prediction
            ai_emoji = "✅" if ai_score >= 70 else "⚠️" if ai_score >= 30 else "❌"
            lines.append(f"{ai_emoji} AI PREDICTION: {ai_score}/100")
            lines.append(f"   Class: {ai_class}")
            lines.append(f"   Confidence: {confidence:.1f}%")

        # Analysis Confidence
        analysis_confidence = data.get("analysis_confidence", {})
        if analysis_confidence:
            conf_score = analysis_confidence.get("score", 0)
            conf_level = analysis_confidence.get("level", "UNKNOWN")
            conf_emoji = "🟢" if conf_score >= 70 else "🟡" if conf_score >= 50 else "🔴"
            lines.append(f"{conf_emoji} Analysis Quality: {conf_score}% - {conf_level}")

        lines.append("")

        # Market Data
        market_data = data.get("market_data", {})
        if market_data and any(market_data.values()):
            lines.append("💹 MARKET DATA")
            lines.append("━━━━━━━━━━━━━━━━━")

            price = market_data.get("price")
            if price:
                lines.append(f"💵 Price: {price}")

            mcap = market_data.get("market_cap")
            if mcap:
                lines.append(f"📈 Market Cap: {mcap}")

            volume = market_data.get("volume_24h")
            if volume:
                lines.append(f"📊 Volume 24h: {volume}")

            liquidity = market_data.get("liquidity")
            if liquidity:
                lines.append(f"💧 Liquidity: {liquidity}")

            lines.append("")

        # Holder Stats
        holder_stats = data.get("holder_stats", {})
        if holder_stats and holder_stats.get("total_holders", 0) > 0:
            lines.append("👥 HOLDERS")
            lines.append("━━━━━━━━━━━━━━━━━")

            total = holder_stats.get("total_holders", 0)
            lines.append(f"👤 Total: {total:,}")

            top_holder = holder_stats.get("top_holder_percentage", "N/A")
            if top_holder != "N/A":
                lines.append(f"🐋 Top Holder: {top_holder}")

            top_10 = holder_stats.get("top_10_percentage", "N/A")
            if top_10 != "N/A":
                lines.append(f"🔝 Top 10: {top_10}")

            # Fresh wallets in top 20
            fresh_top20 = holder_stats.get("fresh_wallets_top20", 0)
            if fresh_top20 > 0:
                fresh_pct = (fresh_top20 / 20) * 100
                warning = ""
                emoji = "⚠️"
                if fresh_top20 >= 14:
                    warning = " ⚠️ SYBIL ATTACK!"
                    emoji = "🚨"
                elif fresh_top20 >= 10:
                    warning = " ⚠️ Suspicious"
                    emoji = "⚠️"

                # Check for bundle detection
                detailed_analysis = data.get("detailed_analysis", {})
                sniper_analysis = detailed_analysis.get("sniper_analysis", {})
                bundle_text = ""
                if sniper_analysis and sniper_analysis.get("coordinated_buying"):
                    bundle_text = " | Bundle: Yes"

                lines.append(f"{emoji} Fresh Wallets: {fresh_top20}/20 ({fresh_pct:.0f}%){bundle_text}{warning}")

            lines.append("")

        # Creator Analysis
        creator_analysis = data.get("creator_analysis", {})
        if creator_analysis and creator_analysis.get("total_tokens_created", 0) > 0:
            total_tokens = creator_analysis.get("total_tokens_created", 0)
            rug_count = creator_analysis.get("rug_count", 0)

            if total_tokens > 5:  # Only show if significant
                lines.append("👨‍💻 CREATOR HISTORY")
                lines.append("━━━━━━━━━━━━━━━━━")
                lines.append(f"📊 Total Tokens: {total_tokens}")

                if rug_count > 0:
                    rug_pct = (rug_count / total_tokens) * 100
                    emoji = "🚨" if rug_pct > 50 else "⚠️" if rug_pct > 20 else "⚠️"
                    lines.append(f"{emoji} Rug Pulls: {rug_count} ({rug_pct:.1f}%)")

                    if rug_pct > 50:
                        lines.append("   🚨 SERIAL RUGGER!")
                lines.append("")

        # Red Flags (top 7)
        red_flags = data.get("red_flags", [])
        if red_flags:
            lines.append("🚨 ALERTS")
            lines.append("━━━━━━━━━━━━━━━━━")

            # Prioritize critical flags
            critical_flags = [f for f in red_flags if any(x in f for x in ["!!", "CRITICAL", "MASSIVE", "DUMPING", "SYBIL", "COORDINATED", "BUYING", "BOT"])]
            display_flags = critical_flags[:7] if critical_flags else red_flags[:7]

            for i, flag in enumerate(display_flags, 1):
                # Remove brackets from flags and add emoji
                clean_flag = flag.replace("[!!]", "").replace("[!]", "").strip()
                flag_emoji = "🔴" if "!!" in flag or "CRITICAL" in flag else "⚠️"
                lines.append(f"{flag_emoji} {clean_flag}")

            if len(red_flags) > 7:
                lines.append(f"   ... +{len(red_flags) - 7} more warnings")

            lines.append("")

        # Links (clickable) - Compact format like other bots
        lines.append("🔗 LINKS")
        lines.append("━━━━━━━━━━━━━━━━━")

        # Main analytics platforms
        links_row1 = (
            f"<a href='https://www.defined.fi/sol/{token_address}'>DEF</a>•"
            f"<a href='https://dexscreener.com/solana/{token_address}'>DS</a>•"
            f"<a href='https://www.geckoterminal.com/solana/pools/{token_address}'>GT</a>•"
            f"<a href='https://www.mobyscreener.com/solana/{token_address}'>MOB</a>•"
            f"<a href='https://solscan.io/token/{token_address}'>EXP</a>•"
            f"<a href='https://x.com/search?f=live&q={token_address}'>𝕏</a>"
        )
        lines.append(links_row1)

        # Trading platforms
        links_row2 = (
            f"<a href='https://gmgn.ai/sol/token/{token_address}'>GM</a>•"
            f"<a href='http://axiom.trade/t/{token_address}?chain=sol'>AXI</a>•"
            f"<a href='https://photon-sol.tinyastro.io/en/lp/{token_address}'>PHO</a>•"
            f"<a href='https://neo.bullx.io/terminal?chainId=1399811149&address={token_address}'>NEO</a>•"
            f"<a href='https://trade.padre.gg/trade/solana/{token_address}'>PDR</a>"
        )
        lines.append(links_row2)

        # Telegram trading bots
        links_row3 = (
            f"<a href='https://t.me/maestro?start={token_address}'>MAE</a>•"
            f"<a href='https://t.me/paris_trojanbot?start=d-{token_address}'>TRO</a>•"
            f"<a href='https://t.me/BloomSolana_bot?start=ref_ca_{token_address}'>BLO</a>•"
            f"<a href='https://t.me/furiosa_bonkbot?start=ref_ca_{token_address}'>BNK</a>•"
            f"<a href='https://t.me/pepeboost_sol_bot?start=ref_ca_{token_address}'>PEP</a>"
        )
        lines.append(links_row3)
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━")
        lines.append("⚠️ Always DYOR | Not financial advice")
        lines.append("🤖 Powered by SCAM AI - 87% Accuracy")

        # Join and send (Telegram has 4096 char limit)
        message = "\n".join(lines)
        if len(message) > 4000:
            # Split into chunks if too long
            chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
            await scanning_msg.edit_text(chunks[0], parse_mode='HTML', disable_web_page_preview=True)
            for chunk in chunks[1:]:
                await update.message.reply_text(chunk, parse_mode='HTML', disable_web_page_preview=True)
        else:
            await scanning_msg.edit_text(message, parse_mode='HTML', disable_web_page_preview=True)

    except httpx.TimeoutException:
        await scanning_msg.edit_text("Request timeout. The API is taking too long. Try again!")
    except Exception as e:
        print(f"Error scanning token: {e}")
        await scanning_msg.edit_text(f"Error: {str(e)}")

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # No emojis to avoid Windows encoding issues
    if not context.args:
        await update.message.reply_text("Please provide a token address!\n\nUsage: /scan <token_address>")
        return
    await scan_token(update, context.args[0])

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    solana_pattern = r'\b([1-9A-HJ-NP-Za-km-z]{32,44})\b'
    matches = re.findall(solana_pattern, text)
    if matches:
        await scan_token(update, matches[0])

def main():
    # No emojis to avoid Windows encoding issues
    print("=" * 50)
    print("   SCAM AI TELEGRAM BOT - STARTING")
    print("=" * 50)
    print(f"API URL: {API_URL}")
    print("Telegram bot is running...")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("scan", scan_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("Telegram bot is ready!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
