"""Phase 2 experimental conditions — system prompts, user instructions, few-shot examples.

Seven conditions (A-G) from the protocol. Each condition defines:
  - system_prompt: sent as the system message (None for baseline)
  - condition_instruction: prepended to the user message
  - few_shot: whether to include a worked example
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Condition:
    code: str
    name: str
    system_prompt: str | None
    condition_instruction: str
    few_shot: bool = False


# --- Condition definitions (from experiment-conditions-FINAL.json) ---

CONDITION_A = Condition(
    code="A",
    name="Baseline",
    system_prompt=None,
    condition_instruction="",
)

CONDITION_B = Condition(
    code="B",
    name="Zero-Shot CoT (token-matched)",
    system_prompt=(
        "Approach this problem step by step. Think carefully about what is being asked. "
        "Consider all of the relevant information provided. Work through your reasoning "
        "thoroughly and methodically. Examine the problem from multiple angles before "
        "settling on your approach. Take your time to ensure your analysis is complete "
        "and that you have not overlooked any important details. Consider whether your "
        "initial impression might be incomplete or whether there are aspects of the "
        "problem that deserve closer attention. Reflect on whether the information "
        "provided contains any nuances that could affect your answer. Make sure you "
        "have accounted for all the relevant factors before arriving at your conclusion. "
        "Verify that each part of your reasoning supports the next, and that you have "
        "not made any assumptions that are not warranted by the information given. Take "
        "care to ensure that your analysis addresses the full scope of the question. "
        "Check whether your reasoning accounts for all the constraints and conditions "
        "present in the problem. Ensure that each step of your reasoning follows "
        "logically from the previous step and that your analysis does not skip over any "
        "intermediate considerations. Double-check that your reasoning is consistent "
        "throughout and that your final answer follows logically from your analysis. "
        "Then provide your final answer clearly."
    ),
    condition_instruction="Think step by step.",
)

CONDITION_C = Condition(
    code="C",
    name="Phase-Gated Reasoning (PGR) v3 — Late Commitment",
    system_prompt=(
        "Work through these five phases in order. Each phase must add new reasoning, "
        "not restate previous phases.\n\n"
        "1. DIAGNOSE: What exactly is being asked? Identify the constraints that will "
        "determine the answer. State the one thing most likely to cause an error on "
        "this type of problem.\n\n"
        "2. OPTIONS: Identify the two strongest candidate answers. For each, state the "
        "specific evidence for and against. Do not rank them. Treat both as live "
        "possibilities.\n\n"
        "3. DECIDE: Plan how to test both candidates. What calculation or reasoning step "
        "would distinguish between them? Do not select an answer yet.\n\n"
        "4. ACTION: Execute the test from DECIDE on both candidates with equal rigour. "
        "Show the full working for each. Record where evidence favours one over the "
        "other.\n\n"
        "5. REVIEW: Based only on the evidence produced in ACTION, select the answer "
        "that better survived testing. State which specific result decided it. If the "
        "evidence is balanced, state why one edge case tips it.\n\n"
        'State your final answer only after completing all five phases. Do not use the '
        'phrase "final answer" anywhere except the final line.'
    ),
    condition_instruction="Follow the five phases (Diagnose, Options, Decide, Action, Review).",
)

CONDITION_C_PREVIOUS = Condition(
    code="C_previous",
    name="PGR v2 — Early Commitment (deprecated)",
    system_prompt=(
        "Work through these five phases in order. Each phase must add new reasoning, "
        "not restate previous phases.\n\n"
        "1. DIAGNOSE: What exactly is being asked? Identify the constraints that will "
        "determine the answer. State the one thing most likely to cause an error on this "
        "type of problem.\n\n"
        "2. OPTIONS: Identify the most plausible answer and the strongest competing "
        "alternative. For each, state the specific evidence for and against. Do not "
        "simply list all choices.\n\n"
        "3. DECIDE: Commit to one answer. State the single strongest reason it is correct "
        "and the single strongest reason it might be wrong.\n\n"
        "4. ACTION: Verify your chosen answer by working through the problem with that "
        "answer in mind. If the problem involves calculation, show each step. If it "
        "involves reasoning, trace the logical chain.\n\n"
        "5. REVIEW: Look for the specific error you identified in DIAGNOSE. Check whether "
        "the concern you raised in DECIDE actually applies. If you find a genuine error, "
        "change your answer. If not, confirm it.\n\n"
        'State your final answer only after completing all five phases. Do not use the '
        'phrase "final answer" anywhere except the final line.'
    ),
    condition_instruction="Follow the five phases (Diagnose, Options, Decide, Action, Review).",
)

CONDITION_D = Condition(
    code="D",
    name="ReAct (Closed-Book)",
    system_prompt=(
        "When answering this question, use the Thought-Action-Observation reasoning pattern. "
        "Alternate between reasoning about the problem and taking concrete analytical actions.\n\n"
        "For each step:\n\n"
        "Thought: Reason about what you currently know, what you need to figure out, and what "
        "approach to try next.\n\n"
        "Action: Perform a specific analytical action (e.g., identify key information, apply a "
        "formula, evaluate an option, check a constraint, test a hypothesis).\n\n"
        "Observation: State what you learned from that action and whether it changes your "
        "understanding.\n\n"
        "Repeat this Thought-Action-Observation cycle until you have enough information to "
        "answer confidently. Then provide your final answer.\n\n"
        "You may use as many cycles as needed. Each cycle should build on what you learned "
        "in the previous one."
    ),
    condition_instruction="Use the Thought-Action-Observation pattern.",
)

CONDITION_E = Condition(
    code="E",
    name="Step-Back Prompting",
    system_prompt=(
        "When answering this question, use the following two-step approach:\n\n"
        "Step 1 - STEP BACK: Before attempting to answer, ask yourself a higher-level question "
        "about the general principles, concepts, or domain knowledge that are relevant to this "
        "problem. Answer that general question first to establish the foundational knowledge "
        "needed.\n\n"
        "Step 2 - REASON: Using the principles and knowledge you established in Step 1, now "
        "reason through the specific question. Apply the general principles to the particular "
        "details of the problem to arrive at your answer.\n\n"
        "Always complete both steps before giving your final answer."
    ),
    condition_instruction="First step back to identify relevant principles, then reason through the specific problem.",
)

CONDITION_F = Condition(
    code="F",
    name="Shuffled-Phase PGR v2",
    system_prompt=(
        "Work through these five phases in order. Each phase must add new reasoning, "
        "not restate previous phases.\n\n"
        "1. REVIEW: Before answering, identify what type of error is most common on this "
        "kind of problem. What specific mistake should you watch for? Be precise about "
        "the failure mode.\n\n"
        "2. ACTION: Begin working through the problem. Show your reasoning or calculations "
        "step by step. Flag any step where you are uncertain. Identify which parts of your "
        "reasoning are solid and which are tentative.\n\n"
        "3. OPTIONS: Based on your work so far, identify the most plausible answer and the "
        "strongest competing alternative. State the specific evidence for and against each. "
        "Do not simply list all choices.\n\n"
        "4. DIAGNOSE: Now re-examine the problem constraints. Have you addressed all of "
        "them? Is there information you overlooked or an assumption you made that might "
        "be wrong?\n\n"
        "5. DECIDE: Commit to your final answer. State the single strongest reason for "
        "your choice and the single strongest reason against it.\n\n"
        'State your final answer only after completing all five phases. Do not use the '
        'phrase "final answer" anywhere except the final line.'
    ),
    condition_instruction="Follow the five phases (Review, Action, Options, Diagnose, Decide).",
)

CONDITION_G = Condition(
    code="G",
    name="Few-Shot CoT",
    system_prompt="Think through this problem step by step. Reason carefully before committing to an answer.",
    condition_instruction="",  # Built dynamically with worked example
    few_shot=True,
)

CONDITION_H = Condition(
    code="H",
    name="Anti-Anchoring PGR",
    system_prompt=(
        "Work through these five phases in order. Each phase must add new reasoning, "
        "not restate previous phases.\n\n"
        "1. DIAGNOSE: What type of problem is this and what are the constraints? What "
        "mistake is most common on this type of problem? Do not consider possible answers "
        "yet.\n\n"
        "2. OPTIONS: Identify the two strongest candidate answers. For each, state the "
        "specific evidence for and against. Treat both as equally plausible until all "
        "evidence is weighed.\n\n"
        "3. DECIDE: State your best answer. Rate your confidence 1-10. Name the one "
        "piece of evidence that would make you switch.\n\n"
        "4. ACTION: Test whether your chosen answer survives scrutiny. If calculation, "
        "show each step. If reasoning, trace the logical chain. Flag any point where "
        "evidence cuts against your choice.\n\n"
        "5. REVIEW: Argue the strongest case that your answer is WRONG. Present the full "
        "case for the alternative as if you were opposing counsel. After making this "
        "argument, decide: switch or stand.\n\n"
        'State your final answer only after completing all five phases. Do not use the '
        'phrase "final answer" anywhere except the final line.'
    ),
    condition_instruction="Follow the five phases (Diagnose, Options, Decide, Action, Review).",
)

# Registry
CONDITIONS: dict[str, Condition] = {
    "A": CONDITION_A,
    "B": CONDITION_B,
    "C": CONDITION_C,
    "C_previous": CONDITION_C_PREVIOUS,
    "D": CONDITION_D,
    "E": CONDITION_E,
    "F": CONDITION_F,
    "G": CONDITION_G,
    "H": CONDITION_H,
}

# Default conditions for new runs (C_previous available but not default)
BENCHMARK_CONDITION_CODES = ["A", "B", "C", "D", "E", "F", "G", "H"]

# All conditions including deprecated
ALL_CONDITION_CODES = ["A", "B", "C", "C_previous", "D", "E", "F", "G", "H"]


# --- Few-shot worked examples for Condition G ---

# Rotation map: test source -> example domain
# Supports both v1 sources ("MedQA-USMLE") and v2 sub-sources ("BBH/causal_judgement")
EXAMPLE_ROTATION: dict[str, str] = {
    # v1 exact sources
    "MedQA-USMLE": "mathematical_reasoning",
    "MMLU": "science_reasoning",
    "GSM8K": "diverse_reasoning",
    "BBH": "professional_reasoning",
    "ARC-Challenge": "clinical_reasoning",
    # v2 sub-sources (BBH/*)
    "BBH/causal_judgement": "professional_reasoning",
    "BBH/logical_deduction_five_objects": "professional_reasoning",
    "BBH/web_of_lies": "professional_reasoning",
    "BBH/snarks": "mathematical_reasoning",
    "BBH/disambiguation_qa": "clinical_reasoning",
    "BBH/navigate": "mathematical_reasoning",
    # v2 sub-sources (MMLU/*)
    "MMLU/professional_law": "science_reasoning",
    "MMLU/professional_accounting": "science_reasoning",
    "MMLU/formal_logic": "clinical_reasoning",
    "MMLU/conceptual_physics": "diverse_reasoning",
    "MMLU/professional_medicine": "science_reasoning",
    # Category-based fallbacks
    "clinical_reasoning": "mathematical_reasoning",
    "professional_reasoning": "science_reasoning",
    "mathematical_reasoning": "diverse_reasoning",
    "diverse_reasoning": "professional_reasoning",
    "science_reasoning": "clinical_reasoning",
}

WORKED_EXAMPLES: dict[str, str] = {
    "clinical_reasoning": (
        "EXAMPLE QUESTION: A 65-year-old man presents with sudden onset of slurred speech "
        "and right-sided weakness that started 2 hours ago. He has a history of atrial "
        "fibrillation and takes warfarin. His INR today is 1.4. CT head shows no haemorrhage. "
        "What is the most appropriate immediate management?\n"
        "A: Administer IV alteplase (thrombolysis)\n"
        "B: Increase warfarin dose\n"
        "C: Start aspirin 300mg\n"
        "D: Arrange urgent MRI brain\n\n"
        "EXAMPLE ANSWER: Let me work through this carefully.\n\n"
        "The presentation is acute onset neurological deficit (slurred speech, right-sided "
        "weakness) within a 2-hour window. This is a clinical stroke presentation.\n\n"
        "Key factors to consider:\n"
        "- 2-hour onset puts him within the thrombolysis window (typically 4.5 hours)\n"
        "- CT shows no haemorrhage, so this is likely ischaemic\n"
        "- He has AF, which is a major risk factor for cardioembolic stroke\n"
        "- His INR is 1.4, which is subtherapeutic (target typically 2-3 for AF)\n"
        "- The subtherapeutic INR may explain why he had a stroke despite being on warfarin\n\n"
        "Now evaluating each option:\n"
        "- A (IV alteplase): Thrombolysis. Within time window, CT excludes haemorrhage. "
        "Guidelines generally consider thrombolysis if INR < 1.7.\n"
        "- B (Increase warfarin): Addresses long-term problem but nothing for acute stroke.\n"
        "- C (Aspirin 300mg): Standard if thrombolysis contraindicated, but thrombolysis is an option here.\n"
        "- D (Urgent MRI): Would delay treatment. CT already excluded haemorrhage.\n\n"
        "Since he is within the thrombolysis window, CT excludes haemorrhage, and INR 1.4 is "
        "below the 1.7 threshold, IV alteplase is most appropriate.\n\n"
        "FINAL ANSWER: A"
    ),
    "professional_reasoning": (
        "EXAMPLE QUESTION: A company discovers that one of its senior managers has been approving "
        "contracts with a vendor owned by their spouse, without disclosing this relationship. "
        "The contracts were all at market rate. Which best describes the legal situation?\n"
        "A: No violation occurred because the contracts were at market rate\n"
        "B: A breach of fiduciary duty occurred regardless of pricing\n"
        "C: This constitutes fraud because of the concealment\n"
        "D: The company can only act if it suffered financial loss\n\n"
        "EXAMPLE ANSWER: Let me think through each element.\n\n"
        "The key facts are: (1) undisclosed conflict of interest, (2) related-party transactions, "
        "(3) contracts at market rate, (4) the manager had approval authority.\n\n"
        "A fiduciary duty requires loyalty and disclosure. The core issue is not whether the "
        "company lost money, but whether the manager fulfilled their duty to disclose.\n\n"
        "Evaluating each option:\n"
        "- A: Market rate pricing is relevant to damages but does not eliminate the duty to disclose.\n"
        "- B: Fiduciary duty includes loyalty and full disclosure. The breach is the concealment, "
        "not the price.\n"
        "- C: Fraud requires intentional deception for personal gain. Higher bar than fiduciary breach.\n"
        "- D: Financial loss is relevant to damages, not to whether a breach occurred.\n\n"
        "The strongest answer is B.\n\n"
        "FINAL ANSWER: B"
    ),
    "mathematical_reasoning": (
        "EXAMPLE QUESTION: A bakery makes 120 cupcakes every morning. They sell 60% by lunchtime "
        "and 25% of the remaining in the afternoon. At the end of the day, they donate unsold "
        "cupcakes. If they operate 6 days a week, how many cupcakes do they donate each week?\n\n"
        "EXAMPLE ANSWER: Let me work through this step by step.\n\n"
        "Starting cupcakes per day: 120\n"
        "Sold by lunchtime: 60% of 120 = 72 cupcakes\n"
        "Remaining after lunch: 120 - 72 = 48 cupcakes\n"
        "Sold in afternoon: 25% of 48 = 12 cupcakes\n"
        "Remaining after afternoon: 48 - 12 = 36 cupcakes\n\n"
        "So 36 cupcakes donated each day.\n"
        "Per week (6 days): 36 x 6 = 216 cupcakes\n\n"
        "Verify: 120 - 72 = 48. 48 x 0.25 = 12. 48 - 12 = 36. 36 x 6 = 216. Checks out.\n\n"
        "FINAL ANSWER: 216"
    ),
    "diverse_reasoning": (
        "EXAMPLE QUESTION: Alice, Bob, and Carol each have a different favourite colour: red, "
        "blue, or green. Alice says: 'My favourite colour is not red.' Bob says: 'My favourite "
        "colour is not blue.' Carol says: 'My favourite colour is not red.' If exactly one is "
        "lying, who likes which colour?\n\n"
        "EXAMPLE ANSWER: Let me reason through this systematically.\n\n"
        "There are three statements and exactly one is a lie. Let me test each possibility.\n\n"
        "Case 1: Alice is lying (her colour IS red). Then Alice=red. Bob's statement is true "
        "(not blue), so Bob=green. Carol's statement is true (not red), so Carol=blue. All "
        "different. Valid.\n\n"
        "Case 2: Bob is lying (his colour IS blue). Then Bob=blue. Alice's statement is true "
        "(not red), so Alice=green or blue. Since Bob=blue, Alice=green. Carol's statement is "
        "true (not red), so Carol=red. But Carol said 'not red' — that's two liars. Invalid.\n\n"
        "Case 3: Carol is lying (her colour IS red). Then Carol=red. Alice is true (not red), "
        "Bob is true (not blue), so Bob=green. Alice=blue. All different. Valid.\n\n"
        "Two valid solutions. Case 1: Alice=red, Bob=green, Carol=blue.\n\n"
        "FINAL ANSWER: Alice likes red (she lied), Bob likes green, Carol likes blue"
    ),
    "science_reasoning": (
        "EXAMPLE QUESTION: A student places a metal spoon in a cup of hot water. After one "
        "minute, the handle feels warm. Which best explains this?\n"
        "A: Heat energy was created in the spoon by the water\n"
        "B: Cold energy moved from the spoon into the water\n"
        "C: Heat energy was transferred through the metal by conduction\n"
        "D: The spoon absorbed light energy from the water\n\n"
        "EXAMPLE ANSWER: The observation is that a metal spoon's handle gets warm when the "
        "bowl end is in hot water. I need to identify the mechanism.\n\n"
        "Key physics: metal is a good thermal conductor. Heat transfers through solid materials "
        "by conduction.\n\n"
        "Evaluating each option:\n"
        "- A: Heat is not created. It is transferred. Violates conservation of energy. Incorrect.\n"
        "- B: No such thing as 'cold energy.' Heat moves from hot to cold. Incorrect.\n"
        "- C: Heat transfers from hot water to spoon, then through metal by conduction. Correct.\n"
        "- D: Light energy not involved. The transfer is thermal. Incorrect.\n\n"
        "FINAL ANSWER: C"
    ),
}


def get_worked_example(source: str, category: str) -> str:
    """Get the worked example for a task, based on its source or category.

    Uses the rotation map: a MedQA task gets a math example, etc.
    Handles v2 sub-sources like "BBH/causal_judgement" by trying the full
    source first, then the prefix before "/".
    """
    # Try exact source match first
    example_key = EXAMPLE_ROTATION.get(source)
    # Try prefix (e.g. "BBH/snarks" -> "BBH")
    if not example_key and "/" in source:
        example_key = EXAMPLE_ROTATION.get(source.split("/")[0])
    # Try category
    if not example_key and category:
        example_key = EXAMPLE_ROTATION.get(category)
    # Fallback: mathematical reasoning (most neutral)
    if not example_key:
        example_key = "mathematical_reasoning"
    return WORKED_EXAMPLES[example_key]


# --- Universal answer format suffix ---

UNIVERSAL_SUFFIX_MC = (
    "\n\nShow your reasoning, then state your final answer clearly on its own line "
    "in the format:\nFINAL ANSWER: [letter]"
)

UNIVERSAL_SUFFIX_NUMERIC = (
    "\n\nShow your reasoning, then state your final answer clearly on its own line "
    "in the format:\nFINAL ANSWER: [number]"
)

UNIVERSAL_SUFFIX_EXACT = (
    "\n\nShow your reasoning, then state your final answer clearly on its own line "
    "in the format:\nFINAL ANSWER: [answer]"
)


def get_universal_suffix(answer_type: str) -> str:
    if answer_type == "multiple_choice":
        return UNIVERSAL_SUFFIX_MC
    elif answer_type == "numeric_exact":
        return UNIVERSAL_SUFFIX_NUMERIC
    else:
        return UNIVERSAL_SUFFIX_EXACT
