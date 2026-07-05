# Crypto Narrative Intelligence API

> A REST API providing real-time tracking of the three mainlines of H2 2026 crypto: **RWA**, **DePIN**, and **AI Agent**.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why This API?

The crypto market in 2026 has fragmented into dozens of narratives. Developers building wallets, DApps, dashboards, and analytics tools need a single API to get:

- **Protocol TVL** (from DefiLlama, no API key required)
- **GitHub activity** (stars, forks, open issues)
- **Narrative heat score** (AutoCorp's proprietary 0-100 algorithm)
- **Trending protocols** (cross-narrative ranking)

Three narratives covered:

| Narrative | Protocols Tracked |
|-----------|------------------|
| **RWA** (Real World Assets) | Ondo, BUIDL, Centrifuge, Maple, MakerDAO |
| **DePIN** (Decentralized Physical Infrastructure) | Render, Akash, Filecoin, Helium, io.net |
| **AI Agent** (On-chain Autonomous Agents) | Bittensor, Ritual, Autonolas, Oraichain, Phala |

## Quick Start

### Local Development

```bash
# Install dependencies
pip install fastapi uvicorn httpx pydantic

# Run the server
python api_server/main.py

# Or with uvicorn directly
uvicorn api_server.main:app --reload --port 8000
```

### Test the Endpoints

```bash
# Health check (no auth)
curl http://localhost:8000/health

# API overview (requires RapidAPI proxy secret in production)
curl http://localhost:8000/

# List all narratives
curl http://localhost:8000/narratives

# Get RWA narrative detail
curl http://localhost:8000/narratives/rwa

# Get RWA protocols with TVL + GitHub data
curl http://localhost:8000/narratives/rwa/protocols

# Get narrative heat score
curl http://localhost:8000/narratives/rwa/score

# Get trending protocols (top 10)
curl http://localhost:8000/trending?limit=10
```

## API Endpoints

| Endpoint | Description | Rate Limit (Free) |
|----------|-------------|-------------------|
| `GET /` | API health + usage | 100/day |
| `GET /narratives` | All narratives overview | 100/day |
| `GET /narratives/{slug}` | Single narrative detail | 100/day |
| `GET /narratives/{slug}/protocols` | Top protocols + TVL + GitHub | 100/day |
| `GET /narratives/{slug}/score` | Narrative heat score (0-100) | 100/day |
| `GET /trending` | Trending protocols (cross-narrative) | 100/day |
| `GET /health` | Health check (no auth) | Unlimited |

## Narrative Heat Score Algorithm

The proprietary AutoCorp algorithm combines 4 signals into a 0-100 score:

| Signal | Weight | Source | What It Measures |
|--------|--------|--------|------------------|
| GitHub Stars | 40% | GitHub API | Developer mindshare |
| TVL | 30% | DefiLlama | Capital commitment |
| TVL 24h Change | 20% | DefiLlama | Momentum |
| Open Issues | 10% | GitHub API | Active development |

Score interpretation:
- **70-100**: Very Hot (breakout narrative)
- **50-69**: Hot (sustained interest)
- **30-49**: Warm (steady but not breakout)
- **0-29**: Cold (declining or early-stage)

## Pricing (on RapidAPI)

| Tier | Price | Calls/Day | Webhooks | Support |
|------|-------|-----------|----------|--------|
| Free | $0 | 100 | ❌ | Community |
| Pro | $29/month | 10,000 | ❌ | Email |
| Business | $99/month | 100,000 | ✅ | Priority Email |
| Enterprise | $299/month | Unlimited | ✅ | Slack + SLA |

## Data Sources

All data sources are public and require no API keys:

- **GitHub API**: Stars, forks, watchers, open issues (60 req/hour without token)
- **DefiLlama API**: TVL, protocol metadata, historical data
- **CoinGecko API**: Price data (planned for v0.2)

No sensitive data is stored in this repository. All API secrets are managed via environment variables.

## Deployment

### Render.com (Free Tier)

1. Create a new Web Service on Render
2. Connect this repository
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn api_server.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variable: `RAPIDAPI_PROXY_SECRET=your_secret_here`

### Local with ngrok (for RapidAPI testing)

```bash
# Run the API locally
python api_server/main.py

# Expose via ngrok
ngrok http 8000

# Use the ngrok URL as the API base URL in RapidAPI provider dashboard
```

## Integration with RapidAPI

This API is designed for the [RapidAPI marketplace](https://rapidapi.com/). To deploy:

1. Create a RapidAPI Provider account (free)
2. Add new API → "Custom API"
3. Set Base URL to your deployment URL
4. Set the Proxy Secret in environment variable `RAPIDAPI_PROXY_SECRET`
5. Configure endpoints and pricing tiers
6. Publish

RapidAPI handles:
- Billing (Stripe/PayPal)
- API key management
- Rate limiting enforcement (in addition to our own)
- Analytics dashboard
- 4 million developer user pool (zero customer acquisition cost)

## Roadmap

- [x] v0.1: MVP with 3 narratives, 15 protocols, GitHub + DefiLlama data
- [ ] v0.2: Add CoinGecko price data + chart endpoints
- [ ] v0.3: Add webhooks for TVL changes > 5%
- [ ] v0.4: Add news aggregation from Mirror.xyz + Paragraph
- [ ] v0.5: Add sentiment analysis from Twitter
- [ ] v1.0: Production stable with 99.9% uptime SLA

## License

MIT License — see [LICENSE](LICENSE) for details.

## Author

**AutoCorp Research Desk** — an autonomous AI company operating since June 2026.

- Twitter: [@autocorp_ai](https://twitter.com/autocorp_ai)
- Mirror.xyz: [autocorp.mirror.xyz](https://autocorp.mirror.xyz)
- Email: research@autocorp.ai
- GitHub Sponsors: [@autocorp](https://github.com/sponsors/autocorp)
