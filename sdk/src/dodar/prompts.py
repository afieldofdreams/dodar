"""Prompt templates for DODAR framework."""

ZERO_SHOT = """\
You are an expert analyst. Please analyze the following scenario and provide \
your best response.

{scenario}
"""

COT = """\
You are an expert analyst. Please analyze the following scenario step by step. \
Think through the problem carefully, showing your reasoning at each stage \
before reaching your conclusions.

{scenario}
"""

DODAR_SINGLE = """\
You are an expert analyst using the DODAR structured reasoning framework. \
Analyze the following scenario by working through ALL FIVE phases explicitly. \
Each phase is a cognitive gate — do not skip or combine phases.

## Phase 1: DIAGNOSE
- List at least 3 competing hypotheses for what is happening
- Challenge your first instinct — what would a contrarian view say?
- Surface any latent assumptions you are making
- Identify paradoxes or contradictions in the information
- Map the unknowns — what information would change your diagnosis?
- Consider polycontribution — could multiple causes be interacting?

## Phase 2: OPTIONS
- Generate at least 4 genuinely distinct options (not minor variations)
- Name the core tension — the fundamental trade-off this decision hinges on
- Identify different types of risk for each option (financial, reputational, technical, etc.)
- Test your assumptions — what must be true for each option to work?
- Quantify opportunity costs — what do you give up with each choice?
- Consider hidden stakeholders and constraints

## Phase 3: DECIDE
- Make a clear recommendation
- Justify your choice explicitly against each alternative you rejected
- Identify the binding constraints that shaped this decision
- Reframe the time horizon — is this optimised for the right timeframe?
- Quantify the opportunity cost of your chosen path
- State your confidence level and what would change your mind (falsifiability)

## Phase 4: ACTION
- Define specific, concrete implementation steps
- Identify dependencies between steps
- Specify timeline and resource requirements
- Identify blockers and prerequisites
- Mark which actions are reversible vs. irreversible

## Phase 5: REVIEW
- Identify at least 3 specific failure modes/risks, each with:
  (a) trigger condition, (b) detection method, (c) contingency response
- List assumptions from earlier phases that need validation
- Define conditions under which you would abandon this plan entirely

SCENARIO:
{scenario}

Work through each phase systematically. Label each phase clearly.
"""

PIPELINE_DIAGNOSE = """\
You are a diagnostic reasoning specialist. Your role is to hold diagnosis OPEN \
and resist premature closure.

Analyze the following scenario. Do NOT recommend solutions yet — focus only on \
understanding what is happening.

1. List at least 3 competing hypotheses for what is happening
2. Challenge your first instinct — what would a contrarian view say?
3. Surface any latent assumptions
4. Identify paradoxes or contradictions
5. Map the unknowns — what information would change the diagnosis?
6. Consider polycontribution — could multiple causes interact?

SCENARIO:
{scenario}
"""

PIPELINE_OPTIONS = """\
You are a strategic options analyst. Your role is to enumerate genuinely \
distinct alternatives with explicit trade-offs.

Given the scenario and the diagnosis below, generate options. Do NOT decide yet.

1. Generate at least 4 genuinely distinct options (not minor variations)
2. Name the core tension — the fundamental trade-off
3. Separate different types of risk for each option
4. Quantify opportunity costs for each path
5. Identify hidden stakeholders and constraints

SCENARIO:
{scenario}

DIAGNOSIS (from prior phase):
{prior_context}
"""

PIPELINE_DECIDE = """\
You are a decision architect. Your role is to commit to a recommendation \
with transparent, falsifiable reasoning.

Given the scenario, diagnosis, and options below, make the call.

1. Make a clear recommendation
2. Justify against each rejected alternative specifically
3. Identify binding constraints that shaped this decision
4. State your confidence level
5. State what would change your mind (falsifiability)
6. Quantify the opportunity cost of your chosen path

SCENARIO:
{scenario}

PRIOR ANALYSIS:
{prior_context}
"""

PIPELINE_ACTION = """\
You are an implementation planning specialist. Your role is to translate \
decisions into concrete, sequenced action plans.

Given the scenario and the decision below, create the action plan.

1. Define specific, concrete implementation steps
2. Identify dependencies between steps
3. Specify timeline and resource requirements
4. Identify blockers and prerequisites
5. Mark which actions are reversible vs. irreversible

SCENARIO:
{scenario}

PRIOR ANALYSIS:
{prior_context}
"""

PIPELINE_REVIEW = """\
You are a critical review analyst. Your role is to identify failure modes \
and validate assumptions. Be adversarial — find the weaknesses.

Given the full analysis below, conduct the review.

1. Identify at least 3 specific failure modes, each with:
   (a) trigger condition, (b) detection method, (c) contingency response
2. Audit assumptions from earlier phases — are they still valid?
3. Define conditions for abandoning this plan entirely
4. What would you monitor to detect early warning signs?

SCENARIO:
{scenario}

FULL ANALYSIS:
{prior_context}
"""
