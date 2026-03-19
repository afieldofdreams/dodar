# DODAR Validation Benchmark

A full-stack benchmarking harness for validating the **DODAR** (Diagnose, Options, Decide, Action, Review) reasoning framework — adapted from aviation Crew Resource Management (CRM) principles — against baseline prompting approaches across multiple large language models.

## What is DODAR?

DODAR is a structured reasoning framework that imposes explicit **gates** at each stage of analysis:

| Phase | Purpose | Gate Behavior |
|-------|---------|---------------|
| **Diagnose** | Hold diagnosis open; resist anchoring | Enumerate multiple root causes before committing |
| **Options** | Surface genuine trade-offs | Enumerate distinct alternatives with explicit opportunity costs |
| **Decide** | Make the call with justified reasoning | Weigh trade-offs, name binding constraints, state falsifiability |
| **Action** | Map implementation concretely | Sequence steps, identify dependencies and reversibility |
| **Review** | Identify failure modes | Specify triggers for course correction, flag assumptions |

## What This Benchmark Tests

The benchmark compares DODAR-guided prompting against three baselines:

| Condition | Description |
|-----------|-------------|
| **Zero-shot** | Model responds without framework guidance |
| **Chain-of-Thought** | Standard "think step by step" reasoning |
| **Length-matched** | Same token budget as DODAR, but unstructured |
| **Full DODAR** | Explicit framework with phase gates |

Responses are scored on 6 dimensions (1-5 scale):

1. **Diagnosis Quality** — Accuracy of problem identification; avoidance of false anchors
2. **Option Breadth** — Range and novelty of alternatives considered
3. **Decision Justification** — Explicit reasoning about trade-offs and uncertainty
4. **Action Specificity** — Concrete, sequenced steps with dependency mapping
5. **Review / Self-Correction** — Identification of failure modes and assumption gaps
6. **Overall Trustworthiness** — Confidence that an expert would endorse the reasoning

## Architecture

```
dodar/
├── backend/          FastAPI + Python async
│   ├── dodar/
│   │   ├── engine/       Benchmark execution (shared by CLI + web)
│   │   ├── models/       Pydantic data models
│   │   ├── prompts/      Prompt templates (versioned)
│   │   ├── routes/       API endpoints + WebSocket
│   │   ├── runners/      Model API clients (Anthropic, OpenAI, Google)
│   │   ├── scoring/      Blind scoring + auto-scoring with Claude
│   │   └── storage/      JSON file persistence
│   └── data/
│       └── scenarios/    YAML scenario definitions
│
└── frontend/         React + TypeScript + Vite
    └── src/
        ├── pages/        Dashboard, Scenarios, Runs, Scoring, Export
        ├── api/          API client layer
        ├── components/   Layout, charts (Recharts)
        └── hooks/        WebSocket, React Query wrappers
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- API keys for at least one model provider

### Setup

```bash
# Clone
git clone git@github.com:afieldofdreams/dodar.git
cd dodar

# Install dependencies
make install

# Configure API keys
cp .env.example .env
# Edit .env with your keys
```

### Run

```bash
make dev
```

This starts the FastAPI backend on `:8000` and the Vite frontend on `:5173`. Open http://localhost:5173.

### Workflow

1. **Browse scenarios** — `/scenarios` shows all 20 scenarios across AMB (Ambiguous Diagnosis) and TRD (Competing Trade-offs) categories
2. **Start a benchmark run** — `/runs/new` lets you select scenarios, models, and conditions. Cost estimation included.
3. **Watch progress** — Live WebSocket updates on the run detail page
4. **Score responses** — `/scoring` creates a scoring session tied to a specific run. Auto-score with Claude or score manually with blind presentation.
5. **View results** — `/` dashboard shows comparison charts, radar plots per model, and Cohen's d effect sizes. Filter by prompt version to compare iterations.
6. **Export** — Download results as CSV or JSON for external analysis

## Scenarios

Each scenario includes:

- **Prompt text** — The situation to analyze
- **Expected pitfalls** — Common reasoning failures to check for
- **Gold standard elements** — What a strong response covers
- **DODAR discriminators** — Specific gate behaviors that DODAR should uniquely surface

### Categories

| Category | Code | Count | Focus |
|----------|------|-------|-------|
| Ambiguous Diagnosis | AMB | 10 | Resisting premature pattern-matching |
| Competing Trade-offs | TRD | 10 | Surfacing genuine tensions between valid alternatives |

Scenarios span business, medical, legal, tech, policy, career, and personal domains at easy/medium/hard difficulty levels.

## Prompt Versioning

Templates are versioned (`v1`, `v2`, etc.) in `backend/dodar/prompts/templates.py`. When you modify the DODAR prompt, bump `PROMPT_VERSION`. Runs are tagged with the version, and the dashboard can filter by version to compare prompt iterations side by side.

## Auto-Scoring

Auto-scoring uses Claude as an evaluator with scenario-specific rubrics. The scorer receives:

- The scenario prompt and model response
- Expected pitfalls and gold standard elements
- DODAR discriminators

It scores blind (no knowledge of which model or condition produced the response) and provides per-dimension rationales.

## Configuration

All settings can be overridden via environment variables or `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `GOOGLE_API_KEY` | — | Google AI API key |
| `ANTHROPIC_MODEL` | `claude-3-haiku-20240307` | Model for Anthropic benchmark runs |
| `OPENAI_MODEL` | `gpt-4o` | Model for OpenAI benchmark runs |
| `GOOGLE_MODEL` | `gemini-2.0-flash` | Model for Google benchmark runs |
| `AUTOSCORE_MODEL` | `claude-3-haiku-20240307` | Model used for auto-scoring |

## CLI

A headless CLI is available for CI or scripted runs:

```bash
cd backend
source .venv/bin/activate

# List scenarios
dodar list

# Validate YAML
dodar validate

# Run benchmark
dodar run --scenarios AMB-01 AMB-02 --models gpt-4o --conditions zero_shot dodar
```

## License

MIT
