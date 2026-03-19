"""Prompt templates for each experimental condition."""

# Bump this when you change DODAR_TEMPLATE or any condition template.
# Runs are tagged with this version so dashboard results can be separated.
PROMPT_VERSION = "v2"

ZERO_SHOT_TEMPLATE = """\
You are an expert analyst. Please analyze the following scenario and provide \
your best response.

{prompt_text}
"""

COT_TEMPLATE = """\
You are an expert analyst. Please analyze the following scenario step by step. \
Think through the problem carefully, showing your reasoning at each stage \
before reaching your conclusions.

{prompt_text}

Think step by step.
"""

LENGTH_MATCHED_PREFIX = """\
You are an expert analyst. Please analyze the following scenario thoroughly.

Consider all relevant factors. Examine the situation from multiple angles. \
Evaluate the strengths and weaknesses of different approaches. Think about \
short-term and long-term consequences. Consider the perspectives of all \
parties involved. Reflect on potential risks and mitigation strategies. \
Provide a comprehensive and well-reasoned response.

Ensure your response is detailed and covers the situation comprehensively. \
Take your time to think through all aspects of the problem. Your analysis \
should demonstrate depth of understanding and practical applicability.
"""

LENGTH_MATCHED_SUFFIX = """
Provide a thorough and detailed analysis.
"""

# Additional filler sentences for length-matching (added/removed to hit token target)
LENGTH_MATCHED_FILLERS = [
    "Consider both immediate and long-term implications of each possible course of action.",
    "Weigh the evidence carefully before drawing conclusions.",
    "Identify any assumptions underlying your analysis and assess their validity.",
    "Think about what information might be missing and how that affects your assessment.",
    "Consider edge cases and unusual circumstances that might affect the outcome.",
    "Evaluate how different stakeholders might perceive the situation differently.",
    "Assess the reversibility of potential actions and their downstream effects.",
    "Consider whether historical precedents or analogies inform your analysis.",
    "Think about both quantitative and qualitative factors in your assessment.",
    "Evaluate the confidence level of your conclusions and acknowledge uncertainties.",
    "Consider the opportunity costs of each potential course of action.",
    "Assess whether the framing of the problem might be misleading or incomplete.",
    "Think about second-order effects that might not be immediately obvious.",
    "Evaluate whether the available evidence supports multiple competing interpretations.",
    "Consider how time pressure or resource constraints affect the decision landscape.",
]

DODAR_TEMPLATE = """\
You are an expert analyst using the DODAR reasoning framework. DODAR stands \
for Diagnose, Options, Decide, Action, Review. You MUST structure your \
response using all five phases in order. Each phase must be explicitly labeled.

{prompt_text}

Now analyze this scenario using the DODAR framework. Complete each phase \
before moving to the next.

## Phase 1: DIAGNOSE
HOLD YOUR DIAGNOSIS OPEN. Do NOT commit to a single cause or interpretation.

Your task is to resist the pull of the most obvious explanation. Follow these steps:
1. **List 3+ competing hypotheses** for what is happening, ranked by plausibility. \
Do not stop at the first plausible cause.
2. **Challenge your anchoring.** What is the most obvious explanation — and why \
might it be wrong? What would a contrarian diagnostician consider? If risk factors \
or prior patterns make one cause seem obvious, explicitly question whether you are \
anchoring on familiarity rather than evidence.
3. **Surface latent assumptions.** What are you assuming that has not been stated? \
Is there a correlation being treated as causation? Is a temporal sequence being \
treated as a causal sequence? Name the assumption explicitly.
4. **Identify paradoxes and contradictions.** Does any evidence point in the \
opposite direction from the leading hypothesis? If so, what does that tell you?
5. **Map the unknowns.** What specific information is missing that would \
disambiguate between your hypotheses? What diagnostic test, question, or data \
point would most change your assessment?
6. **Consider polycontribution.** Could multiple causes be interacting or \
compounding simultaneously? Are you artificially forcing a single-cause explanation \
onto a multi-cause situation?

Do NOT proceed to Phase 2 until you have genuinely held multiple hypotheses open.

## Phase 2: OPTIONS
Generate genuinely distinct alternatives — not minor variations of the same approach.

Your task is to surface real tensions and trade-offs, not just list options. Follow these steps:
1. **Enumerate at least 4 distinct options**, including at least one that is \
unconventional, counterintuitive, or that most people would dismiss too quickly. \
Options that differ only in degree (e.g., "do X slowly" vs. "do X quickly") do not count.
2. **Name the core tension.** What is the fundamental trade-off that makes this \
decision hard? (e.g., speed vs. safety, growth vs. runway, individual vs. collective). \
Frame the tension explicitly — do not let it remain implicit.
3. **Separate different types of risk.** Not all risks are the same. For each option, \
identify what TYPE of risk it carries (e.g., financial, reputational, technical, \
regulatory, relational, ethical). Do not collapse different risk types into a single \
"risk" label.
4. **Test your assumptions.** For each option, state what must be true for it to \
work. Which of these assumptions are validated vs. speculative? Is there an option \
you are dismissing because of an untested assumption about what is possible or \
acceptable?
5. **Quantify opportunity costs.** For each option, what do you specifically give up \
by not choosing the alternatives? Express this concretely, not abstractly.
6. **Surface hidden stakeholders and constraints.** Are there binding constraints \
(e.g., another person's risk tolerance, a legal requirement, a timeline) that are \
not your own preference but must be respected? Are there stakeholders whose \
perspective changes the option landscape?

## Phase 3: DECIDE
Make the call — but make your reasoning transparent and falsifiable.

Your task is not just to choose, but to show exactly WHY you chose and what would \
change your mind. Follow these steps:
1. **State your recommendation clearly.** Do not hedge with "it depends" unless you \
genuinely cannot decide — and if so, state what specific information would resolve it.
2. **Justify against specific alternatives.** Do not just argue for your choice — \
explain why you are NOT choosing each of the other options. What is the specific \
weakness of each alternative that tipped the balance?
3. **Name the binding constraints.** What factors had the most weight in your \
decision? Are any of these constraints imposed by others (e.g., a spouse's risk \
tolerance, a regulatory deadline, a budget limit) rather than your own analysis? \
Give these constraints their proper weight — do not override them with your \
analytical preference.
4. **Reframe the time horizon.** Are you optimizing for the short term or the long \
term? Would your decision change if you shifted the time horizon by 2x or 5x? \
State explicitly what time horizon you are optimizing for and why.
5. **Quantify what you are giving up.** State the concrete opportunity cost of your \
decision. What is the best realistic outcome of the path you are rejecting?
6. **State your confidence and falsifiability.** On a scale of low/medium/high, \
how confident are you? What specific evidence or outcome would prove your decision \
wrong? If nothing could change your mind, you are probably overconfident.

## Phase 4: ACTION
Define the concrete implementation steps. Be specific about sequencing and \
dependencies. Identify which steps are reversible and which are not. Note any \
blockers or prerequisites. Include a rough timeline and resource requirements \
where applicable.

## Phase 5: REVIEW
Critically evaluate your own reasoning. Identify at least 3 specific failure \
modes or risks in your plan. For each, state: (a) what would trigger it, \
(b) how you would detect it, (c) what you would do differently. Flag any \
assumptions you made that should be validated. Specify conditions under which \
you would abandon this plan and switch to an alternative.
"""
