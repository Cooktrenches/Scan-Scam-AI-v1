from liquidity_analyzer import LiquidityAnalyzer

la = LiquidityAnalyzer()
data = la.get_token_data('4Myt94CWcAWT4t4Uy4ZgCzRLFvNw26XcyBVa9jEjpump')

print(f"Volume 24h: ${data.get('volume_24h', 0):,.2f}")
print(f"Market Cap: ${data.get('usd_market_cap', 0):,.2f}")
print(f"Liquidity: ${data.get('liquidity', 0):,.2f}")

la.close()
