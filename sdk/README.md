# DODAR

**Structured reasoning framework for AI agents** — adapted from aviation Crew Resource Management.

DODAR (Diagnose, Options, Decide, Action, Review) imposes explicit gates at each stage of analysis, preventing the reasoning failures that LLMs share with humans under pressure: premature anchoring, option narrowing, and treating decisions as final.

## Install

```bash
pip install dodar
```

## Quick start

```python
from dodar import DODAR

dodar = DODAR(model="gpt-4.1-mini")
result = dodar.analyze("Your scenario here...")

# Structured access to each reasoning phase
result.diagnosis.hypotheses       # Ranked competing causes
result.options.alternatives       # Distinct paths with trade-offs
result.decision.recommendation    # The call + justification
result.action.steps               # Sequenced implementation plan
result.review.failure_modes       # Self-critique
```

## Pipeline mode

For maximum quality, use the pipeline where each DODAR phase runs as a separate model call:

```python
from dodar import DODAR

dodar = DODAR(model="gpt-4.1-mini", mode="pipeline")
result = dodar.analyze("Your scenario here...")
```

Research shows GPT-4.1 Mini + pipeline scores 104% of Claude Opus 4.6 zero-shot quality at 89% lower cost. [Read the whitepaper](https://dodar.crox.io/research).

## Supported models

| Provider | Models |
|----------|--------|
| Anthropic | claude-opus-4-6, claude-sonnet-4-5, claude-haiku-4-5 |
| OpenAI | gpt-5.4, gpt-4o, gpt-4o-mini, gpt-4.1-mini, gpt-4.1-nano |
| Google | gemini-2.0-flash (install with `pip install dodar[google]`) |
| Ollama | Any local model (install with `pip install dodar[ollama]`) |

## Links

- [Documentation](https://dodar.crox.io/framework)
- [Research & whitepaper](https://dodar.crox.io/research)
- [GitHub](https://github.com/afieldofdreams/dodar)

## License

MIT
