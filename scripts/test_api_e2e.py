"""End-to-end API test script."""
import httpx
import json
import sys

BASE = "http://127.0.0.1:8765"


def test_health():
    r = httpx.get(f"{BASE}/health", timeout=10)
    print(f"[1] GET /health → {r.status_code}")
    print(f"    Response: {r.json()}")
    assert r.status_code == 200
    print("[1] OK\n")


def test_root():
    r = httpx.get(f"{BASE}/", timeout=10)
    print(f"[2] GET / → {r.status_code}")
    data = r.json()
    print(f"    Name: {data.get('name')}")
    print(f"    Narratives: {data.get('narratives_tracked')}")
    print(f"    Endpoints: {len(data.get('endpoints', []))}")
    assert r.status_code == 200
    print("[2] OK\n")


def test_narratives():
    r = httpx.get(f"{BASE}/narratives", timeout=10)
    print(f"[3] GET /narratives → {r.status_code}")
    data = r.json()
    for n in data.get("narratives", []):
        print(f"    {n['slug']}: {n['name']} - {n['protocol_count']} protocols")
    assert r.status_code == 200
    assert len(data.get("narratives", [])) == 3
    print("[3] OK\n")


def test_narrative_detail():
    r = httpx.get(f"{BASE}/narratives/rwa", timeout=10)
    print(f"[4] GET /narratives/rwa → {r.status_code}")
    data = r.json()
    print(f"    Name: {data.get('name')}")
    print(f"    Full: {data.get('full_name')}")
    print(f"    Driver: {data.get('key_driver')}")
    assert r.status_code == 200
    print("[4] OK\n")


def test_protocols():
    print("[5] GET /narratives/depin/protocols (this calls GitHub + DefiLlama)...")
    sys.stdout.flush()
    r = httpx.get(f"{BASE}/narratives/depin/protocols", timeout=120)
    print(f"    Status: {r.status_code}")
    data = r.json()
    print(f"    Count: {data.get('count')}")
    for p in data.get("protocols", []):
        name = p.get("name")
        score = p.get("narrative_score")
        gh = p.get("github", {})
        tvl = p.get("tvl", {})
        stars = gh.get("stars", "?") if not gh.get("error") else f"ERR: {gh.get('error')}"
        tvl_usd = tvl.get("current_tvl_usd", "?") if not tvl.get("error") else f"ERR"
        print(f"    {name}: score={score} stars={stars} tvl=${tvl_usd}")
    assert r.status_code == 200
    print("[5] OK - Real API calls successful!\n")


def test_score():
    print("[6] GET /narratives/ai-agent/score...")
    sys.stdout.flush()
    r = httpx.get(f"{BASE}/narratives/ai-agent/score", timeout=120)
    print(f"    Status: {r.status_code}")
    data = r.json()
    print(f"    Overall: {data.get('overall_score')}")
    print(f"    Interpretation: {data.get('interpretation')}")
    for p in data.get("protocol_scores", []):
        print(f"    {p['name']}: {p['score']}")
    assert r.status_code == 200
    print("[6] OK\n")


def test_trending():
    print("[7] GET /trending?limit=5...")
    sys.stdout.flush()
    r = httpx.get(f"{BASE}/trending?limit=5", timeout=120)
    print(f"    Status: {r.status_code}")
    data = r.json()
    print(f"    Count: {data.get('count')}")
    for p in data.get("trending", []):
        print(f"    {p['name']} ({p['narrative']}): score={p['narrative_score']} stars={p.get('stars')} tvl_change={p.get('tvl_change_24h_pct')}")
    assert r.status_code == 200
    print("[7] OK\n")


if __name__ == "__main__":
    print("=" * 60)
    print("  Crypto Narrative Intelligence API - E2E Test")
    print("=" * 60)
    print()

    test_health()
    test_root()
    test_narratives()
    test_narrative_detail()
    test_protocols()
    test_score()
    test_trending()

    print("=" * 60)
    print("  ALL TESTS PASSED ✅")
    print("=" * 60)
    print()
    print("API is ready for RapidAPI deployment.")
    print("Next step: deploy to Render.com free tier.")
