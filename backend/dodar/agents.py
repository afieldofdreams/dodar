"""
DODAR Multi-Agent Pipeline — each phase handled by a specialized agent.

The pipeline chains 5 sequential agents:
  Diagnose → Options → Decide → Action → Review

Each agent receives:
  1. A focused system prompt for its specific phase
  2. The original scenario
  3. The output from all previous phases (building context)

Each agent also has a GATE CHECK: it validates the previous phase's output
and can push back if the gate criteria aren't met.

Usage:
    from dodar.agents import DODARPipeline

    pipeline = DODARPipeline(model="gpt-4.1-nano")
    result = await pipeline.run("Your scenario here...")

    print(result.phases["diagnose"])
    print(result.phases["options"])
    print(result.total_tokens)
    print(result.total_cost_usd)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from dodar.runners.base import ModelResponse
from dodar.runners.registry import get_runner
from dodar.config import get_settings


# --------------------------------------------------------------------------- #
# Phase system prompts — focused and gate-enforcing
# --------------------------------------------------------------------------- #

DIAGNOSE_SYSTEM = """\
You are a diagnostic reasoning specialist. Your ONLY job is to analyze a \
scenario and produce a thorough differential diagnosis. You must RESIST the \
pull of the most obvious explanation.

RULES:
- List 3+ competing hypotheses, ranked by plausibility
- Challenge the most obvious explanation: why might it be wrong?
- Surface latent assumptions: what correlations are being treated as causation?
- Identify paradoxes: does any evidence contradict the leading hypothesis?
- Map the unknowns: what specific information would disambiguate?
- Consider polycontribution: could multiple causes interact?
- Do NOT recommend solutions — that is not your job
- Do NOT commit to a single diagnosis

Output format:
## HYPOTHESES (ranked)
1. [Most plausible] ...
2. ...
3. ...

## ANCHORING CHALLENGE
...

## LATENT ASSUMPTIONS
...

## UNKNOWNS
...

## POLYCONTRIBUTION ASSESSMENT
..."""

OPTIONS_SYSTEM = """\
You are a strategic options analyst. You receive a scenario AND a diagnosis \
from the previous analyst. Your ONLY job is to generate genuinely distinct \
options with explicit trade-offs.

RULES:
- Generate at least 4 genuinely distinct alternatives (not variations of the same approach)
- Include at least one unconventional or counterintuitive option
- Name the CORE TENSION: what fundamental trade-off makes this hard?
- For each option, identify the TYPE of risk (financial, reputational, technical, etc.)
- For each option, state what must be true for it to work
- Quantify opportunity costs: what do you give up by not choosing each alternative?
- Surface hidden stakeholders and binding constraints
- Do NOT recommend a single option — that is the next agent's job

GATE CHECK — Before generating options, verify the diagnosis:
- Does it list 3+ hypotheses? If not, note what's missing.
- Does it challenge the obvious answer? If it anchored, flag this.
- Are unknowns mapped? If not, identify them.

Output format:
## DIAGNOSIS GATE CHECK
[Pass/Fail + notes]

## CORE TENSION
...

## OPTIONS
### Option 1: [Name]
- Description: ...
- Risk type: ...
- Assumes: ...
- Opportunity cost if rejected: ...

### Option 2: [Name]
...

## HIDDEN CONSTRAINTS
..."""

DECIDE_SYSTEM = """\
You are a decision-making specialist. You receive a scenario, a diagnosis, \
and a set of options from previous analysts. Your ONLY job is to make a clear \
recommendation with transparent, falsifiable reasoning.

RULES:
- State your recommendation clearly — no hedging with "it depends"
- Justify against EACH alternative: why are you NOT choosing it?
- Name binding constraints (others' risk tolerance, deadlines, budgets)
- State your time horizon and whether shifting it would change the decision
- Quantify what you are giving up (the opportunity cost of your choice)
- State confidence (low/medium/high) and what would change your mind

GATE CHECK — Before deciding, verify the options:
- Are there 4+ genuinely distinct options? If not, flag this.
- Is the core tension named? If not, identify it.
- Are opportunity costs quantified? If not, estimate them.

Output format:
## OPTIONS GATE CHECK
[Pass/Fail + notes]

## RECOMMENDATION
...

## WHY NOT THE ALTERNATIVES
- Not Option X because: ...
- Not Option Y because: ...

## BINDING CONSTRAINTS
...

## TIME HORIZON
...

## OPPORTUNITY COST
...

## CONFIDENCE & FALSIFIABILITY
Confidence: [low/medium/high]
Would change mind if: ..."""

ACTION_SYSTEM = """\
You are an implementation planning specialist. You receive a scenario, diagnosis, \
options, and a decision from previous analysts. Your ONLY job is to translate the \
decision into concrete, sequenced, executable steps.

RULES:
- Define specific steps with clear owners, inputs, and outputs
- Identify sequencing and dependencies: what must happen before what?
- Mark each step as REVERSIBLE or IRREVERSIBLE
- Sequence reversible steps first where possible
- Identify blockers and prerequisites
- Include rough timeline and resource requirements
- Be concrete — "schedule a meeting with X to discuss Y" not "consult stakeholders"

Output format:
## IMPLEMENTATION PLAN

### Step 1: [Action] [REVERSIBLE/IRREVERSIBLE]
- Dependencies: ...
- Timeline: ...
- Resources: ...

### Step 2: ...

## CRITICAL PATH
...

## BLOCKERS
..."""

REVIEW_SYSTEM = """\
You are a critical review specialist and devil's advocate. You receive the ENTIRE \
analysis chain (diagnosis → options → decision → action plan) from previous analysts. \
Your ONLY job is to find the weaknesses, failure modes, and unvalidated assumptions.

RULES:
- Identify at least 3 specific failure modes in the plan
- For each: what triggers it, how would you detect it, what would you do instead
- Audit ALL assumptions from previous phases — which are unvalidated?
- Specify concrete abort conditions: when should this plan be abandoned?
- Identify the point of no return: where does the plan become irreversible?
- Be adversarial — your job is to stress-test, not to agree

GATE CHECK — Review the entire chain:
- Did the diagnosis hold multiple hypotheses open, or did it anchor?
- Did the options surface genuine trade-offs, or collapse to a binary?
- Did the decision justify against alternatives, or just argue for the winner?
- Is the action plan concrete and sequenced, or vague?
Flag any phase that fell short.

Output format:
## CHAIN QUALITY AUDIT
- Diagnosis: [Pass/Weak/Fail] ...
- Options: [Pass/Weak/Fail] ...
- Decision: [Pass/Weak/Fail] ...
- Action: [Pass/Weak/Fail] ...

## FAILURE MODES
### 1. [Name]
- Trigger: ...
- Detection: ...
- Mitigation: ...

### 2. ...

## UNVALIDATED ASSUMPTIONS
...

## ABORT CONDITIONS
...

## POINT OF NO RETURN
..."""

PHASE_CONFIGS = [
    ("diagnose", DIAGNOSE_SYSTEM),
    ("options", OPTIONS_SYSTEM),
    ("decide", DECIDE_SYSTEM),
    ("action", ACTION_SYSTEM),
    ("review", REVIEW_SYSTEM),
]


# --------------------------------------------------------------------------- #
# Pipeline result
# --------------------------------------------------------------------------- #

@dataclass
class PipelinePhaseResult:
    """Result from a single agent in the pipeline."""
    phase: str
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_seconds: float = 0.0


@dataclass
class PipelineResult:
    """Complete result from the multi-agent DODAR pipeline."""
    phases: dict[str, str] = field(default_factory=dict)
    phase_results: list[PipelinePhaseResult] = field(default_factory=list)
    text: str = ""  # Full concatenated output
    total_tokens: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_latency_seconds: float = 0.0
    total_cost_usd: float = 0.0
    model: str = ""


# --------------------------------------------------------------------------- #
# Pipeline
# --------------------------------------------------------------------------- #

class DODARPipeline:
    """Multi-agent DODAR pipeline — each phase is a separate LLM call.

    Each agent receives the scenario + all previous phases as context.
    Each agent validates the previous phase's output (gate check).

    Args:
        model: Model ID for all agents (e.g., "gpt-4.1-nano", "qwen2.5:7b").
        diagnose_model: Override model for diagnose phase only.
        options_model: Override model for options phase only.
        decide_model: Override model for decide phase only.
        action_model: Override model for action phase only.
        review_model: Override model for review phase only.
    """

    def __init__(
        self,
        model: str = "gpt-4.1-nano",
        diagnose_model: str | None = None,
        options_model: str | None = None,
        decide_model: str | None = None,
        action_model: str | None = None,
        review_model: str | None = None,
    ) -> None:
        self._default_model = model
        self._phase_models = {
            "diagnose": diagnose_model or model,
            "options": options_model or model,
            "decide": decide_model or model,
            "action": action_model or model,
            "review": review_model or model,
        }
        # Pre-validate all models exist
        for phase, m in self._phase_models.items():
            get_runner(m)  # Raises if unknown

    async def run(self, scenario: str) -> PipelineResult:
        """Run the full 5-agent pipeline sequentially."""
        settings = get_settings()
        result = PipelineResult(model=self._default_model)
        accumulated_context = f"## SCENARIO\n{scenario}"

        for phase_name, system_prompt in PHASE_CONFIGS:
            model_id = self._phase_models[phase_name]
            runner = get_runner(model_id)

            # Build the user message: scenario + all previous phases
            user_message = accumulated_context

            # Call the agent
            response = await runner.run(
                self._format_prompt(system_prompt, user_message)
            )

            # Calculate cost
            pricing = settings.model_pricing.get(model_id, {"input": 0, "output": 0})
            cost = (
                response.input_tokens / 1_000_000 * pricing["input"]
                + response.output_tokens / 1_000_000 * pricing["output"]
            )

            # Store result
            phase_result = PipelinePhaseResult(
                phase=phase_name,
                text=response.text,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                latency_seconds=response.latency_seconds,
            )
            result.phase_results.append(phase_result)
            result.phases[phase_name] = response.text
            result.total_tokens += response.input_tokens + response.output_tokens
            result.total_input_tokens += response.input_tokens
            result.total_output_tokens += response.output_tokens
            result.total_latency_seconds += response.latency_seconds
            result.total_cost_usd += cost

            # Add this phase's output to the context for the next agent
            accumulated_context += f"\n\n## {phase_name.upper()} (from previous analyst)\n{response.text}"

        # Build full text
        result.text = "\n\n".join(
            f"## Phase: {pr.phase.upper()}\n{pr.text}"
            for pr in result.phase_results
        )
        result.total_cost_usd = round(result.total_cost_usd, 6)

        return result

    def _format_prompt(self, system_prompt: str, user_message: str) -> str:
        """Format system + user into a single prompt.

        Most runners take a single prompt string. We embed the system
        prompt as context since the runner interface doesn't support
        separate system messages.
        """
        return f"{system_prompt}\n\n---\n\n{user_message}"

    def __repr__(self) -> str:
        models = set(self._phase_models.values())
        if len(models) == 1:
            return f"DODARPipeline(model={next(iter(models))!r})"
        return f"DODARPipeline(models={dict(self._phase_models)!r})"
