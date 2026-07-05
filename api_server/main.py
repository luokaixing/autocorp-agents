"""Crypto Narrative Intelligence API

A REST API that provides real-time tracking of the three mainlines of H2 2026 crypto:
- RWA (Real World Assets)
- DePIN (Decentralized Physical Infrastructure Networks)
- AI Agent (On-chain Autonomous Agents)

Designed for RapidAPI marketplace (B2B developer market).
Zero sensitive data exposure — all secrets stay in .secrets/.

Endpoints:
- GET /                    : API health + usage
- GET /narratives          : Overview of all three mainlines
- GET /narratives/{name}   : Single mainline detail
- GET /narratives/{name}/protocols : Top protocols in a mainline
- GET /trending            : Trending protocols (24h stars/TVL change)
- GET /narratives/{name}/score : Narrative heat score (AutoCorp algorithm)

License: MIT
Author: AutoCorp Research Desk
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ============================================================
# Configuration
# ============================================================

RAPIDAPI_PROXY_SECRET = os.getenv("RAPIDAPI_PROXY_SECRET", "")
RATE_LIMIT_FREE = 100       # calls/day
RATE_LIMIT_PRO = 10_000     # calls/day
RATE_LIMIT_BUSINESS = 100_000
RATE_LIMIT_ENTERPRISE = 1_000_000

# Cache TTLs (seconds)
CACHE_TTL_NARRATIVES = 300      # 5 min
CACHE_TTL_PROTOCOLS = 600       # 10 min
CACHE_TTL_TRENDING = 1800       # 30 min

# ============================================================
# Storage (simple JSON cache, no DB required for MVP)
# ============================================================

CACHE_DIR = Path("api_cache")
CACHE_DIR.mkdir(exist_ok=True)

USAGE_FILE = Path("api_usage.json")


def load_usage() -> dict:
    if USAGE_FILE.exists():
        try:
            return json.loads(USAGE_FILE.read_text())
        except Exception:
            pass
    return {"calls": {}, "by_key": {}}


def save_usage(usage: dict) -> None:
    USAGE_FILE.write_text(json.dumps(usage, indent=2))


def get_today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def check_rate_limit(rapidapi_key: Optional[str]) -> tuple[bool, dict]:
    """Check rate limit for given API key. Returns (allowed, usage_info)."""
    usage = load_usage()
    today = get_today()

    # Reset daily counters if new day
    if today not in usage["calls"]:
        usage["calls"] = {today: {}}
        usage["by_key"] = {}

    daily = usage["calls"].setdefault(today, {})

    # Identify tier by RapidAPI key prefix (simplified for MVP)
    if not rapidapi_key:
        tier = "free"
        limit = RATE_LIMIT_FREE
    elif rapidapi_key.startswith("pro_"):
        tier = "pro"
        limit = RATE_LIMIT_PRO
    elif rapidapi_key.startswith("biz_"):
        tier = "business"
        limit = RATE_LIMIT_BUSINESS
    elif rapidapi_key.startswith("ent_"):
        tier = "enterprise"
        limit = RATE_LIMIT_ENTERPRISE
    else:
        tier = "free"
        limit = RATE_LIMIT_FREE

    calls_today = daily.get(rapidapi_key or "anonymous", 0)

    if calls_today >= limit:
        return False, {
            "tier": tier,
            "limit": limit,
            "used": calls_today,
            "remaining": 0,
            "reset_at": f"{today} 23:59:59 UTC",
        }

    # Increment
    daily[rapidapi_key or "anonymous"] = calls_today + 1
    usage["by_key"][rapidapi_key or "anonymous"] = {"tier": tier, "total_calls": sum(
        v.get(rapidapi_key or "anonymous", 0) for v in usage["calls"].values()
    )}
    save_usage(usage)

    return True, {
        "tier": tier,
        "limit": limit,
        "used": calls_today + 1,
        "remaining": limit - calls_today - 1,
        "reset_at": f"{today} 23:59:59 UTC",
    }


# ============================================================
# Data Providers (real implementations calling public APIs)
# ============================================================

class GitHubProvider:
    """Fetch GitHub repo stats via public API (no token required for low volume)."""

    BASE_URL = "https://api.github.com"

    @staticmethod
    async def get_repo_stats(owner: str, repo: str) -> dict:
        """Get stars, forks, watchers, open issues for a repo."""
        cache_key = f"github_{owner}_{repo}.json"
        cache_file = CACHE_DIR / cache_key
        if cache_file.exists():
            age = time.time() - cache_file.stat().st_mtime
            if age < CACHE_TTL_PROTOCOLS:
                return json.loads(cache_file.read_text())

        url = f"{GitHubProvider.BASE_URL}/repos/{owner}/{repo}"
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.get(url, headers={"Accept": "application/vnd.github.v3+json"})
                if resp.status_code != 200:
                    return {"error": f"GitHub API {resp.status_code}", "owner": owner, "repo": repo}
                data = resp.json()
                result = {
                    "owner": owner,
                    "repo": repo,
                    "stars": data.get("stargazers_count", 0),
                    "forks": data.get("forks_count", 0),
                    "watchers": data.get("subscribers_count", 0),
                    "open_issues": data.get("open_issues_count", 0),
                    "language": data.get("language"),
                    "updated_at": data.get("updated_at"),
                    "description": data.get("description"),
                }
                cache_file.write_text(json.dumps(result))
                return result
            except Exception as e:
                return {"error": str(e), "owner": owner, "repo": repo}


class DefiLlamaProvider:
    """Fetch TVL data via DefiLlama public API (no key required)."""

    BASE_URL = "https://api.llama.fi"

    @staticmethod
    async def get_protocol_tvl(protocol_slug: str) -> dict:
        """Get current TVL for a protocol."""
        cache_file = CACHE_DIR / f"defillama_{protocol_slug}.json"
        if cache_file.exists():
            age = time.time() - cache_file.stat().st_mtime
            if age < CACHE_TTL_PROTOCOLS:
                return json.loads(cache_file.read_text())

        url = f"{DefiLlamaProvider.BASE_URL}/protocol/{protocol_slug}"
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return {"error": f"DefiLlama {resp.status_code}", "slug": protocol_slug}
                data = resp.json()
                tvl_history = data.get("tvl", [])
                current_tvl = tvl_history[-1] if tvl_history else {}
                result = {
                    "name": data.get("name"),
                    "slug": protocol_slug,
                    "category": data.get("category"),
                    "chain": data.get("chain"),
                    "current_tvl_usd": current_tvl.get("totalLiquidityUSD", 0),
                    "tvl_24h_ago": tvl_history[-2].get("totalLiquidityUSD", 0) if len(tvl_history) >= 2 else 0,
                    "change_24h_pct": (
                        (current_tvl.get("totalLiquidityUSD", 0) - tvl_history[-2].get("totalLiquidityUSD", 0))
                        / tvl_history[-2].get("totalLiquidityUSD", 1) * 100
                    ) if len(tvl_history) >= 2 and tvl_history[-2].get("totalLiquidityUSD", 0) > 0 else 0,
                    "description": data.get("description"),
                    "url": data.get("url"),
                    "twitter": data.get("twitter"),
                }
                cache_file.write_text(json.dumps(result))
                return result
            except Exception as e:
                return {"error": str(e), "slug": protocol_slug}


# ============================================================
# Narrative Definitions
# ============================================================

NARRATIVES = {
    "rwa": {
        "name": "RWA",
        "full_name": "Real World Assets",
        "description": "Tokenized real-world assets: Treasuries, private credit, real estate",
        "key_driver": "TradFi on-chain adoption",
        "protocols": [
            {"slug": "ondo-finance", "github": None, "name": "Ondo Finance", "defillama": "ondo-finance"},
            {"slug": "blackrock-buidl", "github": None, "name": "BlackRock BUIDL", "defillama": "buidl"},
            {"slug": "centrifuge", "github": "centrifuge", "name": "Centrifuge", "defillama": "centrifuge"},
            {"slug": "maple", "github": "maple-labs/maple-core", "name": "Maple Finance", "defillama": "maple"},
            {"slug": "makerdao", "github": "makerdao/dss", "name": "MakerDAO", "defillama": "makerdao"},
        ],
    },
    "depin": {
        "name": "DePIN",
        "full_name": "Decentralized Physical Infrastructure Networks",
        "description": "Networks where supply side is physical hardware (GPUs, hotspots, storage)",
        "key_driver": "AI compute shortage",
        "protocols": [
            {"slug": "render", "github": "Render-Project/render", "name": "Render Network", "defillama": "render"},
            {"slug": "akash", "github": "ovrclk/akash", "name": "Akash Network", "defillama": "akash"},
            {"slug": "filecoin", "github": "filecoin-project/lotus", "name": "Filecoin", "defillama": "filecoin"},
            {"slug": "helium", "github": "helium/plumber", "name": "Helium", "defillama": "helium"},
            {"slug": "io-net", "github": None, "name": "io.net", "defillama": "io-net"},
        ],
    },
    "ai-agent": {
        "name": "AI Agent",
        "full_name": "On-chain Autonomous Agents",
        "description": "AI Agent infrastructure, frameworks, and on-chain applications",
        "key_driver": "2026 Agent元年 + OpenClaw 26万 Stars",
        "protocols": [
            {"slug": "bittensor", "github": "opentensor/BitTensor", "name": "Bittensor (TAO)", "defillama": "bittensor"},
            {"slug": "ritual", "github": "ritual-network/infernet", "name": "Ritual", "defillama": None},
            {"slug": "autonolas", "github": "valory-xyz/mech", "name": "Autonolas", "defillama": "autonolas"},
            {"slug": "oraichain", "github": None, "name": "Oraichain", "defillama": "oraichain"},
            {"slug": "phala", "github": "Phala-Network/phala-blockchain", "name": "Phala Network", "defillama": "phala"},
        ],
    },
}


def calculate_narrative_score(github_data: dict, tvl_data: dict) -> float:
    """AutoCorp's proprietary narrative heat score (0-100).

    Combines:
    - GitHub stars (40%): developer mindshare
    - TVL (30%): capital commitment
    - TVL 24h change (20%): momentum
    - Open issues (10%): active development
    """
    score = 0

    # GitHub stars (log scale)
    stars = github_data.get("stars", 0) if not github_data.get("error") else 0
    if stars > 0:
        import math
        score += min(40, math.log10(stars) * 8)  # 10 stars=8, 100=16, 1k=24, 10k=32, 100k=40

    # TVL (log scale)
    tvl = tvl_data.get("current_tvl_usd", 0) if not tvl_data.get("error") else 0
    if tvl > 0:
        import math
        score += min(30, math.log10(tvl) * 3)  # $1M=18, $10M=21, $100M=24, $1B=27, $10B=30

    # TVL 24h momentum
    change_24h = tvl_data.get("change_24h_pct", 0) if not tvl_data.get("error") else 0
    score += min(20, max(-20, change_24h * 2))

    # Open issues (proxy for active development)
    issues = github_data.get("open_issues", 0) if not github_data.get("error") else 0
    if issues > 0:
        import math
        score += min(10, math.log10(issues + 1) * 3)

    return round(max(0, min(100, score)), 2)


# ============================================================
# FastAPI App
# ============================================================

app = FastAPI(
    title="Crypto Narrative Intelligence API",
    description="Real-time tracking of RWA, DePIN, and AI Agent crypto narratives.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ============================================================
# Auth & Rate Limit Dependency
# ============================================================

async def verify_rapidapi(
    request: Request,
    x_rapidapi_proxy_secret: Optional[str] = Header(None, alias="X-RapidAPI-Proxy-Secret"),
    x_rapidapi_key: Optional[str] = Header(None, alias="X-RapidAPI-Key"),
):
    """Verify RapidAPI proxy secret and enforce rate limits.

    For local dev, RAPIDAPI_PROXY_SECRET env var can be empty (no auth).
    On RapidAPI, the proxy secret is automatically injected.
    """
    # If env var is set, require matching secret (RapidAPI production)
    if RAPIDAPI_PROXY_SECRET:
        if x_rapidapi_proxy_secret != RAPIDAPI_PROXY_SECRET:
            raise HTTPException(status_code=403, detail="Invalid RapidAPI proxy secret")

    # Rate limit check
    allowed, usage_info = check_rate_limit(x_rapidapi_key)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "usage": usage_info,
                "upgrade_url": "https://rapidapi.com/autocorp/api/crypto-narrative-intelligence",
            },
        )

    # Store usage in request state for response headers
    request.state.usage = usage_info
    return usage_info


# ============================================================
# Response Models
# ============================================================

class NarrativeOverview(BaseModel):
    slug: str
    name: str
    full_name: str
    description: str
    key_driver: str
    protocol_count: int


class ProtocolStats(BaseModel):
    slug: str
    name: str
    github: Optional[dict]
    defillama: Optional[dict]
    narrative_score: float


class TrendingProtocol(BaseModel):
    slug: str
    name: str
    narrative: str
    narrative_score: float
    tvl_change_24h_pct: Optional[float]
    stars: Optional[int]


# ============================================================
# Endpoints
# ============================================================

@app.get("/", dependencies=[Depends(verify_rapidapi)])
async def root():
    """API health + usage."""
    return {
        "name": "Crypto Narrative Intelligence API",
        "version": "0.1.0",
        "provider": "AutoCorp Research Desk",
        "narratives_tracked": list(NARRATIVES.keys()),
        "endpoints": [
            "GET /narratives - All narratives overview",
            "GET /narratives/{slug} - Single narrative detail",
            "GET /narratives/{slug}/protocols - Top protocols in a narrative",
            "GET /narratives/{slug}/score - Narrative heat score",
            "GET /trending - Trending protocols across all narratives",
        ],
        "rate_limits": {
            "free": f"{RATE_LIMIT_FREE}/day",
            "pro": f"{RATE_LIMIT_PRO}/day",
            "business": f"{RATE_LIMIT_BUSINESS}/day",
            "enterprise": f"{RATE_LIMIT_ENTERPRISE}/day",
        },
        "documentation": "https://rapidapi.com/autocorp/api/crypto-narrative-intelligence",
    }


@app.get("/narratives", dependencies=[Depends(verify_rapidapi)])
async def list_narratives():
    """Overview of all three mainlines."""
    result = []
    for slug, data in NARRATIVES.items():
        result.append(NarrativeOverview(
            slug=slug,
            name=data["name"],
            full_name=data["full_name"],
            description=data["description"],
            key_driver=data["key_driver"],
            protocol_count=len(data["protocols"]),
        ))
    return {
        "narratives": result,
        "updated_at": datetime.now().isoformat(),
        "source": "AutoCorp Research Desk",
    }


@app.get("/narratives/{slug}", dependencies=[Depends(verify_rapidapi)])
async def get_narrative(slug: str):
    """Single narrative detail."""
    if slug not in NARRATIVES:
        raise HTTPException(status_code=404, detail=f"Narrative '{slug}' not found. Available: {list(NARRATIVES.keys())}")

    data = NARRATIVES[slug]
    return {
        "slug": slug,
        "name": data["name"],
        "full_name": data["full_name"],
        "description": data["description"],
        "key_driver": data["key_driver"],
        "protocols": [{"slug": p["slug"], "name": p["name"]} for p in data["protocols"]],
        "updated_at": datetime.now().isoformat(),
    }


async def _fetch_proto_data(proto: dict) -> tuple[dict, dict]:
    """Helper: fetch GitHub + DefiLlama data for a protocol, with safe error handling."""
    github_data = {}
    tvl_data = {}

    if proto.get("github") and "/" in proto["github"]:
        try:
            owner, repo = proto["github"].split("/", 1)
            github_data = await GitHubProvider.get_repo_stats(owner, repo)
        except Exception as e:
            github_data = {"error": str(e)}

    if proto.get("defillama"):
        try:
            tvl_data = await DefiLlamaProvider.get_protocol_tvl(proto["defillama"])
        except Exception as e:
            tvl_data = {"error": str(e)}

    return github_data, tvl_data


@app.get("/narratives/{slug}/protocols", dependencies=[Depends(verify_rapidapi)])
async def get_narrative_protocols(slug: str):
    """Top protocols in a narrative with GitHub + TVL data."""
    if slug not in NARRATIVES:
        raise HTTPException(status_code=404, detail=f"Narrative '{slug}' not found")

    data = NARRATIVES[slug]
    protocols_result = []

    for proto in data["protocols"]:
        github_data, tvl_data = await _fetch_proto_data(proto)
        score = calculate_narrative_score(github_data, tvl_data)

        protocols_result.append({
            "slug": proto["slug"],
            "name": proto["name"],
            "github": github_data,
            "tvl": tvl_data,
            "narrative_score": score,
        })

    protocols_result.sort(key=lambda x: x["narrative_score"], reverse=True)

    return {
        "narrative": slug,
        "protocols": protocols_result,
        "count": len(protocols_result),
        "updated_at": datetime.now().isoformat(),
    }


@app.get("/narratives/{slug}/score", dependencies=[Depends(verify_rapidapi)])
async def get_narrative_score(slug: str):
    """Narrative heat score (0-100) using AutoCorp's proprietary algorithm."""
    if slug not in NARRATIVES:
        raise HTTPException(status_code=404, detail=f"Narrative '{slug}' not found")

    data = NARRATIVES[slug]
    total_score = 0
    protocol_scores = []

    for proto in data["protocols"]:
        github_data, tvl_data = await _fetch_proto_data(proto)
        score = calculate_narrative_score(github_data, tvl_data)
        protocol_scores.append({"slug": proto["slug"], "name": proto["name"], "score": score})
        total_score += score

    avg_score = round(total_score / len(data["protocols"]), 2) if data["protocols"] else 0

    return {
        "narrative": slug,
        "name": data["name"],
        "overall_score": avg_score,
        "interpretation": (
            "Very Hot" if avg_score >= 70 else
            "Hot" if avg_score >= 50 else
            "Warm" if avg_score >= 30 else
            "Cold"
        ),
        "protocol_scores": protocol_scores,
        "updated_at": datetime.now().isoformat(),
        "algorithm": "AutoCorp Narrative Heat Score v1.0 (GitHub 40% + TVL 30% + Momentum 20% + Activity 10%)",
    }


@app.get("/trending", dependencies=[Depends(verify_rapidapi)])
async def get_trending(limit: int = 10):
    """Trending protocols across all narratives (sorted by narrative score)."""
    all_protocols = []

    for narrative_slug, data in NARRATIVES.items():
        for proto in data["protocols"]:
            github_data, tvl_data = await _fetch_proto_data(proto)
            score = calculate_narrative_score(github_data, tvl_data)

            all_protocols.append({
                "slug": proto["slug"],
                "name": proto["name"],
                "narrative": narrative_slug,
                "narrative_score": score,
                "tvl_change_24h_pct": tvl_data.get("change_24h_pct") if not tvl_data.get("error") else None,
                "stars": github_data.get("stars") if not github_data.get("error") else None,
                "current_tvl_usd": tvl_data.get("current_tvl_usd") if not tvl_data.get("error") else None,
            })

    all_protocols.sort(key=lambda x: x["narrative_score"], reverse=True)
    return {
        "trending": all_protocols[:limit],
        "count": len(all_protocols[:limit]),
        "updated_at": datetime.now().isoformat(),
    }


# ============================================================
# Health check (no auth)
# ============================================================

@app.get("/health")
async def health():
    """Health check (no rate limit)."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ============================================================
# Main entry (for local dev)
# ============================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
