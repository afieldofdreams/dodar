# Contributing to DODAR

Thanks for your interest in contributing to the DODAR framework. This is an open research project and there are several high-impact ways to help.

## Where help is most needed

### 1. Expand the scenario bank

The current benchmark uses only 10 of 20 defined scenarios. We need more scenarios across more domains to strengthen the findings. The scenario bank defines the structure — you write the scenario, the pitfalls, and the discriminators.

**Priority domains that need coverage:**
- Healthcare operations (triage, resource allocation, clinical pathways)
- Financial risk assessment (credit, fraud, portfolio)
- Legal reasoning (contract analysis, compliance, case strategy)
- Engineering incident response (outages, security, data loss)
- Supply chain and logistics
- Education and hiring decisions

**What makes a good scenario:**
- Multiple plausible interpretations or causes — not a single right answer
- Real trade-offs between options — not an obvious best choice
- Domain-grounded — based on realistic situations, not abstract puzzles
- Discriminating — the DODAR framework should surface something that baseline reasoning misses

### 2. Run benchmarks on local models

We have limited data on small open-source models. If you have hardware to run local models via Ollama, we need benchmark results for:

- **Llama 3.1 / 3.2** (8B, 70B)
- **Mistral / Mixtral** (7B, 8x7B)
- **Qwen 2.5** (7B, 14B, 32B, 72B)
- **Phi-3 / Phi-4** (3.8B, 14B)
- **Gemma 2** (9B, 27B)
- **DeepSeek** (7B, 67B)
- **Command R** (35B, 104B)

The benchmark harness supports Ollama out of the box. Run `make dev`, go to Runs, select your local models and all scenarios. Export the results and open a PR with the data.

### 3. Test prompt variants

The current DODAR prompts (v2) are a single iteration. We need robustness testing:

- Does rephrasing the phase instructions change results?
- Do different persona descriptions in the pipeline affect quality?
- Is the pipeline ordering important (could Options come before Diagnose)?
- What happens with fewer/more required items per phase?

Bump `PROMPT_VERSION` in `backend/dodar/prompts/templates.py` before running so results don't mix with existing data.

### 4. Add human evaluation baselines

All current scoring is automated (Claude Opus 4.6 + GPT-5.4). We have no human expert scores. If you have domain expertise in any scenario domain, you can score responses manually through the scoring UI. This is the single biggest methodological gap.

---

## How to contribute

### Adding scenarios

Scenarios are in YAML under `backend/data/scenarios/`. Each category gets its own file.

```yaml
- id: "CAT-01"
  category: "CAT"
  title: "Short descriptive title"
  domain: "business"        # business, medical, legal, tech, policy, career, personal, healthcare, finance
  difficulty: "medium"      # easy, medium, hard
  prompt_text: |
    The full scenario text that gets sent to the model.
    Include enough detail to create genuine ambiguity or trade-offs.
    Avoid scenarios with obvious single answers.
  expected_pitfalls:
    - "Common reasoning failure the model might exhibit"
    - "Another pitfall to check for"
  gold_standard_elements:
    - "What a strong response should include"
    - "Another element of a good answer"
  discriminators:
    - dimension: "Diagnosis Quality"
      description: "Specific DODAR gate behavior this scenario tests"
```

Every scenario needs 1-2 **discriminators** — specific gate behaviors that DODAR should uniquely surface. These are what the benchmark measures.

Examples:
- "Holds diagnosis open: lists 3+ hypotheses before committing"
- "Surfaces the equity paradox: recognizes competing fairness claims"
- "Separates risk types: distinguishes financial from reputational risk"

### Adding a model runner

To add support for a new LLM provider:

1. Create `backend/dodar/runners/yourprovider.py`
2. Implement the `ModelRunner` interface:

```python
from dodar.runners.base import ModelResponse, ModelRunner

class YourRunner(ModelRunner):
    model_id = "your-model"

    def __init__(self, model_override: str | None = None) -> None:
        self._model = model_override or "default-model-id"

    async def _call_api(self, prompt: str) -> ModelResponse:
        return ModelResponse(
            text="response text",
            input_tokens=100,
            output_tokens=200,
            latency_seconds=1.5,
        )
```

3. Register it in `backend/dodar/runners/registry.py`
4. Add pricing to `backend/dodar/config.py`

### Improving the DODAR prompt

1. Edit the template in `backend/dodar/prompts/templates.py`
2. Bump `PROMPT_VERSION` (e.g., `"v2"` to `"v3"`)
3. Re-run the benchmark — results are tagged by version
4. Compare versions on the dashboard
5. Include benchmark comparison data in your PR

---

## Development setup

```bash
git clone git@github.com:afieldofdreams/dodar.git
cd dodar
make install
cp .env.example .env    # Add your API keys
make dev                # Backend :8001, Frontend :5173
```

### Running tests

```bash
source .venv/bin/activate
cd backend && pytest
```

### Running the benchmark

From the web UI: **Runs > New Run** — select scenarios, models, conditions.

From the CLI:
```bash
source .venv/bin/activate
cd backend
dodar list                          # List scenarios
dodar run --scenarios AMB-01 AMB-02 --models gpt-4o --conditions zero_shot dodar
```

### Exporting results

Use the Export page in the web UI, or hit the API directly:
```bash
curl http://localhost:8001/api/reports/export?format=json > results.json
```

The full export includes scenario metadata, prompts, responses, per-item scores with rationales, and aggregate statistics.

---

## Code style

- Python: formatted with `ruff`
- TypeScript: ESLint config in `frontend/eslint.config.js`
- No docstrings required on obvious functions
- Comments only where logic isn't self-evident

## Pull requests

- Keep PRs focused — one feature or fix per PR
- If changing the DODAR prompt, include benchmark comparison data
- If adding scenarios, include discriminators and gold standard elements
- If adding benchmark results, include the full export JSON
- Tests appreciated but not blocking

## Questions?

Open an issue on [GitHub](https://github.com/afieldofdreams/dodar/issues) or email [adam@crox.io](mailto:adam@crox.io).
