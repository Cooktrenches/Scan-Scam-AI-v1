"""
Batch analyze all tokens from a creator
"""
import httpx
from typing import List, Dict
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn


@dataclass
class BatchResult:
    """Result for one token in batch"""
    mint: str
    name: str
    symbol: str
    market_cap: float
    risk_score: int
    is_rugged: bool
    red_flags_count: int


class BatchAnalyzer:
    """Analyze all tokens created by a wallet"""

    def __init__(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://pump.fun/'
        }
        self.client = httpx.Client(timeout=60.0, headers=headers, follow_redirects=True)

    def get_creator_tokens(self, creator_address: str) -> List[Dict]:
        """Get all tokens created by a wallet"""
        try:
            url = f"https://frontend-api.pump.fun/coins/user-created-coins/{creator_address}"
            response = self.client.get(url, timeout=15.0)

            if response.status_code == 200:
                return response.json()

            return []

        except Exception:
            return []

    def analyze_creator_batch(self, creator_address: str, console: Console) -> List[BatchResult]:
        """Analyze all tokens from a creator"""

        console.print(f"\n[cyan]Fetching all tokens from creator {creator_address[:8]}...[/cyan]")

        tokens = self.get_creator_tokens(creator_address)

        if not tokens:
            console.print("[red]No tokens found for this creator[/red]")
            return []

        console.print(f"[green]Found {len(tokens)} tokens! Analyzing...[/green]\n")

        results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            task = progress.add_task(f"Analyzing {len(tokens)} tokens...", total=len(tokens))

            for token in tokens:
                mint = token.get("mint", "")
                name = token.get("name", "Unknown")
                symbol = token.get("symbol", "???")
                market_cap = token.get("usd_market_cap", 0)

                # Quick risk assessment
                is_rugged = market_cap < 100  # Less than $100 = likely rugged
                risk_score = 0
                red_flags = 0

                # Dead token
                if market_cap < 100:
                    risk_score = 100
                    red_flags += 3
                elif market_cap < 1000:
                    risk_score = 75
                    red_flags += 2

                # Check if still has liquidity
                liquidity = token.get("liquidity", 0)
                if liquidity < 100:
                    risk_score = max(risk_score, 90)
                    red_flags += 1

                results.append(BatchResult(
                    mint=mint,
                    name=name,
                    symbol=symbol,
                    market_cap=market_cap,
                    risk_score=risk_score,
                    is_rugged=is_rugged,
                    red_flags_count=red_flags
                ))

                progress.update(task, advance=1)

        return results

    def display_batch_results(self, results: List[BatchResult], console: Console):
        """Display batch analysis results"""

        # Summary
        total = len(results)
        rugged = sum(1 for r in results if r.is_rugged)
        active = total - rugged
        rug_percentage = (rugged / total * 100) if total > 0 else 0

        console.print("\n")
        console.print("=" * 60, style="bold")
        console.print(f"\n[bold cyan]📊 BATCH ANALYSIS SUMMARY[/bold cyan]\n")

        summary_table = Table(show_header=False, box=None)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="white")

        summary_table.add_row("Total Tokens Created", str(total))
        summary_table.add_row("Active Tokens", f"[green]{active}[/green]")
        summary_table.add_row("Rugged Tokens", f"[red]{rugged}[/red]")

        rug_color = "red" if rug_percentage > 50 else "yellow" if rug_percentage > 25 else "green"
        summary_table.add_row("Rug Percentage", f"[{rug_color}]{rug_percentage:.1f}%[/{rug_color}]")

        console.print(summary_table)

        # Verdict
        console.print("\n")
        if rug_percentage > 75:
            console.print("[bold red][!!] SERIAL RUGGER - AVOID AT ALL COSTS![/bold red]")
        elif rug_percentage > 50:
            console.print("[bold red]⛔ KNOWN RUGGER - Very Dangerous![/bold red]")
        elif rug_percentage > 25:
            console.print("[bold yellow][!] SUSPICIOUS - Many failed tokens[/bold yellow]")
        else:
            console.print("[bold green][OK] Relatively Clean History[/bold green]")

        # Detailed table
        console.print("\n")
        detail_table = Table(title="📋 All Tokens", show_header=True)
        detail_table.add_column("#", style="cyan", justify="right")
        detail_table.add_column("Name", style="white")
        detail_table.add_column("Symbol", style="white")
        detail_table.add_column("Market Cap", justify="right")
        detail_table.add_column("Status", justify="center")

        for i, result in enumerate(results, 1):
            mcap_str = f"${result.market_cap:,.0f}" if result.market_cap > 0 else "$0"

            if result.is_rugged:
                status = "[red]💀 RUGGED[/red]"
                mcap_color = "red"
            elif result.market_cap < 5000:
                status = "[yellow][!] Dying[/yellow]"
                mcap_color = "yellow"
            else:
                status = "[green][OK] Active[/green]"
                mcap_color = "green"

            detail_table.add_row(
                str(i),
                result.name[:20],
                result.symbol[:10],
                f"[{mcap_color}]{mcap_str}[/{mcap_color}]",
                status
            )

        console.print(detail_table)
        console.print("\n" + "=" * 60, style="bold")

    def close(self):
        """Close HTTP client"""
        self.client.close()
