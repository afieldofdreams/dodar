# Contributing to DODAR

Thanks for your interest in contributing to the DODAR framework. Here's how you can help.

## Adding New Scenarios

Scenarios are defined in YAML files under `backend/data/scenarios/`. Each category gets its own file.

### Scenario Structure

```yaml
- id: "CAT-01"
  category: "CAT"
  title: "Short descriptive title"
  domain: "business"        # business, medical, legal, tech, policy, career, personal
  difficulty: "medium"      # easy, medium, hard
  prompt_text: |
    The full scenario text that gets sent to the model...
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

### What Makes a Good Scenario

- **Ambiguity**: Multiple plausible interpretations or causes, not a single right answer
- **Real trade-offs**: Options that have genuine tensions, not an obvious best choice
- **Discriminating**: The DODAR framework should surface something that baseline reasoning misses
- **Domain grounding**: Based on realistic situations, not abstract puzzles

### Discriminators

Every scenario needs 1-2 discriminators — specific behaviors that DODAR's gate structure should uniquely surface. These are what the benchmark actually measures.

Examples:
- "Holds diagnosis open: lists 3+ hypotheses before committing"
- "Surfaces the equity paradox: recognizes competing fairness claims"
- "Separates risk types: distinguishes financial from reputational risk"

## Improving the DODAR Prompt

The DODAR prompt template lives in `backend/dodar/prompts/templates.py`.

1. Edit the template
2. Bump `PROMPT_VERSION` (e.g., `"v2"` to `"v3"`)
3. Re-run the benchmark — results are tagged by version so they won't mix
4. Compare versions on the dashboard

## Adding a Model Runner

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
        # Call your API here
        return ModelResponse(
            text="response text",
            input_tokens=100,
            output_tokens=200,
            latency_seconds=1.5,
        )
```

3. Register it in `backend/dodar/runners/registry.py`
4. Add pricing to `backend/dodar/config.py`
5. Add the model ID to `frontend/src/types/index.ts`

## Using the DODAR SDK

```python
from dodar import DODAR

dodar = DODAR(provider="anthropic", model="claude-sonnet-4-5")
result = dodar.analyze("Your scenario...")

# Structured access to each phase
print(result.diagnosis.hypotheses)
print(result.options.alternatives)
print(result.decision.recommendation)
print(result.action.steps)
print(result.review.failure_modes)
```

## Development Setup

```bash
git clone git@github.com:afieldofdreams/dodar.git
cd dodar
make install
cp .env.example .env
# Add your API keys to .env
make dev
```

## Running Tests

```bash
cd backend
source .venv/bin/activate
pytest
```

## Code Style

- Python: formatted with `ruff`
- TypeScript: ESLint config in `frontend/eslint.config.js`
- No docstrings required on obvious functions
- Comments only where logic isn't self-evident

## Pull Requests

- Keep PRs focused — one feature or fix per PR
- If changing the DODAR prompt, include benchmark comparison data
- If adding scenarios, include discriminators and gold standard elements
- Tests appreciated but not blocking
