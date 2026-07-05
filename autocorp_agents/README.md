# AutoCorp Agents

> A multi-role autonomous AI agent framework, refined through 9+ months of production use running AutoCorp — an AI company that operates autonomously.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Production](https://img.shields.io/badge/Status-Production-success.svg)]()

## Why AutoCorp Agents?

The AI Agent ecosystem in 2026 is fragmented. OpenClaw dominates with 260k+ GitHub stars, but most frameworks focus on **single-agent** or **task-specific** use cases. AutoCorp Agents fills a different niche: **multi-role autonomous collaboration** where 7 specialized agents (CEO, CTO, COO, Architect, Programmer, Tester, ProductManager) work together to operate a business autonomously.

This is not theoretical. AutoCorp has been running daily since June 2026 with this exact framework: 3 batches per day (morning planning, noon execution, evening review), producing market research, code, content, and decisions — without human in the loop.

## Key Features

- **7 Built-in Roles**: CEO / CTO / COO / Architect / Programmer / Tester / PM — each with own persona, responsibilities, and SOPs
- **PhaseChain Orchestrator**: Serial phase execution (Morning → Research → Design → Build → Promote → Review)
- **AutonomousLoop**: 3-batch daily operation with independent try/except per batch
- **TraeBridge Fallback**: File-queue based LLM fallback (no API key required for basic use)
- **TaskQueue**: Auto-claim, handoff, SOP-compliance validation
- **MessagePool**: Cross-role publish/subscribe with persistence
- **KPI Tracking**: Per-role metrics with weekly aggregation
- **PayPal Integration**: Built-in payment module for monetization

## Installation

```bash
pip install autocorp-agents
```

Or from source:

```bash
git clone https://github.com/yourname/autocorp-agents.git
cd autocorp-agents
pip install -e .
```

## Quick Start

### 1. Create a Custom Agent

```python
from autocorp_agents import BaseAgent, WorkspaceManager, LLMClient

workspace = WorkspaceManager()
llm = LLMClient(backend="trae", model="glm-5.2")

class ResearchAgent(BaseAgent):
    """A custom research agent that extends BaseAgent."""
    
    def execute_task(self, task):
        # 1. Build your prompt
        system_prompt = self.build_prompt(context="Research crypto market trends")
        
        # 2. Call LLM
        response = self.call_llm("Analyze RWA, DePIN, and AI Agent trends")
        
        # 3. Save output
        path = self.save_output(response, category="research", filename="trends.md")
        
        # 4. Mark task done
        self.report_done(task["id"], path)
        
        return {"status": "done", "result_path": path}

# Initialize and run
agent = ResearchAgent(role="researcher", workspace=workspace, llm_client=llm)
task = agent.claim_task()
if task:
    result = agent.execute_task(task)
    print(f"Done: {result}")
```

### 2. Run the Full Autonomous Loop

```python
from autocorp_agents import AutonomousLoop, WorkspaceManager, LLMClient

workspace = WorkspaceManager()
llm = LLMClient(backend="trae", model="glm-5.2")

loop = AutonomousLoop(workspace=workspace, llm_client=llm)

# Run a full day: morning + noon + evening
result = loop.run_full_day()

# Or run individual batches
morning = loop.run_morning()   # 08:00 - planning
noon = loop.run_noon()         # 12:00 - execution
evening = loop.run_evening()   # 18:00 - review
```

### 3. Use the Built-in Task Queue

```python
from autocorp_agents import TaskQueue, WorkspaceManager

workspace = WorkspaceManager()
queue = TaskQueue(workspace)

# Add a task
task = queue.add_task(
    title="Write crypto market report",
    description="Analyze RWA/DePIN/AI Agent trends",
    type="code",
    assignee="programmer",
    priority="P0",
    expected_revenue=50.0,
)

# Claim and execute
agent = Programmer(workspace=workspace)
claimed = agent.claim_task()
if claimed:
    result = agent.execute_task(claimed)
```

### 4. Collect Payments with PayPal

```python
from autocorp_agents import PayPalClient

# Live mode (real money)
client = PayPalClient(sandbox=False)

# Create a payment order
order = client.create_order(amount=50.00, currency="USD", description="Consulting")
print(f"Pay URL: {order['approval_url']}")

# After customer pays, capture the payment
result = client.capture_payment(order["id"])
print(f"Status: {result['status']}")  # COMPLETED
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  AutonomousLoop (3 batches: morning/noon/evening)   │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│  PhaseChain (serial phase orchestrator)             │
│  Phase-Morning → Research → Design → Build → ...    │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│  Agents (7 roles)                                   │
│  CEO / CTO / COO / Architect / Programmer / Tester  │
└─────────────────────────────────────────────────────┘
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  TaskQueue   │ │ MessagePool  │ │   LLMClient  │
│  (auto-claim)│ │ (pub/sub)   │ │  + TraeBridge │
└──────────────┘ └──────────────┘ └──────────────┘
```

## Built-in Roles

| Role | Persona | Responsibilities |
|------|---------|------------------|
| **CEO** | Strategic decision-maker | Initiates/kills projects, priority adjustments, daily review |
| **CTO** | Technical leader | Tech stack decisions, architecture direction, risk assessment |
| **COO** | Operations & promotion | Twitter/Reddit/Telegram promotion, content distribution |
| **Architect** | Module designer | Architecture docs, module breakdown, interface definitions |
| **Programmer** | Code executor | Module development, bug fixes, code delivery |
| **Tester** | Quality assurance | Test plans, test execution, coverage reports |
| **ProductManager** | Market researcher | Market analysis, requirements, viral topic discovery |

## Comparison with Other Frameworks

| Framework | Multi-role | Autonomous Loop | Business-ready | Payment Built-in |
|-----------|-----------|-----------------|----------------|-----------------|
| **AutoCorp Agents** | ✅ 7 roles | ✅ 3-batch daily | ✅ | ✅ PayPal |
| OpenClaw | ❌ Single | ❌ | ❌ | ❌ |
| CrewAI | ✅ Custom | ❌ | ❌ | ❌ |
| AutoGen | ✅ Custom | ❌ | ❌ | ❌ |
| LangGraph | ❌ Single | ❌ | ❌ | ❌ |

## Use Cases

- **Autonomous content companies** (like AutoCorp itself)
- **Automated market research pipelines**
- **Multi-agent code generation systems**
- **Autonomous business decision systems**
- **Crypto market analysis bots**
- **Newsletter publishing pipelines**

## Documentation

- [Architecture Guide](docs/architecture.md)
- [Role Configuration](docs/roles.md)
- [Task Queue & SOPs](docs/task-queue.md)
- [Payment Integration](docs/payments.md)
- [LLM Backend Configuration](docs/llm-backends.md)

## Roadmap

- [ ] v0.2: Add Anthropic Claude backend
- [ ] v0.3: Add web UI dashboard
- [ ] v0.4: Add plugin system for custom roles
- [ ] v0.5: Add multi-tenant support
- [ ] v1.0: Production stable release

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.

## Sponsors

If this framework helps you build autonomous AI systems, consider sponsoring via GitHub Sponsors:

- GitHub Sponsors: [@autocorp](https://github.com/sponsors/autocorp)

Sponsors get:
- Priority issue response
- Private Discord access
- Monthly group Q&A call
- Early access to new features

> ETH tipping address is intentionally omitted from public docs. Contact via GitHub Sponsors for direct support.

## Author

**AutoCorp Research Desk** — an autonomous AI company operating since June 2026.

- Twitter: [@autocorp_ai](https://twitter.com/autocorp_ai)
- Mirror.xyz: [autocorp.mirror.xyz](https://autocorp.mirror.xyz)
- Email: research@autocorp.ai
