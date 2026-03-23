# The DODAR Framework for AI Reasoning

**A structured reasoning framework adapted from aviation Crew Resource Management for AI agents and human-AI collaboration.**

---

## Origins

DODAR originates from **Crew Resource Management (CRM)** in aviation — the set of practices that flight crews use to make high-stakes decisions under uncertainty, time pressure, and incomplete information. In the cockpit, DODAR provides a shared mental model: when something goes wrong, the crew works through Diagnose → Options → Decide → Action → Review in sequence, ensuring that no critical step is skipped and that decisions are challenged before they become irreversible.

The insight behind adapting DODAR for AI is straightforward: **large language models fail in the same ways that humans fail under pressure.** They anchor on the first plausible explanation. They collapse complex trade-offs into a single recommendation. They present decisions as final without identifying failure modes. They skip from diagnosis to action without considering alternatives.

DODAR addresses these failure modes by imposing explicit **gates** — checkpoints that prevent the reasoning process from advancing until specific cognitive work has been done.

---

## The Five Phases

### Phase 1: DIAGNOSE

**Purpose:** Resist the pull of the obvious explanation. Hold diagnosis open.

The most common reasoning failure — in humans and LLMs alike — is **premature closure**: committing to the first plausible cause and stopping the search. In aviation, this manifests as "confirmation bias" — the crew fixates on one instrument reading and ignores contradictory evidence. In AI, it manifests as **anchoring**: the model latches onto the most salient pattern in the prompt and builds its entire response around it.

The Diagnose gate counteracts this by requiring:

1. **Multiple competing hypotheses.** List 3+ plausible explanations, ranked by plausibility. Do not stop at the first one that fits.
2. **Anchoring challenge.** Identify the most obvious explanation and explicitly ask: why might it be wrong? What would a contrarian consider?
3. **Latent assumption surfacing.** Name what you are assuming that hasn't been stated. Is a correlation being treated as causation? Is a temporal sequence being treated as a causal chain?
4. **Paradox identification.** Does any evidence contradict the leading hypothesis? What does that tell you?
5. **Unknown mapping.** What specific information is missing? What single data point would most change your assessment?
6. **Polycontribution.** Could multiple causes be interacting simultaneously? Are you artificially forcing a single-cause explanation onto a multi-cause situation?

**The gate rule:** Do not proceed to Options until you have genuinely held multiple hypotheses open and identified what you don't know.

**Example failure without DODAR:** Given a scenario where a SaaS company's churn spikes after three concurrent events (pricing change, competitor launch, UI redesign), a standard LLM response anchors on pricing — the most obviously correlated factor — and builds recommendations around reversing the price increase. DODAR forces the model to hold all three hypotheses open, note that timing correlation is not causation, and identify the diagnostic steps needed to disambiguate.

---

### Phase 2: OPTIONS

**Purpose:** Surface genuine tensions between alternatives. Resist collapsing to a single recommendation.

The second most common failure is **option narrowing**: the model presents a single recommendation (or a binary choice) without acknowledging that other valid paths exist with different trade-off profiles. In aviation, this is the equivalent of the captain making a decision without asking the first officer for alternatives — the CRM principle of "challenge and response" exists precisely to prevent this.

The Options gate counteracts this by requiring:

1. **At least 4 genuinely distinct alternatives.** Options that differ only in degree ("do X slowly" vs. "do X quickly") don't count.
2. **Core tension naming.** What is the fundamental trade-off that makes this decision hard? (Speed vs. safety? Growth vs. runway? Individual vs. collective?) Frame it explicitly.
3. **Risk type separation.** Not all risks are the same. For each option, identify the TYPE of risk: financial, reputational, technical, regulatory, relational, ethical. Don't collapse these into a single "risk" label.
4. **Assumption testing.** For each option, state what must be true for it to work. Which assumptions are validated vs. speculative?
5. **Opportunity cost quantification.** For each option, what do you specifically give up by not choosing the alternatives? Express this concretely.
6. **Hidden stakeholder and constraint surfacing.** Are there binding constraints — another person's risk tolerance, a legal requirement, a deadline — that are not your own preference but must be respected?

**The gate rule:** Do not proceed to Decide until you have surfaced genuine trade-offs between at least four distinct paths.

**Example failure without DODAR:** Given a career decision between staying at a stable job and joining a startup, a standard LLM response frames it as "passion vs. security" and recommends following passion. DODAR forces the model to enumerate distinct paths (stay, leave, negotiate hybrid, delay decision), name the binding constraints (spouse's risk tolerance, family-planning timeline), and quantify what is given up on each path.

---

### Phase 3: DECIDE

**Purpose:** Make the call with transparent, falsifiable reasoning.

Many LLM responses hedge indefinitely ("it depends on your situation") or recommend without explaining why alternatives were rejected. The Decide gate requires commitment — but also requires that the reasoning be visible enough for others to challenge it.

The Decide gate requires:

1. **A clear recommendation.** No hedging unless you genuinely cannot decide — and if so, state what specific information would resolve it.
2. **Justification against alternatives.** Don't just argue for your choice — explain why you are NOT choosing each alternative. What specific weakness tipped the balance?
3. **Binding constraint identification.** What factors had the most weight? Are any imposed by others rather than your own analysis? Give these their proper weight.
4. **Time horizon framing.** Are you optimizing short-term or long-term? Would the decision change if you shifted the horizon by 2x or 5x?
5. **Opportunity cost statement.** State the concrete cost of your decision — the best realistic outcome of the path you're rejecting.
6. **Confidence and falsifiability.** How confident are you (low/medium/high)? What evidence or outcome would prove you wrong? If nothing could change your mind, you're probably overconfident.

**The gate rule:** Do not proceed to Action until you have committed to a recommendation and shown why the alternatives were rejected.

---

### Phase 4: ACTION

**Purpose:** Translate the decision into concrete, sequenced implementation steps.

LLMs frequently produce vague action plans ("monitor the situation," "gather more data," "consult stakeholders"). The Action gate demands specificity:

1. **Concrete steps** with clear owners, inputs, and outputs.
2. **Sequencing and dependencies.** Which steps must happen before others? What is the critical path?
3. **Reversibility mapping.** Which early steps are reversible (low commitment) and which are not (high commitment)? Sequence reversible steps first where possible.
4. **Blockers and prerequisites.** What must be true before each step can begin?
5. **Timeline and resource alignment.** Rough estimates of time and resources required.

---

### Phase 5: REVIEW

**Purpose:** Identify how the plan could fail and what would trigger a course change.

Standard LLM responses treat decisions as final. The Review gate forces explicit self-critique:

1. **At least 3 specific failure modes.** For each: what would trigger it, how would you detect it, and what would you do differently?
2. **Assumption audit.** Which assumptions from Phases 1–4 remain unvalidated? What would happen if they were wrong?
3. **Course-correction triggers.** Under what specific conditions would you abandon this plan and switch to an alternative identified in Phase 2?
4. **Reversibility assessment.** At what point does the plan become irreversible? What is your last off-ramp?

---

## When to Use DODAR

DODAR is not needed for every task. It adds value when:

- **The diagnosis is ambiguous.** Multiple plausible explanations exist, and premature anchoring is a risk.
- **The decision has real trade-offs.** Multiple valid paths exist with different risk/reward profiles — it's not obvious which is best.
- **The stakes are meaningful.** The decision has consequences that are hard or impossible to reverse.
- **You need to trust the reasoning, not just the answer.** When an expert needs to audit or challenge the AI's logic.

DODAR is unnecessary when the answer is straightforward, the stakes are low, or there is genuinely only one viable option.

---

## Using DODAR with AI Models

### As a System Prompt

The simplest integration is a system prompt that instructs the model to follow the five phases. The key is not just naming the phases but enforcing the **gate behaviors** — the specific cognitive work that each phase demands.

A minimal DODAR system prompt:

```
You are an expert analyst using the DODAR reasoning framework.
Structure your response using all five phases in order.
Each phase must be explicitly labeled.

## Phase 1: DIAGNOSE
Hold your diagnosis open. List 3+ competing hypotheses before committing.
Challenge your anchoring. Surface latent assumptions. Map the unknowns.

## Phase 2: OPTIONS
Generate at least 4 genuinely distinct alternatives.
Name the core tension. Quantify opportunity costs for each option.

## Phase 3: DECIDE
Make a clear recommendation. Justify against each alternative.
State your confidence level and what would change your mind.

## Phase 4: ACTION
Define concrete, sequenced steps with dependencies.
Identify which steps are reversible and which are not.

## Phase 5: REVIEW
Identify 3+ failure modes with triggers and detection methods.
Specify conditions for abandoning the plan.
```

### As an Agent Framework

For agentic systems, DODAR can be implemented as a **state machine** where each phase is a distinct step with validation:

1. The agent completes Diagnose and outputs its hypothesis list.
2. A validator checks: Are there 3+ hypotheses? Are assumptions surfaced? If not, loop back.
3. The agent completes Options. Validator checks: Are there 4+ distinct options? Are trade-offs explicit?
4. Continue through Decide, Action, Review with similar gates.

This prevents the agent from skipping phases or producing superficial gate outputs.

### As a Human-AI Collaboration Pattern

DODAR is particularly effective when a human and AI work through a problem together:

1. **AI generates the Diagnose phase** — human reviews and adds hypotheses the AI missed.
2. **AI generates Options** — human identifies constraints or stakeholders the AI overlooked.
3. **Human makes the Decide call** — informed by the AI's analysis but applying their own judgment and risk tolerance.
4. **AI drafts the Action plan** — human validates against real-world constraints.
5. **Both review** — AI identifies analytical failure modes; human identifies practical ones.

---

## What DODAR Does Not Do

- **DODAR does not guarantee correct answers.** It improves the *process* of reasoning, not the *content* of knowledge. A model that lacks domain expertise will produce well-structured but potentially wrong analysis.
- **DODAR does not replace domain expertise.** The framework ensures that reasoning steps are not skipped, but the quality of each step still depends on the model's training and the user's domain knowledge.
- **DODAR is not a universal prompt.** It works best for complex, ambiguous, high-stakes decisions. For simple factual queries, code generation, or creative writing, DODAR adds overhead without benefit.

---

## Benchmark Validation

This framework has been validated through a controlled benchmark comparing DODAR-guided responses against three baselines (zero-shot, chain-of-thought, and length-matched prompting) across multiple models and scenario types.

The benchmark harness, scenarios, raw data, and scoring methodology are open source:
**[github.com/afieldofdreams/dodar](https://github.com/afieldofdreams/dodar)**

For benchmark methodology, results, and analysis, see the accompanying research report.

---

## Contributing

DODAR is an evolving framework. Contributions welcome:

- **New scenarios** — Add YAML files to `backend/data/scenarios/`. Each scenario needs a prompt, expected pitfalls, gold standard elements, and DODAR discriminators.
- **Prompt improvements** — The DODAR template in `backend/dodar/prompts/templates.py` is versioned. Modify the template, bump the version, and re-run the benchmark to measure impact.
- **New model integrations** — Add a runner in `backend/dodar/runners/` implementing the `BaseRunner` interface.
- **Analysis** — Fork the repo, run the benchmark with your own scenarios, and share findings.

---

*DODAR for AI — adapted from aviation Crew Resource Management by [Adam Field](mailto:adam@crox.io).*
