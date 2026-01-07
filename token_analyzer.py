"""Token holder and distribution analysis"""
import httpx
from typing import Dict, List, Optional
from dataclasses import dataclass
from config import RISK_THRESHOLDS, SOLANA_RPC_URL


@dataclass
class HolderInfo:
    """Information about a token holder"""
    address: str
    balance: float
    percentage: float


@dataclass
class DistributionAnalysis:
    """Results of token distribution analysis"""
    total_holders: int
    top_holder_percentage: float
    top_10_percentage: float
    risk_score: int  # 0-100
    red_flags: List[str]
    holders: List[HolderInfo]


class TokenAnalyzer:
    """Analyzes token holder distribution and patterns"""

    def __init__(self, rpc_url: str = SOLANA_RPC_URL):
        self.rpc_url = rpc_url
        self.client = httpx.Client(timeout=30.0)

    async def get_token_accounts(self, mint_address: str) -> List[Dict]:
        """Get all token accounts for a mint"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getProgramAccounts",
            "params": [
                "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",  # Token program
                {
                    "encoding": "jsonParsed",
                    "filters": [
                        {
                            "dataSize": 165  # Size of token account
                        },
                        {
                            "memcmp": {
                                "offset": 0,
                                "bytes": mint_address
                            }
                        }
                    ]
                }
            ]
        }

        response = self.client.post(self.rpc_url, json=payload)
        if response.status_code != 200:
            raise Exception(f"RPC error: {response.status_code}")

        data = response.json()
        return data.get("result", [])

    def analyze_distribution(
        self,
        mint_address: str,
        total_supply: float,
        creator_address: Optional[str] = None
    ) -> DistributionAnalysis:
        """Analyze token holder distribution"""

        # Get all token accounts
        accounts = self.get_token_accounts(mint_address)

        # Parse holder balances
        holders = []
        for account in accounts:
            try:
                parsed = account["account"]["data"]["parsed"]
                info = parsed["info"]
                balance = float(info["tokenAmount"]["uiAmount"])

                if balance > 0:  # Only count non-zero balances
                    percentage = (balance / total_supply) * 100
                    holders.append(HolderInfo(
                        address=info["owner"],
                        balance=balance,
                        percentage=percentage
                    ))
            except (KeyError, ValueError):
                continue

        # Sort by balance descending
        holders.sort(key=lambda x: x.balance, reverse=True)

        # Calculate metrics
        total_holders = len(holders)
        top_holder_pct = holders[0].percentage if holders else 0
        top_10_pct = sum(h.percentage for h in holders[:10])

        # Detect red flags
        red_flags = []
        risk_score = 0

        # Check whale concentration
        if top_holder_pct > RISK_THRESHOLDS["WHALE_PERCENTAGE"]:
            red_flags.append(
                f"[!] WHALE ALERT: Top holder has {top_holder_pct:.1f}% of supply"
            )
            risk_score += 30

        # Check top 10 concentration
        if top_10_pct > RISK_THRESHOLDS["TOP_10_PERCENTAGE"]:
            red_flags.append(
                f"[!] CONCENTRATED: Top 10 holders have {top_10_pct:.1f}% of supply"
            )
            risk_score += 25

        # Check number of holders
        if total_holders < RISK_THRESHOLDS["MIN_HOLDERS"]:
            red_flags.append(
                f"[!] LOW HOLDERS: Only {total_holders} holders (very suspicious)"
            )
            risk_score += 20

        # Check if creator still holds large amount
        if creator_address:
            creator_holding = next(
                (h for h in holders if h.address == creator_address),
                None
            )
            if creator_holding and creator_holding.percentage > RISK_THRESHOLDS["DEV_PERCENTAGE"]:
                red_flags.append(
                    f"[!] DEV DUMP RISK: Creator holds {creator_holding.percentage:.1f}%"
                )
                risk_score += 25

        return DistributionAnalysis(
            total_holders=total_holders,
            top_holder_percentage=top_holder_pct,
            top_10_percentage=top_10_pct,
            risk_score=min(risk_score, 100),
            red_flags=red_flags,
            holders=holders[:20]  # Return top 20 holders
        )

    def close(self):
        """Close HTTP client"""
        self.client.close()
