"""
SCAM AI - AI-Powered Solana Token Security Scanner
"""
import sys
import os

# Fix Windows encoding issues
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from liquidity_analyzer import LiquidityAnalyzer
from creator_checker import CreatorChecker
from social_checker import SocialChecker
from wallet_analyzer import WalletAnalyzer
from onchain_analyzer import OnChainAnalyzer
from sniper_detector import SniperDetector
from volume_analyzer import VolumeAnalyzer
from batch_analyzer import BatchAnalyzer
from risk_scorer import RiskScorer
from insightx_api import InsightXAPI
from pump_dump_detector import PumpDumpDetector  # NEW

console = Console(force_terminal=True, legacy_windows=False)


def print_banner():
    """Print tool banner"""
    banner = """
===============================================================
        SCAM AI - SOLANA SECURITY SCANNER
        Protect yourself from scams!
===============================================================
    """
    console.print(banner, style="bold cyan")


def analyze_token(mint_address: str):
    """Main analysis function"""

    console.print(f"\n[bold]Analyzing token:[/bold] [cyan]{mint_address}[/cyan]\n")

    # Initialize analyzers
    liq_analyzer = LiquidityAnalyzer()
    creator_checker = CreatorChecker()
    social_checker = SocialChecker()
    wallet_analyzer = WalletAnalyzer()
    onchain_analyzer = OnChainAnalyzer()
    sniper_detector = SniperDetector()
    volume_analyzer = VolumeAnalyzer()
    insightx = InsightXAPI()
    pump_dump_detector = PumpDumpDetector()  # NEW

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # Fetch basic token data
            task1 = progress.add_task("Fetching token data...", total=None)
            token_data = liq_analyzer.get_token_data(mint_address)

            if not token_data:
                console.print("[red][X] Error: Could not fetch token data. Check the mint address.[/red]")
                return

            progress.update(task1, completed=True)

            # Extract creator address
            creator_address = token_data.get("creator")

            # Run all analyses
            task2 = progress.add_task("Analyzing liquidity...", total=None)
            liquidity_analysis = liq_analyzer.analyze_liquidity(mint_address)
            progress.update(task2, completed=True)

            task3 = progress.add_task("Checking creator history...", total=None)
            creator_analysis = None
            if creator_address:
                creator_analysis = creator_checker.analyze_creator(creator_address)
            progress.update(task3, completed=True)

            task4 = progress.add_task("Analyzing social presence...", total=None)
            social_analysis = social_checker.analyze_social(token_data)
            progress.update(task4, completed=True)

            task5 = progress.add_task("Analyzing wallet patterns (fresh wallets, sybil)...", total=None)
            wallet_analysis = None
            # Get holder data from pump.fun API
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
                pass  # Continue without wallet analysis if it fails
            progress.update(task5, completed=True)

            task6 = progress.add_task("Detecting snipers and bundle buyers...", total=None)
            sniper_analysis = None
            try:
                token_creation_time = token_data.get("created_timestamp")
                sniper_analysis = sniper_detector.analyze_snipers(mint_address, token_creation_time)
            except Exception:
                pass
            progress.update(task6, completed=True)

            task7 = progress.add_task("Analyzing trading volume (wash trading)...", total=None)
            volume_analysis = None
            try:
                # Get liquidity value for volume analysis
                liquidity = liquidity_analysis.liquidity_usd if liquidity_analysis else 0
                volume_analysis = volume_analyzer.analyze_volume(token_data, liquidity)
            except Exception:
                pass
            progress.update(task7, completed=True)

            task8 = progress.add_task("Fetching distribution metrics (InsightX)...", total=None)
            distribution_metrics = None
            scanner_results = None
            insightx_sniper_metrics = None
            insightx_cluster_metrics = None
            try:
                distribution_metrics = insightx.get_distribution_metrics(mint_address, network="sol")
                scanner_results = insightx.scan_token(mint_address, network="sol")
                # Try to get sniper and cluster metrics from InsightX
                insightx_sniper_metrics = insightx.get_sniper_metrics(mint_address, network="sol")
                insightx_cluster_metrics = insightx.get_cluster_metrics(mint_address, network="sol")
            except Exception:
                pass
            progress.update(task8, completed=True)

            task9 = progress.add_task("Analyzing pump & dump patterns...", total=None)
            pump_dump_analysis = None
            try:
                pump_dump_analysis = pump_dump_detector.analyze_pump_dump(mint_address, token_data)
            except Exception:
                pass
            progress.update(task9, completed=True)

        # Note: Distribution analysis would require full token account scanning
        # which can be slow/expensive. Skipping for now but code is in token_analyzer.py
        distribution_analysis = None

        # Fetch on-chain holder data (for fresh wallet analysis in top 10)
        onchain_data = None
        try:
            console.print("\n[yellow]Fetching holder data from blockchain...[/yellow]")
            onchain_data = onchain_analyzer.get_token_holders(mint_address)
        except Exception:
            pass

        # Calculate overall risk (IMPROVED: includes all detection modules)
        risk_report = RiskScorer.calculate_risk(
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

        # Display results
        display_results(token_data, liquidity_analysis, creator_analysis, social_analysis, wallet_analysis,
                        risk_report, onchain_data, sniper_analysis, volume_analysis, distribution_metrics, scanner_results,
                        insightx_sniper_metrics, insightx_cluster_metrics, pump_dump_analysis)

    finally:
        # Cleanup
        liq_analyzer.close()
        creator_checker.close()
        social_checker.close()
        wallet_analyzer.close()
        onchain_analyzer.close()
        sniper_detector.close()
        insightx.close()
        pump_dump_detector.close()  # NEW


def display_results(token_data, liquidity_analysis, creator_analysis, social_analysis, wallet_analysis, risk_report, onchain_data=None, sniper_analysis=None, volume_analysis=None, distribution_metrics=None, scanner_results=None, insightx_sniper_metrics=None, insightx_cluster_metrics=None, pump_dump_analysis=None):
    """Display analysis results"""

    # Token Info
    console.print("\n" + "=" * 60 + "\n", style="bold")

    info_table = Table(title="📋 Token Information", show_header=False, box=None)
    info_table.add_column("Field", style="cyan")
    info_table.add_column("Value", style="white")

    info_table.add_row("Name", token_data.get("name", "N/A"))
    info_table.add_row("Symbol", token_data.get("symbol", "N/A"))
    info_table.add_row("Mint", token_data.get("mint", "N/A"))

    creator = token_data.get("creator", "N/A")
    if creator and creator != "N/A":
        info_table.add_row("Creator", creator)

    console.print(info_table)

    # Overall Risk Score
    console.print("\n")
    risk_color = "red" if risk_report.overall_risk_score >= 50 else "yellow" if risk_report.overall_risk_score >= 25 else "green"

    risk_panel = Panel(
        f"[bold {risk_color}]{risk_report.risk_level}[/bold {risk_color}]\n\n"
        f"Risk Score: [bold]{risk_report.overall_risk_score}/100[/bold]\n\n"
        f"{risk_report.verdict}",
        title="🎯 RISK ASSESSMENT",
        border_style=risk_color
    )
    console.print(risk_panel)

    # Component Scores
    console.print("\n")
    scores_table = Table(title="📊 Detailed Scores", show_header=True)
    scores_table.add_column("Component", style="cyan")
    scores_table.add_column("Score", justify="right")
    scores_table.add_column("Status", justify="center")

    def get_status_emoji(score):
        if score >= 50:
            return "🔴 High Risk"
        elif score >= 25:
            return "🟡 Medium"
        else:
            return "🟢 Low Risk"

    scores_table.add_row("Liquidity", f"{risk_report.liquidity_score}/100", get_status_emoji(risk_report.liquidity_score))
    scores_table.add_row("Creator History", f"{risk_report.creator_score}/100", get_status_emoji(risk_report.creator_score))
    scores_table.add_row("Social Presence", f"{risk_report.social_score}/100", get_status_emoji(risk_report.social_score))
    scores_table.add_row("Wallet Analysis", f"{risk_report.wallet_score}/100", get_status_emoji(risk_report.wallet_score))

    console.print(scores_table)

    # Market Data
    if liquidity_analysis:
        console.print("\n")
        market_table = Table(title="💰 Market Data", show_header=False, box=None)
        market_table.add_column("Metric", style="cyan")
        market_table.add_column("Value", style="white")

        market_table.add_row("Market Cap", f"${liquidity_analysis.market_cap_usd:,.2f}")
        market_table.add_row("Liquidity", f"${liquidity_analysis.liquidity_usd:,.2f}")
        market_table.add_row("Price", f"${liquidity_analysis.price_usd:.8f}")
        market_table.add_row("Bonding Curve", "[OK] Complete" if liquidity_analysis.bonding_curve_complete else "[~] In Progress")

        # Show DEX status (PumpSwap or Raydium)
        dex_status = "[OK] PumpSwap" if liquidity_analysis.migrated_to_raydium else "[X] Not migrated"
        market_table.add_row("DEX", dex_status)

        console.print(market_table)

    # Social Media
    if social_analysis:
        console.print("\n")
        social_table = Table(title="🌐 Social Media Presence", show_header=False, box=None)
        social_table.add_column("Platform", style="cyan")
        social_table.add_column("Status", style="white")

        # Get URLs from token_data
        twitter_url = token_data.get("twitter")
        telegram_url = token_data.get("telegram")
        website_url = token_data.get("website")

        twitter_status = f"[OK] {twitter_url}" if twitter_url else "[X] Not Found"
        telegram_status = f"[OK] {telegram_url}" if telegram_url else "[X] Not Found"
        website_status = f"[OK] {website_url}" if website_url else "[X] Not Found"

        social_table.add_row("Twitter", twitter_status)
        social_table.add_row("Telegram", telegram_status)
        social_table.add_row("Website", website_status)

        desc_quality = social_analysis.description_quality
        desc_color = "green" if desc_quality == "good" else "yellow" if desc_quality == "suspicious" else "red"
        desc_text = {
            "good": "[OK] Good",
            "suspicious": "[!] Suspicious",
            "empty": "[X] Empty"
        }.get(desc_quality, "Unknown")
        social_table.add_row("Description", f"[{desc_color}]{desc_text}[/{desc_color}]")

        console.print(social_table)

    # Creator History
    if creator_analysis and creator_analysis.total_tokens_created > 0:
        console.print("\n")
        creator_table = Table(title="👤 Creator History", show_header=False, box=None)
        creator_table.add_column("Metric", style="cyan")
        creator_table.add_column("Value", style="white")

        creator_table.add_row("Total Tokens Created", str(creator_analysis.total_tokens_created))
        creator_table.add_row("Potential Rugs", str(creator_analysis.potential_rugs))
        creator_table.add_row("Still Active", str(creator_analysis.active_tokens))
        creator_table.add_row("Rug Percentage", f"{creator_analysis.rug_percentage:.1f}%")

        console.print(creator_table)

    # Wallet Analysis (Fresh Wallets & Sybil)
    if wallet_analysis:
        console.print("\n")
        wallet_table = Table(title="👥 Wallet Analysis (Fresh Wallets & Sybil Detection)", show_header=False, box=None)
        wallet_table.add_column("Metric", style="cyan")
        wallet_table.add_column("Value", style="white")

        # Total holders with color coding
        holders_color = "green" if wallet_analysis.total_holders > 200 else "yellow" if wallet_analysis.total_holders > 50 else "red"
        wallet_table.add_row("Total Holders", f"[{holders_color}]{wallet_analysis.total_holders}[/{holders_color}]")

        # Fresh wallets with percentage
        fresh_color = "red" if wallet_analysis.fresh_wallet_percentage > 50 else "yellow" if wallet_analysis.fresh_wallet_percentage > 30 else "green"
        wallet_table.add_row("Fresh Wallets (<7 days)", f"[{fresh_color}]{wallet_analysis.fresh_wallet_count} ({wallet_analysis.fresh_wallet_percentage:.1f}%)[/{fresh_color}]")

        # Batch created
        batch_color = "red" if wallet_analysis.batch_created_wallets > 10 else "yellow" if wallet_analysis.batch_created_wallets > 5 else "green"
        wallet_table.add_row("Wallets Created in 24h", f"[{batch_color}]{wallet_analysis.batch_created_wallets}[/{batch_color}]")

        # Suspected dev wallets
        dev_color = "red" if wallet_analysis.suspected_dev_wallets > 10 else "yellow" if wallet_analysis.suspected_dev_wallets > 5 else "green"
        wallet_table.add_row("Suspected Dev Wallets", f"[{dev_color}]{wallet_analysis.suspected_dev_wallets}[/{dev_color}]")

        wallet_table.add_row("Only Buys This Creator", str(wallet_analysis.wallets_buying_same_creator))

        console.print(wallet_table)

    # Sniper Analysis - Always show even if limited data
    if sniper_analysis:
        console.print("\n")
        sniper_table = Table(title="🎯 Sniper & Bundle Detection (Insider Trading)", show_header=False, box=None)
        sniper_table.add_column("Metric", style="cyan")
        sniper_table.add_column("Value", style="white")

        if sniper_analysis.total_early_buyers > 0:
            sniper_table.add_row("Early Buyers (First Minute)", str(sniper_analysis.total_early_buyers))

            # Snipers
            sniper_color = "red" if sniper_analysis.sniper_percentage > 50 else "yellow" if sniper_analysis.sniper_percentage > 30 else "green"
            sniper_table.add_row("Snipers (First 10 sec)", f"[{sniper_color}]{sniper_analysis.sniper_count} ({sniper_analysis.sniper_percentage:.1f}%)[/{sniper_color}]")

            # Bundles
            bundle_color = "red" if sniper_analysis.bundle_transactions > 5 else "yellow" if sniper_analysis.bundle_transactions > 2 else "green"
            sniper_table.add_row("Bundle Transactions", f"[{bundle_color}]{sniper_analysis.bundle_transactions}[/{bundle_color}]")
            sniper_table.add_row("Bundle Wallets", str(sniper_analysis.bundle_wallets))

            # Suspected insiders
            insider_color = "red" if sniper_analysis.suspected_insiders > 10 else "yellow" if sniper_analysis.suspected_insiders > 5 else "green"
            sniper_table.add_row("Suspected Insiders", f"[{insider_color}]{sniper_analysis.suspected_insiders}[/{insider_color}]")

            # Wallet clusters
            if sniper_analysis.cluster_count > 0:
                cluster_color = "red" if sniper_analysis.cluster_count > 2 else "yellow"
                sniper_table.add_row("Wallet Clusters Detected", f"[{cluster_color}]{sniper_analysis.cluster_count} clusters ({sniper_analysis.cluster_wallets} wallets)[/{cluster_color}]")
        else:
            sniper_table.add_row("Status", "[yellow][!] Transaction data not available from RPC[/yellow]")
            sniper_table.add_row("Note", "[dim]Sniper/bundle detection requires transaction history access[/dim]")

        console.print(sniper_table)

        # Show wallet clusters details
        if sniper_analysis.wallet_clusters and len(sniper_analysis.wallet_clusters) > 0:
            console.print("")
            console.print("[bold red][!!] WALLET CLUSTERS (Same Purchase History):[/bold red]")
            for i, cluster in enumerate(sniper_analysis.wallet_clusters[:5], 1):  # Show first 5 clusters
                wallet_list = ", ".join([f"{w[:4]}...{w[-4:]}" for w in cluster[:5]])  # Show first 5 wallets
                more_text = f" +{len(cluster) - 5} more" if len(cluster) > 5 else ""
                console.print(f"  Cluster {i}: {wallet_list}{more_text}")

        # Show sniper red flags
        if sniper_analysis.red_flags:
            console.print("")
            for flag in sniper_analysis.red_flags:
                console.print(f"  {flag}")

    # InsightX Sniper Metrics (if available)
    if insightx_sniper_metrics:
        console.print("\n")
        console.print("[bold cyan]📊 InsightX Sniper Analysis:[/bold cyan]")
        # Display InsightX sniper data (structure depends on API response)
        # This will show detailed sniper metrics when available
        import json
        console.print(f"[dim]{json.dumps(insightx_sniper_metrics, indent=2)}[/dim]")

    # InsightX Cluster Metrics (if available)
    if insightx_cluster_metrics:
        console.print("\n")
        console.print("[bold cyan]📊 InsightX Cluster Analysis:[/bold cyan]")
        # Display InsightX cluster data
        import json
        console.print(f"[dim]{json.dumps(insightx_cluster_metrics, indent=2)}[/dim]")

    # Volume Analysis - Always show
    if volume_analysis:
        console.print("\n")
        volume_table = Table(title="📊 Volume Analysis (Wash Trading Detection)", show_header=False, box=None)
        volume_table.add_column("Metric", style="cyan")
        volume_table.add_column("Value", style="white")

        if volume_analysis.volume_24h > 0:
            volume_table.add_row("24h Volume", f"${volume_analysis.volume_24h:,.0f}")
            volume_table.add_row("Market Cap", f"${volume_analysis.market_cap:,.0f}")

            # Volume to MCap ratio
            ratio_color = "red" if volume_analysis.volume_to_mcap_ratio > 20 else "yellow" if volume_analysis.volume_to_mcap_ratio > 10 else "green"
            volume_table.add_row("Volume/MCap Ratio", f"[{ratio_color}]{volume_analysis.volume_to_mcap_ratio:.2f}x[/{ratio_color}]")

            # Buy/Sell ratio
            bs_ratio_color = "yellow" if (volume_analysis.buy_sell_ratio > 5 or (volume_analysis.buy_sell_ratio > 0 and volume_analysis.buy_sell_ratio < 0.2)) else "green"
            volume_table.add_row("Buy/Sell Ratio", f"[{bs_ratio_color}]{volume_analysis.buy_sell_ratio:.2f}[/{bs_ratio_color}]")

            # Wash trading verdict
            if volume_analysis.is_wash_trading:
                volume_table.add_row("Status", "[bold red][!!] WASH TRADING DETECTED[/bold red]")
            else:
                volume_table.add_row("Status", "[green][OK] Normal Activity[/green]")
        else:
            volume_table.add_row("24h Volume", "$0 or data unavailable")
            volume_table.add_row("Status", "[yellow][!] No volume data available[/yellow]")

        console.print(volume_table)

        # Show volume red flags
        if volume_analysis.red_flags:
            console.print("")
            for flag in volume_analysis.red_flags:
                console.print(f"  {flag}")

    # NEW: Pump & Dump Analysis
    if pump_dump_analysis:
        console.print("\n")
        pd_table = Table(title="📈 Pump & Dump Analysis", show_header=False, box=None)
        pd_table.add_column("Metric", style="cyan")
        pd_table.add_column("Value", style="white")

        # Volatility
        if pump_dump_analysis.price_volatility > 0:
            vol_color = "red" if pump_dump_analysis.price_volatility > 150 else "yellow" if pump_dump_analysis.price_volatility > 100 else "green"
            pd_table.add_row("Price Volatility", f"[{vol_color}]{pump_dump_analysis.price_volatility:.0f}%[/{vol_color}]")

        # Price spike
        if pump_dump_analysis.max_price_spike > 0:
            spike_color = "red" if pump_dump_analysis.max_price_spike > 200 else "yellow" if pump_dump_analysis.max_price_spike > 100 else "white"
            pd_table.add_row("Max Price Spike", f"[{spike_color}]{pump_dump_analysis.max_price_spike:.0f}%[/{spike_color}]")

        # Dump after spike
        if pump_dump_analysis.price_dump_after_spike > 0:
            dump_color = "red" if pump_dump_analysis.price_dump_after_spike > 50 else "yellow"
            pd_table.add_row("Price Drop After Spike", f"[{dump_color}]{pump_dump_analysis.price_dump_after_spike:.0f}%[/{dump_color}]")

        # Rapid changes
        if pump_dump_analysis.rapid_price_changes > 0:
            changes_color = "red" if pump_dump_analysis.rapid_price_changes > 15 else "yellow" if pump_dump_analysis.rapid_price_changes > 10 else "white"
            pd_table.add_row("Rapid Price Changes", f"[{changes_color}]{pump_dump_analysis.rapid_price_changes}[/{changes_color}]")

        # Current vs ATH
        if pump_dump_analysis.current_vs_ath_percentage < 100:
            ath_color = "red" if pump_dump_analysis.current_vs_ath_percentage < 30 else "yellow" if pump_dump_analysis.current_vs_ath_percentage < 50 else "white"
            pd_table.add_row("Current vs ATH", f"[{ath_color}]{pump_dump_analysis.current_vs_ath_percentage:.0f}%[/{ath_color}]")

        # Verdict
        if pump_dump_analysis.is_pump_dump:
            pd_table.add_row("Status", "[bold red][!!] PUMP & DUMP DETECTED[/bold red]")
        else:
            pd_table.add_row("Status", "[green][OK] No pump & dump pattern detected[/green]")

        console.print(pd_table)

        # Show pump & dump red flags
        if pump_dump_analysis.red_flags:
            console.print("")
            for flag in pump_dump_analysis.red_flags:
                console.print(f"  {flag}")

    # InsightX Distribution Metrics
    if distribution_metrics:
        console.print("\n")
        dist_table = Table(title="📊 Distribution Metrics (InsightX)", show_header=False, box=None)
        dist_table.add_column("Metric", style="cyan")
        dist_table.add_column("Value", style="white")

        # Nakamoto Coefficient
        nakamoto = distribution_metrics.get("nakamoto")
        if nakamoto is not None:
            nak_color = "red" if nakamoto < 10 else "yellow" if nakamoto < 20 else "green"
            dist_table.add_row("Nakamoto Coefficient", f"[{nak_color}]{nakamoto}[/{nak_color}]")
            dist_table.add_row("", f"[dim](Wallets needed to control 51%)[/dim]")

        # Top 10 Concentration
        top10_conc = distribution_metrics.get("top_10_holder_concentration")
        if top10_conc is not None:
            # InsightX returns already as percentage (26.41 = 26.41%), not decimal
            top10_pct = top10_conc if top10_conc > 1 else top10_conc * 100
            top10_color = "red" if top10_pct > 80 else "yellow" if top10_pct > 60 else "green"
            dist_table.add_row("Top 10 Concentration", f"[{top10_color}]{top10_pct:.1f}%[/{top10_color}]")

        # Gini Coefficient
        gini = distribution_metrics.get("gini")
        if gini is not None:
            # Note: Lower Gini = more inequality in this case (unusual)
            gini_color = "red" if gini < 0.01 else "yellow" if gini < 0.05 else "green"
            dist_table.add_row("Gini Coefficient", f"[{gini_color}]{gini:.4f}[/{gini_color}]")
            dist_table.add_row("", f"[dim](Lower = more concentrated)[/dim]")

        # HHI (Herfindahl-Hirschman Index)
        hhi = distribution_metrics.get("hhi")
        if hhi is not None:
            hhi_color = "red" if hhi > 0.8 else "yellow" if hhi > 0.5 else "green"
            dist_table.add_row("HHI Index", f"[{hhi_color}]{hhi:.4f}[/{hhi_color}]")
            dist_table.add_row("", f"[dim](>0.8 = monopoly-level concentration)[/dim]")

        console.print(dist_table)

        # Red flags for distribution
        red_flags = []
        if nakamoto and nakamoto < 10:
            red_flags.append(f"[!!] EXTREME CENTRALIZATION: Only {nakamoto} wallets control 51%")
        elif nakamoto and nakamoto < 20:
            red_flags.append(f"[!] High centralization: Only {nakamoto} wallets control 51%")

        if top10_conc:
            # Use the already-calculated top10_pct (handles both decimal and percentage formats)
            check_pct = top10_conc if top10_conc > 1 else top10_conc * 100
            if check_pct > 80:
                red_flags.append(f"[!!] TOP 10 WHALE DOMINANCE: {check_pct:.1f}% held by top 10")

        if hhi and hhi > 0.8:
            red_flags.append(f"[!!] MONOPOLY-LEVEL CONCENTRATION: HHI = {hhi:.2f}")

        if red_flags:
            console.print("")
            for flag in red_flags:
                console.print(f"  {flag}")

    # On-chain holder analysis (if available)
    if onchain_data and onchain_data.can_analyze:
        console.print("\n")
        onchain_table = Table(title="⛓️ On-Chain Holder Analysis", show_header=False, box=None)
        onchain_table.add_column("Metric", style="cyan")
        onchain_table.add_column("Value", style="white")

        # Total holders
        holders_color = "green" if onchain_data.total_holders > 200 else "yellow" if onchain_data.total_holders > 50 else "red"
        onchain_table.add_row("Total Holders", f"[{holders_color}]{onchain_data.total_holders}[/{holders_color}]")

        # Top holder
        top1_color = "red" if onchain_data.top_holder_percentage > 20 else "yellow" if onchain_data.top_holder_percentage > 10 else "green"
        onchain_table.add_row("Top Holder", f"[{top1_color}]{onchain_data.top_holder_percentage:.2f}%[/{top1_color}]")

        # Top 10
        top10_color = "red" if onchain_data.top_10_percentage > 80 else "yellow" if onchain_data.top_10_percentage > 60 else "green"
        onchain_table.add_row("Top 10 Holders", f"[{top10_color}]{onchain_data.top_10_percentage:.2f}%[/{top10_color}]")

        console.print(onchain_table)

        # Show fresh wallet count in top 10
        if onchain_data.fresh_wallet_count_top10 > 0:
            console.print("")
            fresh_color = "red" if onchain_data.fresh_wallet_count_top10 > 3 else "yellow"
            console.print(f"[{fresh_color}][!] {onchain_data.fresh_wallet_count_top10} fresh wallets (<7 days) in top 10 holders![/{fresh_color}]")

        # Show top holders
        if onchain_data.holders:
            console.print("\n")
            top_holders_table = Table(title="🔝 Top 10 Holders", show_header=True)
            top_holders_table.add_column("#", style="cyan", justify="right")
            top_holders_table.add_column("Address", style="white")
            top_holders_table.add_column("% of Supply", justify="right")
            top_holders_table.add_column("Age", justify="center")

            for i, holder in enumerate(onchain_data.holders[:10], 1):
                addr = holder["address"]
                short_addr = f"{addr[:4]}...{addr[-4:]}"
                pct = holder["percentage"]
                age = holder.get("age_days")
                is_fresh = holder.get("is_fresh", False)

                pct_color = "red" if pct > 10 else "yellow" if pct > 5 else "white"

                # Age display
                if age is not None:
                    if is_fresh:
                        age_display = f"[red]{age}d [!!][/red]"
                    elif age < 30:
                        age_display = f"[yellow]{age}d[/yellow]"
                    else:
                        age_display = f"[green]{age}d[/green]"
                else:
                    age_display = "[dim]?[/dim]"

                top_holders_table.add_row(
                    str(i),
                    short_addr,
                    f"[{pct_color}]{pct:.2f}%[/{pct_color}]",
                    age_display
                )

            console.print(top_holders_table)

    # Red Flags
    if risk_report.all_red_flags:
        console.print("\n")
        flags_panel = Panel(
            "\n".join(risk_report.all_red_flags),
            title="🚩 RED FLAGS",
            border_style="red"
        )
        console.print(flags_panel)

    # Recommendations
    console.print("\n")
    rec_panel = Panel(
        "\n".join(risk_report.recommendations),
        title="[i] RECOMMENDATIONS",
        border_style="blue"
    )
    console.print(rec_panel)

    # Summary of all rug indicators
    console.print("\n")
    summary_text = _generate_rug_summary(
        risk_report,
        liquidity_analysis,
        creator_analysis,
        social_analysis,
        wallet_analysis,
        onchain_data
    )
    summary_panel = Panel(
        summary_text,
        title="📊 RUG PULL INDICATORS SUMMARY",
        border_style="bold cyan"
    )
    console.print(summary_panel)

    console.print("\n" + "=" * 60 + "\n", style="bold")


def _generate_rug_summary(risk_report, liquidity_analysis, creator_analysis, social_analysis, wallet_analysis, onchain_data):
    """Generate a summary of all rug pull indicators"""
    lines = []

    # Overall verdict with emoji
    if risk_report.overall_risk_score >= 75:
        lines.append("[bold red][!!] EXTREME DANGER - DO NOT BUY![/bold red]")
    elif risk_report.overall_risk_score >= 50:
        lines.append("[bold red]⛔ HIGH RISK - Very Dangerous![/bold red]")
    elif risk_report.overall_risk_score >= 25:
        lines.append("[bold yellow][!] MEDIUM RISK - Be Careful![/bold yellow]")
    else:
        lines.append("[bold green][OK] LOW RISK - Relatively Safe[/bold green]")

    lines.append("")

    # Key metrics
    lines.append("[bold]Key Indicators:[/bold]")

    # Holders
    if onchain_data and onchain_data.can_analyze:
        holder_emoji = "🔴" if onchain_data.total_holders < 50 else "🟡" if onchain_data.total_holders < 200 else "🟢"
        lines.append(f"{holder_emoji} Holders: {onchain_data.total_holders}")

        top1_emoji = "🔴" if onchain_data.top_holder_percentage > 20 else "🟡" if onchain_data.top_holder_percentage > 10 else "🟢"
        lines.append(f"{top1_emoji} Top Holder: {onchain_data.top_holder_percentage:.1f}%")

        top10_emoji = "🔴" if onchain_data.top_10_percentage > 80 else "🟡" if onchain_data.top_10_percentage > 60 else "🟢"
        lines.append(f"{top10_emoji} Top 10: {onchain_data.top_10_percentage:.1f}%")
    elif wallet_analysis:
        holder_emoji = "🔴" if wallet_analysis.total_holders < 50 else "🟡" if wallet_analysis.total_holders < 200 else "🟢"
        lines.append(f"{holder_emoji} Holders: {wallet_analysis.total_holders}")

    # Liquidity
    if liquidity_analysis:
        liq_emoji = "🔴" if liquidity_analysis.liquidity_usd < 5000 else "🟡" if liquidity_analysis.liquidity_usd < 10000 else "🟢"
        lines.append(f"{liq_emoji} Liquidity: ${liquidity_analysis.liquidity_usd:,.0f}")

    # Fresh wallets
    if wallet_analysis:
        fresh_emoji = "🔴" if wallet_analysis.fresh_wallet_percentage > 50 else "🟡" if wallet_analysis.fresh_wallet_percentage > 30 else "🟢"
        lines.append(f"{fresh_emoji} Fresh Wallets: {wallet_analysis.fresh_wallet_percentage:.0f}%")

    # Creator history
    if creator_analysis and creator_analysis.total_tokens_created > 0:
        rug_emoji = "🔴" if creator_analysis.rug_percentage > 50 else "🟡" if creator_analysis.rug_percentage > 25 else "🟢"
        lines.append(f"{rug_emoji} Creator Rug Rate: {creator_analysis.rug_percentage:.0f}%")

    # Social media
    if social_analysis:
        social_count = sum([social_analysis.has_twitter, social_analysis.has_telegram, social_analysis.has_website])
        social_emoji = "🔴" if social_count == 0 else "🟡" if social_count == 1 else "🟢"
        lines.append(f"{social_emoji} Social Media: {social_count}/3 platforms")

    lines.append("")
    lines.append(f"[bold]Overall Risk Score: {risk_report.overall_risk_score}/100[/bold]")

    return "\n".join(lines)


def analyze_creator_batch(creator_address: str):
    """Analyze all tokens from a creator"""
    batch_analyzer = BatchAnalyzer()

    try:
        results = batch_analyzer.analyze_creator_batch(creator_address, console)

        if results:
            batch_analyzer.display_batch_results(results, console)
        else:
            console.print("[red]No results to display[/red]")

    finally:
        batch_analyzer.close()


def main():
    """Main entry point"""
    print_banner()

    # Check for batch mode
    if len(sys.argv) >= 3 and sys.argv[1] == "--batch":
        creator_address = sys.argv[2]
        console.print("[cyan]Running in BATCH MODE - Analyzing all tokens from creator...[/cyan]\n")

        # Validate address
        if len(creator_address) < 32 or len(creator_address) > 44:
            console.print("[red][X] Error: Invalid Solana address format[/red]")
            sys.exit(1)

        try:
            analyze_creator_batch(creator_address)
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Analysis interrupted by user[/yellow]")
            sys.exit(0)
        except Exception as e:
            console.print(f"\n[red][X] Error: {str(e)}[/red]")
            sys.exit(1)
        return

    if len(sys.argv) < 2:
        console.print("[yellow]Usage:[/yellow]")
        console.print("  Single token:  python main.py <token_mint_address>")
        console.print("  Batch mode:    python main.py --batch <creator_address>")
        console.print("\n[yellow]Examples:[/yellow]")
        console.print("  python main.py 7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr")
        console.print("  python main.py --batch Ah8zY3gfWEd1tkBAZgMKPTGSvxJbfVJJvbP8G5y3pump")
        sys.exit(1)

    mint_address = sys.argv[1]

    # Validate mint address format (basic check)
    if len(mint_address) < 32 or len(mint_address) > 44:
        console.print("[red][X] Error: Invalid Solana address format[/red]")
        sys.exit(1)

    try:
        analyze_token(mint_address)
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Analysis interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red][X] Error: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
