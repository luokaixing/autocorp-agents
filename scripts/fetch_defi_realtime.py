"""
Fetch real-time DeFi yield data from multiple sources for article writing.
Sources:
1. Aave V3 API (direct contract data via defillama)
2. CoinGecko API (token prices)
3. DefiLlama API (TVL data)
"""
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

HEADERS = {"User-Agent": "AutoCorp-Research/1.0"}

def fetch_json(url, timeout=15):
    """Fetch JSON from URL with error handling."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"  [WARN] Failed to fetch {url[:80]}...: {e}")
        return None

def fetch_coingecko_ping():
    """Test CoinGecko API connectivity."""
    print("\n[1] Testing CoinGecko API...")
    data = fetch_json("https://api.coingecko.com/api/v3/ping")
    if data:
        print(f"  Status: {data.get('gecko_says', 'OK')}")
        return True
    return False

def fetch_defillama_protocols():
    """Fetch DeFi protocol TVL data from DefiLlama (no API key needed)."""
    print("\n[2] Fetching DeFi protocols TVL from DefiLlama...")
    data = fetch_json("https://api.llama.fi/protocols")
    if not data:
        return None
    # Filter lending protocols (handle null TVL)
    lending = [p for p in data if p.get('category') == 'Lending']
    for p in lending:
        if p.get('tvl') is None:
            p['tvl'] = 0
    lending_sorted = sorted(lending, key=lambda x: x.get('tvl', 0), reverse=True)[:10]
    print(f"  Found {len(data)} total protocols, {len(lending)} lending protocols")
    print(f"  Top 5 lending by TVL:")
    for p in lending_sorted[:5]:
        print(f"    - {p.get('name')}: ${p.get('tvl', 0)/1e9:.2f}B TVL ({p.get('chain', 'multi')})")
    return lending_sorted

def fetch_defillama_chains():
    """Fetch chain TVL data."""
    print("\n[3] Fetching chain TVL from DefiLlama...")
    data = fetch_json("https://api.llama.fi/v2/chains")
    if not data:
        return None
    # Handle null TVL
    for c in data:
        if c.get('tvl') is None:
            c['tvl'] = 0
    # Top 10 chains by TVL
    chains_sorted = sorted(data, key=lambda x: x.get('tvl', 0), reverse=True)[:10]
    print(f"  Top 5 chains by TVL:")
    for c in chains_sorted[:5]:
        print(f"    - {c.get('name')}: ${c.get('tvl', 0)/1e9:.2f}B TVL")
    return chains_sorted

def fetch_aave_pools():
    """Fetch Aave V3 pool data via DefiLlama yields endpoint."""
    print("\n[4] Fetching Aave yield pools from DefiLlama Yields...")
    data = fetch_json("https://yields.llama.fi/pools")
    if not data:
        return None
    # Filter Aave pools
    aave_pools = [p for p in data.get('data', []) if 'aave' in p.get('project', '').lower()]
    print(f"  Found {len(aave_pools)} Aave pools")
    # Handle null APY
    for p in aave_pools:
        if p.get('apy') is None:
            p['apy'] = 0
        if p.get('tvlUsd') is None:
            p['tvlUsd'] = 0
    # Top 15 by APY
    aave_sorted = sorted(aave_pools, key=lambda x: x.get('apy', 0), reverse=True)[:15]
    print(f"  Top 10 Aave pools by APY:")
    for p in aave_sorted[:10]:
        symbol = p.get('symbol', '?')
        apy = p.get('apy', 0)
        tvl_usd = p.get('tvlUsd', 0)
        chain = p.get('chain', '?')
        print(f"    - {symbol} on {chain}: APY={apy:.2f}%, TVL=${tvl_usd/1e6:.2f}M")
    return aave_sorted

def fetch_compound_pools(aave_pools):
    """Fetch Compound V3 pools for comparison."""
    print("\n[5] Fetching Compound pools from DefiLlama Yields...")
    data = fetch_json("https://yields.llama.fi/pools")
    if not data:
        return None
    compound_pools = [p for p in data.get('data', []) if 'compound' in p.get('project', '').lower()]
    print(f"  Found {len(compound_pools)} Compound pools")
    # Handle null APY
    for p in compound_pools:
        if p.get('apy') is None:
            p['apy'] = 0
        if p.get('tvlUsd') is None:
            p['tvlUsd'] = 0
    # Top 10 by APY
    compound_sorted = sorted(compound_pools, key=lambda x: x.get('apy', 0), reverse=True)[:10]
    print(f"  Top 10 Compound pools by APY:")
    for p in compound_sorted[:10]:
        symbol = p.get('symbol', '?')
        apy = p.get('apy', 0)
        tvl_usd = p.get('tvlUsd', 0)
        chain = p.get('chain', '?')
        print(f"    - {symbol} on {chain}: APY={apy:.2f}%, TVL=${tvl_usd/1e6:.2f}M")
    return compound_sorted

def fetch_token_prices():
    """Fetch current prices of key tokens."""
    print("\n[6] Fetching token prices from CoinGecko...")
    ids = 'aave,ethereum,usd-coin,tether,wrapped-steth,dai,bitcoin'
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"
    data = fetch_json(url)
    if not data:
        return None
    print(f"  Token prices (USD):")
    for token_id, info in data.items():
        price = info.get('usd', 0)
        change = info.get('usd_24h_change', 0)
        mcap = info.get('usd_market_cap', 0)
        print(f"    - {token_id}: ${price:,.2f} (24h: {change:+.2f}%), MCap: ${mcap/1e9:.2f}B")
    return data

def main():
    print(f"=== AutoCorp Real-time DeFi Data Fetcher ===")
    print(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")

    coingecko_ok = fetch_coingecko_ping()

    protocols = fetch_defillama_protocols()

    chains = fetch_defillama_chains()

    aave_pools = fetch_aave_pools()

    compound_pools = fetch_compound_pools(aave_pools)

    prices = fetch_token_prices()

    # Save all data to a single JSON file for the article writer
    snapshot = {
        "fetch_time_utc": datetime.now(timezone.utc).isoformat(),
        "coingecko_available": coingecko_ok,
        "top_lending_protocols": protocols,
        "top_chains": chains,
        "aave_top_pools": aave_pools,
        "compound_top_pools": compound_pools,
        "token_prices": prices,
    }

    output_path = "d:\\autoCompany\\company\\knowledge\\market-research\\defi-yield-snapshot-2026-06-30.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n[OK] Snapshot saved to: {output_path}")
    print(f"[OK] File size: {__import__('os').path.getsize(output_path)//1024} KB")

if __name__ == "__main__":
    main()
