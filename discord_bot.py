"""
SCAM AI - Discord Bot
Scan Solana tokens directly from Discord
"""
import discord
from discord import app_commands
from discord.ext import commands
import os
import httpx
from dotenv import load_dotenv
import asyncio
from datetime import datetime
import re

load_dotenv()

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://localhost:5000")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Colors for embeds
COLOR_SAFE = 0x00ff88      # Green
COLOR_LOW = 0x00ff88       # Green
COLOR_MEDIUM = 0xffaa00    # Orange
COLOR_HIGH = 0xff3333      # Red
COLOR_EXTREME = 0x990000   # Dark Red
COLOR_INFO = 0x00aaff      # Blue

def get_risk_color(risk_score):
    """Get color based on risk score"""
    if risk_score < 25:
        return COLOR_LOW
    elif risk_score < 50:
        return COLOR_MEDIUM
    elif risk_score < 75:
        return COLOR_HIGH
    else:
        return COLOR_EXTREME

def get_risk_emoji(risk_score):
    """Get emoji based on risk score"""
    if risk_score < 25:
        return "🟢"
    elif risk_score < 50:
        return "🟡"
    elif risk_score < 75:
        return "🔴"
    else:
        return "⛔"

def get_risk_emoji_from_level(risk_level):
    """Get emoji based on risk level (more accurate than score)"""
    risk_level = risk_level.upper()
    if risk_level in ["SAFE", "LOW"]:
        return "🟢"
    elif risk_level in ["MODERATE", "MEDIUM"]:
        return "🟡"
    elif risk_level in ["HIGH", "DANGER"]:
        return "🔴"
    elif risk_level in ["CRITICAL", "EXTREME"]:
        return "⛔"
    else:
        # Fallback to score-based
        return "🟡"

@bot.event
async def on_ready():
    """Bot startup"""
    print("=" * 50)
    print("   SCAM AI DISCORD BOT - ONLINE")
    print("=" * 50)
    print(f"Bot: {bot.user.name}")
    print(f"ID: {bot.user.id}")
    print(f"Servers: {len(bot.guilds)}")
    print(f"API: {API_URL}")
    print(f"Ready to scan tokens!")

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.event
async def on_message(message):
    """Detect Solana addresses in messages and auto-scan"""
    # Ignore bot messages
    if message.author.bot:
        return

    # Regex to detect Solana addresses (32-44 base58 characters)
    solana_pattern = r'\b([1-9A-HJ-NP-Za-km-z]{32,44})\b'
    matches = re.findall(solana_pattern, message.content)

    if matches:
        # Take the first address found
        token_address = matches[0]

        # React to show we detected it
        try:
            await message.add_reaction("👀")
        except:
            pass

        # Scan the token
        await scan_and_reply(message.channel, token_address, message)

    # Allow commands to work
    await bot.process_commands(message)

async def scan_and_reply(channel, token_address: str, reference_message=None):
    """Scan a token and send the result to a channel"""

    # Validate address format
    if len(token_address) < 32 or len(token_address) > 44:
        return

    # Send scanning message
    scanning_embed = discord.Embed(
        title="🔍 Scanning Token",
        description=f"`{token_address[:8]}...{token_address[-8:]}`",
        color=COLOR_INFO
    )
    scanning_embed.add_field(name="⏳ Running AI analysis...", value="🤖 Analyzing holders, creator history & ML prediction\n⏱️ This may take 15-30 seconds for complete analysis", inline=False)

    if reference_message:
        scanning_msg = await channel.send(embed=scanning_embed, reference=reference_message)
    else:
        scanning_msg = await channel.send(embed=scanning_embed)

    try:
        # Call SCAM AI API (using GET like Telegram bot)
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(f"{API_URL}/api/scan/{token_address}")

            if response.status_code != 200:
                error_embed = discord.Embed(
                    title="❌ Scan Failed",
                    description="API returned an error",
                    color=COLOR_HIGH
                )
                error_embed.add_field(name="Status", value=str(response.status_code), inline=True)
                await scanning_msg.edit(embed=error_embed)
                return

            data = response.json()

            if not data.get("success"):
                error_embed = discord.Embed(
                    title="❌ Analysis Failed",
                    description=data.get("error", "Unknown error"),
                    color=COLOR_HIGH
                )
                await scanning_msg.edit(embed=error_embed)
                return

            # Extract data
            token_info = data.get("token_info", {})
            risk = data.get("risk_assessment", {})
            ml_pred = data.get("ml_prediction", {})
            market = data.get("market_data", {})
            holders = data.get("holder_stats", {})
            red_flags = data.get("red_flags", [])
            detailed = data.get("detailed_analysis", {})
            sniper_data = detailed.get("sniper_analysis", {}) if detailed else {}

            # Debug: print what we received
            print(f"DEBUG - Market data keys: {list(market.keys()) if market else 'None'}")
            print(f"DEBUG - Holders data keys: {list(holders.keys()) if holders else 'None'}")
            print(f"DEBUG - ML Prediction keys: {list(ml_pred.keys()) if ml_pred else 'None'}")

            risk_score = risk.get("overall_score", 0)
            risk_level = risk.get("risk_level", "UNKNOWN")
            confidence = risk.get("confidence", {})

            # Create result embed (use risk_level for emoji like Telegram bot)
            color = get_risk_color(risk_score)
            emoji = get_risk_emoji_from_level(risk_level)

            # Build header like Telegram bot
            token_name = token_info.get('name', 'Unknown')
            token_symbol = token_info.get('symbol', 'N/A')

            embed = discord.Embed(
                title="🛡️ SCAM AI SCAN RESULTS",
                description=f"━━━━━━━━━━━━━━━━━\n📊 **{token_name}** (${token_symbol})",
                color=color,
                timestamp=datetime.utcnow()
            )

            # RISK SCORE with emoji and level (like Telegram)
            risk_text = f"{emoji} **RISK SCORE: {risk_score}/100**\n   Level: {risk_level}"
            embed.add_field(name="⚠️ Risk Assessment", value=risk_text, inline=False)

            # AI Score only (on one line) - ALWAYS show if available
            try:
                if ml_pred and ml_pred.get("score") is not None:
                    ai_score = int(ml_pred.get("score", 0))
                    ai_class = ml_pred.get("predicted_class", "UNKNOWN")

                    # No emoji to avoid Windows encoding issues
                    embed.add_field(
                        name="AI Safety Score",
                        value=f"**{ai_score}/100** - {ai_class}",
                        inline=False
                    )
                    print(f"[DEBUG] AI Score added: {ai_score}/100 - {ai_class}")
            except (ValueError, TypeError) as e:
                print(f"[DEBUG] AI Score error: {e}")
                pass

            # Compact Market Overview - PARSE STRINGS FROM API
            market_overview = ""
            if market:
                try:
                    # Parse market cap (remove $ and commas)
                    mcap_str = market.get("market_cap", "0")
                    mcap = float(mcap_str.replace("$", "").replace(",", ""))

                    # Parse liquidity (remove $ and commas)
                    liq_str = market.get("liquidity", "0")
                    liquidity = float(liq_str.replace("$", "").replace(",", ""))

                    # Parse volume (remove $ and commas)
                    vol_str = market.get("volume_24h", "0")
                    volume = float(vol_str.replace("$", "").replace(",", ""))

                    # Get age from token_info
                    age = token_info.get("age", "N/A")

                    # FDV
                    fdv_text = f"${mcap/1000:.1f}K" if mcap < 1000000 else f"${mcap/1000000:.1f}M"
                    market_overview += f"💎 FDV: {fdv_text}\n"

                    # Liquidity
                    liq_text = f"${liquidity/1000:.1f}K" if liquidity < 1000000 else f"${liquidity/1000000:.1f}M"
                    market_overview += f"💧 Liq: {liq_text} ⋅ LP: \n"

                    # Volume and Age
                    vol_text = f"${volume/1000:.1f}K" if volume < 1000000 else f"${volume/1000000:.1f}M"
                    market_overview += f"📊 Vol: {vol_text} ⋅ Age: {age}\n"
                except (ValueError, TypeError) as e:
                    print(f"Market parsing error: {e}")
                    pass

            if market_overview:
                embed.add_field(name="💰 Market", value=market_overview.strip(), inline=False)

            # Top Holders Compact - USE REAL API KEYS
            if holders:
                try:
                    holder_text = ""

                    # Top holder percentage (from API)
                    top_holder_pct_str = holders.get("top_holder_percentage", "0%")
                    top_holder_pct = float(top_holder_pct_str.replace("%", ""))

                    # Top 10 percentage (from API)
                    top_10_pct_str = holders.get("top_10_percentage", "0%")
                    top_10_pct = float(top_10_pct_str.replace("%", ""))

                    if top_holder_pct > 0:
                        holder_text += f"🐋 Top Holder: {top_holder_pct:.1f}% | Top 10: {top_10_pct:.1f}%\n"

                    # Total holders
                    total = int(holders.get("total_holders", 0))
                    if total > 0:
                        holder_text += f"👥 Total: {total}\n"

                    # Fresh wallets in top 20 - SYBIL ATTACK INDICATOR
                    fresh_top20 = int(holders.get("fresh_wallets_top20", 0))
                    if fresh_top20 > 0:
                        fresh_pct = (fresh_top20 / 20) * 100

                        # Warning based on severity (adjusted for /20)
                        if fresh_top20 >= 14:
                            warning = "SYBIL ATTACK"
                        elif fresh_top20 >= 10:
                            warning = "Suspicious"
                        else:
                            warning = ""

                        holder_text += f"Fresh: {fresh_top20}/20 ({fresh_pct:.0f}%)"

                        # Add bundle detection on same line
                        if sniper_data:
                            bundled = sniper_data.get("coordinated_buying", False)
                            if bundled:
                                holder_text += f" | Bundle: Yes"

                        if warning:
                            holder_text += f" - {warning}"
                        holder_text += "\n"

                    if holder_text:
                        embed.add_field(name="👥 Holders", value=holder_text.strip(), inline=False)
                except (ValueError, TypeError) as e:
                    print(f"Holder parsing error: {e}")
                    pass

            # Sniper/DEV Detection - Removed (API doesn't provide this data)

            # Quick Links - Organized by category
            # Charts - Main trading charts
            charts_text = f"[DEX](https://dexscreener.com/solana/{token_address}) ⋅ "
            charts_text += f"[DEF](https://www.defined.fi/sol/{token_address})"
            embed.add_field(name="📊 Charts", value=charts_text, inline=True)

            # Trade - Trading platforms
            trade_text = f"[GM](https://gmgn.ai/sol/token/{token_address}) ⋅ "
            trade_text += f"[AXI](http://axiom.trade/t/{token_address}?chain=sol) ⋅ "
            trade_text += f"[PHO](https://photon-sol.tinyastro.io/en/lp/{token_address}) ⋅ "
            trade_text += f"[NEO](https://neo.bullx.io/terminal?chainId=1399811149&address={token_address})"
            embed.add_field(name="💹 Trade", value=trade_text, inline=True)

            # Analytics - Other analytics tools
            analytics_text = f"[GT](https://www.geckoterminal.com/solana/pools/{token_address}) ⋅ "
            analytics_text += f"[MOB](https://www.mobyscreener.com/solana/{token_address}) ⋅ "
            analytics_text += f"[EXP](https://solscan.io/token/{token_address})"
            embed.add_field(name="🔍 Analytics", value=analytics_text, inline=True)

            # Show up to 7 most critical alerts (increased from 3 for better visibility)
            if red_flags:
                critical_flags = [f for f in red_flags if any(x in f for x in ["!!", "CRITICAL", "MASSIVE", "DUMPING", "SYBIL", "COORDINATED", "BUYING", "BOT"])]
                display_flags = critical_flags[:7] if critical_flags else red_flags[:7]
                flags_text = "\n".join([f"⚠️ {flag}" for flag in display_flags])
                if len(red_flags) > 7:
                    flags_text += f"\n*+{len(red_flags) - 7} more warnings*"
                embed.add_field(name="🚨 Alerts", value=flags_text, inline=False)

            # Footer
            embed.set_footer(
                text="SCAM AI v1.0 | Always DYOR | Not financial advice",
                icon_url=bot.user.avatar.url if bot.user.avatar else None
            )

            # Send result
            await scanning_msg.edit(embed=embed)

    except httpx.TimeoutException:
        error_embed = discord.Embed(
            title="⏱️ Request Timeout",
            description="The API took too long to respond. Please try again.",
            color=COLOR_HIGH
        )
        await scanning_msg.edit(embed=error_embed)
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Error",
            description=f"An unexpected error occurred:\n```{str(e)}```",
            color=COLOR_HIGH
        )
        await scanning_msg.edit(embed=error_embed)

@bot.tree.command(name="scan", description="🔍 Scan a Solana token for rug pull indicators")
@app_commands.describe(token_address="The Solana token mint address to analyze")
async def scan(interaction: discord.Interaction, token_address: str):
    """Scan a token for rug pull indicators"""

    # Defer response (scanning takes time)
    await interaction.response.defer(thinking=True)

    # Validate address format
    if len(token_address) < 32 or len(token_address) > 44:
        error_embed = discord.Embed(
            title="❌ Invalid Token Address",
            description=f"The address `{token_address}` doesn't look like a valid Solana address.",
            color=COLOR_HIGH
        )
        error_embed.add_field(
            name="Expected Format",
            value="32-44 characters (base58)",
            inline=False
        )
        error_embed.add_field(
            name="Example",
            value="`BDuWXaAcs88guisXQWvdiDGDVNn7eR7Wxw3Q5KLgpump`",
            inline=False
        )
        await interaction.followup.send(embed=error_embed)
        return

    # Send scanning message
    scanning_embed = discord.Embed(
        title="🔍 Scanning Token",
        description=f"`{token_address[:8]}...{token_address[-8:]}`",
        color=COLOR_INFO
    )
    scanning_embed.add_field(name="⏳ Running AI analysis...", value="🤖 Analyzing holders, creator history & ML prediction\n⏱️ This may take 15-30 seconds for complete analysis", inline=False)
    await interaction.followup.send(embed=scanning_embed)

    try:
        # Call SCAM AI API (using GET like Telegram bot)
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(f"{API_URL}/api/scan/{token_address}")

            if response.status_code != 200:
                error_embed = discord.Embed(
                    title="❌ Scan Failed",
                    description="API returned an error",
                    color=COLOR_HIGH
                )
                error_embed.add_field(name="Status", value=str(response.status_code), inline=True)
                error_embed.add_field(name="Error", value=response.text[:200], inline=False)
                await interaction.edit_original_response(embed=error_embed)
                return

            data = response.json()

            if not data.get("success"):
                error_embed = discord.Embed(
                    title="❌ Analysis Failed",
                    description=data.get("error", "Unknown error"),
                    color=COLOR_HIGH
                )
                await interaction.edit_original_response(embed=error_embed)
                return

            # Extract data
            token_info = data.get("token_info", {})
            risk = data.get("risk_assessment", {})
            ml_pred = data.get("ml_prediction", {})
            market = data.get("market_data", {})
            holders = data.get("holder_stats", {})
            red_flags = data.get("red_flags", [])
            detailed = data.get("detailed_analysis", {})
            sniper_data = detailed.get("sniper_analysis", {}) if detailed else {}

            # Debug: print what we received
            print(f"DEBUG - Market data keys: {list(market.keys()) if market else 'None'}")
            print(f"DEBUG - Holders data keys: {list(holders.keys()) if holders else 'None'}")
            print(f"DEBUG - ML Prediction keys: {list(ml_pred.keys()) if ml_pred else 'None'}")

            risk_score = risk.get("overall_score", 0)
            risk_level = risk.get("risk_level", "UNKNOWN")
            confidence = risk.get("confidence", {})

            # Create result embed (use risk_level for emoji like Telegram bot)
            color = get_risk_color(risk_score)
            emoji = get_risk_emoji_from_level(risk_level)

            # Build header like Telegram bot
            token_name = token_info.get('name', 'Unknown')
            token_symbol = token_info.get('symbol', 'N/A')

            embed = discord.Embed(
                title="🛡️ SCAM AI SCAN RESULTS",
                description=f"━━━━━━━━━━━━━━━━━\n📊 **{token_name}** (${token_symbol})",
                color=color,
                timestamp=datetime.utcnow()
            )

            # RISK SCORE with emoji and level (like Telegram)
            risk_text = f"{emoji} **RISK SCORE: {risk_score}/100**\n   Level: {risk_level}"
            embed.add_field(name="⚠️ Risk Assessment", value=risk_text, inline=False)

            # AI Score only (on one line) - ALWAYS show if available
            try:
                if ml_pred and ml_pred.get("score") is not None:
                    ai_score = int(ml_pred.get("score", 0))
                    ai_class = ml_pred.get("predicted_class", "UNKNOWN")

                    # No emoji to avoid Windows encoding issues
                    embed.add_field(
                        name="AI Safety Score",
                        value=f"**{ai_score}/100** - {ai_class}",
                        inline=False
                    )
                    print(f"[DEBUG] AI Score added: {ai_score}/100 - {ai_class}")
            except (ValueError, TypeError) as e:
                print(f"[DEBUG] AI Score error: {e}")
                pass

            # Compact Market Overview - PARSE STRINGS FROM API
            market_overview = ""
            if market:
                try:
                    # Parse market cap (remove $ and commas)
                    mcap_str = market.get("market_cap", "0")
                    mcap = float(mcap_str.replace("$", "").replace(",", ""))

                    # Parse liquidity (remove $ and commas)
                    liq_str = market.get("liquidity", "0")
                    liquidity = float(liq_str.replace("$", "").replace(",", ""))

                    # Parse volume (remove $ and commas)
                    vol_str = market.get("volume_24h", "0")
                    volume = float(vol_str.replace("$", "").replace(",", ""))

                    # Get age from token_info
                    age = token_info.get("age", "N/A")

                    # FDV
                    fdv_text = f"${mcap/1000:.1f}K" if mcap < 1000000 else f"${mcap/1000000:.1f}M"
                    market_overview += f"💎 FDV: {fdv_text}\n"

                    # Liquidity
                    liq_text = f"${liquidity/1000:.1f}K" if liquidity < 1000000 else f"${liquidity/1000000:.1f}M"
                    market_overview += f"💧 Liq: {liq_text} ⋅ LP: \n"

                    # Volume and Age
                    vol_text = f"${volume/1000:.1f}K" if volume < 1000000 else f"${volume/1000000:.1f}M"
                    market_overview += f"📊 Vol: {vol_text} ⋅ Age: {age}\n"
                except (ValueError, TypeError) as e:
                    print(f"Market parsing error: {e}")
                    pass

            if market_overview:
                embed.add_field(name="💰 Market", value=market_overview.strip(), inline=False)

            # Top Holders Compact - USE REAL API KEYS
            if holders:
                try:
                    holder_text = ""

                    # Top holder percentage (from API)
                    top_holder_pct_str = holders.get("top_holder_percentage", "0%")
                    top_holder_pct = float(top_holder_pct_str.replace("%", ""))

                    # Top 10 percentage (from API)
                    top_10_pct_str = holders.get("top_10_percentage", "0%")
                    top_10_pct = float(top_10_pct_str.replace("%", ""))

                    if top_holder_pct > 0:
                        holder_text += f"🐋 Top Holder: {top_holder_pct:.1f}% | Top 10: {top_10_pct:.1f}%\n"

                    # Total holders
                    total = int(holders.get("total_holders", 0))
                    if total > 0:
                        holder_text += f"👥 Total: {total}\n"

                    # Fresh wallets in top 20 - SYBIL ATTACK INDICATOR
                    fresh_top20 = int(holders.get("fresh_wallets_top20", 0))
                    if fresh_top20 > 0:
                        fresh_pct = (fresh_top20 / 20) * 100

                        # Warning based on severity (adjusted for /20)
                        if fresh_top20 >= 14:
                            warning = "SYBIL ATTACK"
                        elif fresh_top20 >= 10:
                            warning = "Suspicious"
                        else:
                            warning = ""

                        holder_text += f"Fresh: {fresh_top20}/20 ({fresh_pct:.0f}%)"

                        # Add bundle detection on same line
                        if sniper_data:
                            bundled = sniper_data.get("coordinated_buying", False)
                            if bundled:
                                holder_text += f" | Bundle: Yes"

                        if warning:
                            holder_text += f" - {warning}"
                        holder_text += "\n"

                    if holder_text:
                        embed.add_field(name="👥 Holders", value=holder_text.strip(), inline=False)
                except (ValueError, TypeError) as e:
                    print(f"Holder parsing error: {e}")
                    pass

            # Sniper/DEV Detection - Removed (API doesn't provide this data)

            # Quick Links - Organized by category
            # Charts - Main trading charts
            charts_text = f"[DEX](https://dexscreener.com/solana/{token_address}) ⋅ "
            charts_text += f"[DEF](https://www.defined.fi/sol/{token_address})"
            embed.add_field(name="📊 Charts", value=charts_text, inline=True)

            # Trade - Trading platforms
            trade_text = f"[GM](https://gmgn.ai/sol/token/{token_address}) ⋅ "
            trade_text += f"[AXI](http://axiom.trade/t/{token_address}?chain=sol) ⋅ "
            trade_text += f"[PHO](https://photon-sol.tinyastro.io/en/lp/{token_address}) ⋅ "
            trade_text += f"[NEO](https://neo.bullx.io/terminal?chainId=1399811149&address={token_address})"
            embed.add_field(name="💹 Trade", value=trade_text, inline=True)

            # Analytics - Other analytics tools
            analytics_text = f"[GT](https://www.geckoterminal.com/solana/pools/{token_address}) ⋅ "
            analytics_text += f"[MOB](https://www.mobyscreener.com/solana/{token_address}) ⋅ "
            analytics_text += f"[EXP](https://solscan.io/token/{token_address})"
            embed.add_field(name="🔍 Analytics", value=analytics_text, inline=True)

            # Show up to 7 most critical alerts (increased from 3 for better visibility)
            if red_flags:
                critical_flags = [f for f in red_flags if any(x in f for x in ["!!", "CRITICAL", "MASSIVE", "DUMPING", "SYBIL", "COORDINATED", "BUYING", "BOT"])]
                display_flags = critical_flags[:7] if critical_flags else red_flags[:7]
                flags_text = "\n".join([f"⚠️ {flag}" for flag in display_flags])
                if len(red_flags) > 7:
                    flags_text += f"\n*+{len(red_flags) - 7} more warnings*"
                embed.add_field(name="🚨 Alerts", value=flags_text, inline=False)

            # Footer
            embed.set_footer(
                text="SCAM AI v1.0 | Always DYOR | Not financial advice",
                icon_url=bot.user.avatar.url if bot.user.avatar else None
            )

            # Send result
            await interaction.edit_original_response(embed=embed)

    except httpx.TimeoutException:
        error_embed = discord.Embed(
            title="⏱️ Request Timeout",
            description="The API took too long to respond. Please try again.",
            color=COLOR_HIGH
        )
        await interaction.edit_original_response(embed=error_embed)
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Error",
            description=f"An unexpected error occurred:\n```{str(e)}```",
            color=COLOR_HIGH
        )
        await interaction.edit_original_response(embed=error_embed)

@bot.tree.command(name="stats", description="📊 View SCAM AI scanner statistics")
async def stats(interaction: discord.Interaction):
    """Show scanner statistics"""
    await interaction.response.defer(thinking=True)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_URL}/api/stats")

            if response.status_code == 200:
                data = response.json()

                embed = discord.Embed(
                    title="📊 SCAM AI Statistics",
                    description="Scanner usage and performance",
                    color=COLOR_INFO,
                    timestamp=datetime.utcnow()
                )

                embed.add_field(
                    name="🔍 Total Scans",
                    value=f"{data.get('total_scans', 0):,}",
                    inline=True
                )
                embed.add_field(
                    name="🔴 High Risk",
                    value=f"{data.get('total_high_risk', 0):,}",
                    inline=True
                )
                embed.add_field(
                    name="🟡 Medium Risk",
                    value=f"{data.get('total_medium_risk', 0):,}",
                    inline=True
                )
                embed.add_field(
                    name="🟢 Low Risk",
                    value=f"{data.get('total_low_risk', 0):,}",
                    inline=True
                )

                if data.get("ml_enabled"):
                    embed.add_field(
                        name="🤖 AI Status",
                        value="✅ Enabled",
                        inline=True
                    )

                embed.set_footer(text="SCAM AI v1.0")
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("❌ Failed to fetch statistics")

    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="help", description="❓ Show help and commands")
async def help_command(interaction: discord.Interaction):
    """Show help"""
    embed = discord.Embed(
        title="🤖 SCAM AI - Discord Bot Help",
        description="AI-powered Solana token security scanner with **87% accuracy**\nTrained on **800+ real tokens** from Pump.fun",
        color=COLOR_INFO
    )

    embed.add_field(
        name="/scan <token_address>",
        value="🔍 Scan a Solana token for rug pull indicators\nExample: `/scan BDuWXaAcs88guisXQWvdiDGDVNn7eR7Wxw3Q5KLgpump`",
        inline=False
    )

    embed.add_field(
        name="/stats",
        value="📊 View scanner statistics",
        inline=False
    )

    embed.add_field(
        name="/help",
        value="❓ Show this help message",
        inline=False
    )

    embed.add_field(
        name="🌐 Links",
        value="[Website](https://scamai.fun) | [Twitter](https://x.com/ScamAIscanner) | [Documentation](https://scamai.fun/bots) | [Support](https://t.me/CookOfTrenches)",
        inline=False
    )

    embed.add_field(
        name="⚠️ Disclaimer",
        value="Always DYOR (Do Your Own Research). This is not financial advice.",
        inline=False
    )

    embed.set_footer(text="SCAM AI v1.0 | ©SCAM AI 2025")

    await interaction.response.send_message(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"Error: {error}")

def main():
    """Run the bot"""
    if not DISCORD_TOKEN:
        print("❌ ERROR: DISCORD_BOT_TOKEN not found in .env file")
        print("Please add your Discord bot token to .env:")
        print("DISCORD_BOT_TOKEN=your_token_here")
        return

    print("Starting SCAM AI Discord Bot...")
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()
