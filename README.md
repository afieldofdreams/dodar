# DODAR

**Structured reasoning framework for AI agents** — adapted from aviation Crew Resource Management.

DODAR (Diagnose, Options, Decide, Action, Review) imposes explicit gates at each stage of analysis, preventing the reasoning failures that LLMs share with humans under pressure: premature anchoring, option narrowing, and treating decisions as final.

## Quick Start — Python SDK

```bash
pip install dodar
```

```python
from dodar import DODAR

dodar = DODAR(model="claude-sonnet-4-5")
result = dodar.analyze("Your scenario here...")

# Structured access to each reasoning phase
result.diagnosis.hypotheses       # Ranked competing causes
result.options.alternatives       # Distinct paths with trade-offs
result.options.core_tension       # The fundamental trade-off
result.decision.recommendation    # The call + justification
result.decision.confidence        # Confidence level
result.action.steps               # Sequenced implementation plan
result.action.reversible_steps    # Which steps can be undone
result.review.failure_modes       # Self-critique
result.review.abort_conditions    # When to abandon the plan
```

### Agent Integration

```python
from dodar import DODAR

dodar = DODAR(model="gpt-4o")

async def agent_decision(context: str) -> dict:
    result = await dodar.analyze_async(context)

    if result.decision.confidence == "low":
        return {"action": "gather_info", "unknowns": result.diagnosis.unknowns}

    return {
        "action": "execute",
        "steps": result.action.steps,
        "abort_if": result.review.abort_conditions,
    }
```

## The Five Phases

| Phase | Gate | What It Does |
|-------|------|-------------|
| **Diagnose** | Hold diagnosis open | List 3+ competing hypotheses. Challenge anchoring. Surface latent assumptions. Map unknowns. |
| **Options** | Force genuine trade-offs | Enumerate 4+ distinct alternatives. Name the core tension. Separate risk types. Quantify opportunity costs. |
| **Decide** | Commit with transparency | Make a clear recommendation. Justify against each alternative. State confidence and falsifiability. |
| **Action** | Concrete sequencing | Define specific steps with dependencies. Identify reversible vs. irreversible actions. |
| **Review** | Self-critique | Identify 3+ failure modes with triggers. Audit assumptions. Specify abort conditions. |

## Supported Models

| Provider | Models |
|----------|--------|
| **Anthropic** | claude-opus-4-6, claude-sonnet-4-5, claude-haiku-4-5 |
| **OpenAI** | gpt-5.4, gpt-4o, gpt-4o-mini, gpt-4.1-mini, gpt-4.1-nano |
| **Google** | gemini-2.0-flash |
| **Local (Ollama)** | qwen2.5:14b, qwen2.5:7b, llama3.1:8b, phi3:3.8b |

## Web Playground

A web UI for interactive DODAR analysis, side-by-side baseline comparison, and benchmark visualization.

```bash
git clone git@github.com:afieldofdreams/dodar.git
cd dodar
make install
cp .env.example .env   # Add your API keys
make dev               # Backend :8001, Frontend :5173
```

Open http://localhost:5173 to access:
- **Playground** — Paste a scenario, pick a model, watch DODAR reason phase by phase
- **Documentation** — The five phases, SDK examples, agent integration patterns
- **Benchmark Results** — Comparison charts, effect sizes, per-model radar plots

## Benchmark

The repo includes a validation benchmark that compares DODAR against three baselines (zero-shot, chain-of-thought, length-matched) across 20 scenarios in two categories:

| Category | Scenarios | Focus |
|----------|-----------|-------|
| **Ambiguous Diagnosis (AMB)** | 10 | Resisting premature pattern-matching |
| **Competing Trade-offs (TRD)** | 10 | Surfacing genuine tensions between valid alternatives |

Scenarios span business, medical, legal, tech, policy, career, and personal domains.

### Running the Benchmark

From the web UI: **Runs → New Run** — select scenarios, models, conditions. Cost estimation included. Live progress via WebSocket.

From the CLI:
```bash
cd backend && source .venv/bin/activate

dodar list                          # List all scenarios
dodar validate                      # Validate scenario YAML
dodar run --scenarios AMB-01 AMB-02 --models gpt-4o --conditions zero_shot dodar
```

### Scoring

Auto-score with any supported model (Claude, GPT, or Gemini) using scenario-specific rubrics. Blind presentation — the scorer doesn't know which model or condition produced the response.

Responses are scored on 6 dimensions (1–5):
1. **Diagnosis Quality** — Problem identification; avoidance of false anchors
2. **Option Breadth** — Range and novelty of alternatives
3. **Decision Justification** — Reasoning about trade-offs and uncertainty
4. **Action Specificity** — Concrete steps with dependency mapping
5. **Review / Self-Correction** — Failure modes and assumption gaps
6. **Overall Trustworthiness** — Would an expert endorse the reasoning?

### Prompt Versioning

Templates in `backend/dodar/prompts/templates.py` are versioned. Bump `PROMPT_VERSION` when you change the DODAR prompt. Runs are tagged by version, and the dashboard filters by version for side-by-side comparison.

## Architecture

```
dodar/
├── backend/
│   ├── dodar/
│   │   ├── sdk.py           Public API (DODAR class)
│   │   ├── engine/          Benchmark execution
│   │   ├── models/          Pydantic data models
│   │   ├── prompts/         Versioned prompt templates
│   │   ├── routes/          API endpoints + WebSocket + Playground
│   │   ├── runners/         Model clients (Anthropic, OpenAI, Google, Ollama)
│   │   ├── scoring/         Blind + auto-scoring
│   │   └── storage/         JSON file persistence
│   ├── data/scenarios/      YAML scenario definitions
│   └── tests/               33 tests (pytest)
│
└── frontend/                React + TypeScript + Vite
    └── src/
        ├── pages/           Playground, Docs, Dashboard, Runs, Scoring
        ├── api/             API client layer
        └── components/      Layout, charts (Recharts)
```

## Configuration

All settings via environment variables or `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `GOOGLE_API_KEY` | — | Google AI API key |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-5` | Default Anthropic model |
| `OPENAI_MODEL` | `gpt-4o` | Default OpenAI model |
| `GOOGLE_MODEL` | `gemini-2.0-flash` | Default Google model |
| `AUTOSCORE_MODEL` | `claude-opus-4-6` | Model for auto-scoring |

Local models (Ollama) need no API key — just have Ollama running on `localhost:11434`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add scenarios, improve prompts, add model runners, and use the SDK.

## License

[MIT](LICENSE)

---

*DODAR for AI — adapted from aviation Crew Resource Management by [Adam Field](mailto:adam@crox.io).*
