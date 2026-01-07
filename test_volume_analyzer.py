from liquidity_analyzer import LiquidityAnalyzer
from volume_analyzer import VolumeAnalyzer

la = LiquidityAnalyzer()
token_data = la.get_token_data('4Myt94CWcAWT4t4Uy4ZgCzRLFvNw26XcyBVa9jEjpump')

print("Token data keys:", token_data.keys())
print(f"volume_24h in token_data: {token_data.get('volume_24h')}")

va = VolumeAnalyzer()
volume_analysis = va.analyze_volume(token_data, 0)

print(f"\nVolume Analysis:")
print(f"  volume_24h: ${volume_analysis.volume_24h:,.2f}")
print(f"  market_cap: ${volume_analysis.market_cap:,.2f}")
print(f"  volume_to_mcap_ratio: {volume_analysis.volume_to_mcap_ratio:.2f}x")
print(f"  is_wash_trading: {volume_analysis.is_wash_trading}")
print(f"  risk_score: {volume_analysis.risk_score}")
print(f"  red_flags: {volume_analysis.red_flags}")

la.close()
