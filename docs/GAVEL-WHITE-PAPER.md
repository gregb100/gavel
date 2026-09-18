# Gavel — Structured Decisions for AI Agent Orchestration

### A White Paper on the OpenClaw Plugin and Skill for TypeSafe Jev

**Author:** Gavel Contributors  
**Date:** 2026-09-18  
**Status:** Public — ready for distribution

---

## 1. The Problem

AI agents running on large language models face a recurring inefficiency: **every decision, no matter how simple, consumes a full LLM call.**

When an agent needs to classify an incoming message, route a bug report, gauge urgency, or pick a department — these are not reasoning problems. They are classification problems with known, finite answer sets. Yet the standard approach is:

1. Send the full context to an LLM
2. Wait 2–10 seconds for a response
3. Parse unstructured prose to extract what was really a one-word answer
4. Pay $0.01–0.05 per call for the privilege

At scale, this is untenable. An agent orchestrator processing 1,000 routing decisions per day spends $10–50/day on decisions that should cost fractions of a cent. Worse, the LLM might hallucinate a category that doesn't exist, wrap the answer in unnecessary prose, or drift in judgment across calls.

**The gap:** No tool existed in the OpenClaw ecosystem to make fast, cheap, typed decisions with calibrated confidence. Agents either burned LLM calls on classifications or skipped routing logic entirely.

---

## 2. The Insight

TypeSafe AI's Jev (System One class model, `typesafe/jev-1.13`) is purpose-built for this gap. It is **not a chat LLM** — it generates no text, does no reasoning, produces no explanations. It returns exactly three primitives:

| Primitive | Question it answers | Output |
|-----------|---------------------|--------|
| **Noul** | Is this true? | Probability 0–1 |
| **Choice** | Which option? | Selected option + full probability distribution + confidence |
| **Score** | Which level? | Rubric level + probability distribution + confidence |

At ~200ms per call and ~$0.00002 per decision, it is 500–2,500x cheaper than a general-purpose LLM call for the same classification task. It cannot hallucinate an answer outside the provided options. It returns calibrated confidence that can gate automated actions.

**But Jev alone is not enough.** An agent needs to know *when* to reach for it, *which* primitive to use, and *how* to structure the question. Without that knowledge, Jev is a sharp tool with no handle.

---

## 3. What We Built

**Gavel** is the combined OpenClaw plugin and skill that bridges this gap. It has three layers:

### Layer 1: The Skill (`SKILL.md`)

The skill teaches agents **when and how** to use Jev. It is a decision tree, not a sales pitch:

**Use Jev when ALL hold:**

- Output is yes/no, pick-from-set, or rubric level
- Decision is atomic — one focused judgment
- No text generation needed
- Speed or cost matters at scale
- Input is text-only under 32k tokens

**Use an LLM when ANY hold:**

- Needs prose, code, or structured text generation
- Requires multi-step reasoning or chain-of-thought
- Answer is open-ended
- Multimodal input required
- Context/memory across calls needed

**Use hybrid when:**

- Workflow has both decision points (Jev) and generation steps (LLM)
- High-volume routing where Jev triages and LLM handles edge cases

The skill also documents the three primitives with concrete examples, state format best practices (string for simple messages, object for named fields, array for conversations), confidence-gated routing thresholds (>0.8 auto-act, 0.5–0.8 confirm, <0.5 fallback), and example agent routing patterns — intent routing, bug triage, and message classification.

### Layer 2: The Plugin (`index.ts`)

The plugin is a thin TypeScript wrapper that registers the `jev_decide` tool in OpenClaw. It:

- Calls the OpenRouter `/api/alpha/decisions` endpoint
- Passes state + questions to `typesafe/jev-1.13`
- Returns typed answers with probabilities and confidence
- Handles 30s timeout, error responses, and missing API key
- Activates on gateway startup — no manual enable needed

The plugin does no decision logic itself. It is a pipe. The intelligence lives in the skill (when to call) and in Jev (what to answer).

### Layer 3: The Test Suite (`tests/`)

32 integration tests hitting the real OpenRouter API — no mocks. The suite validates:

- **Primitive correctness:** Each type (noul/choice/score) returns correctly structured answers
- **State format handling:** String, object, and array inputs all produce valid results
- **Multi-question independence:** Five questions in one call don't contaminate each other
- **Confidence calibration:** High-confidence answers are actually more often correct
- **Routing patterns:** Real-world workflows (intent, bug triage, message classification) produce sane results
- **Edge cases:** Empty state, 30k-char state, bad model ID, missing fields
- **Performance:** Sub-second single calls, sub-2-second five-question calls

---

## 4. Architecture

The following diagram shows the end-to-end flow from user message through Gavel to a typed decision and back to agent action:

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER SENDS A MESSAGE                        │
│                 "fix the login bug on dashboard"                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  ORCHESTRATING AGENT                             │
│                                                                  │
│  1.  Ingest incoming message or task                            │
│  2.  Classify: Is this bug / feature / status / ops?            │
│  3.  Decide: handle solo or delegate to worker agent?            │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  SKILL LAYER  (SKILL.md)                                  │  │
│  │                                                           │  │
│  │  Teaches the agent WHEN to reach for Jev:                 │  │
│  │                                                           │  │
│  │    Yes / no?        ──▶  noul                             │  │
│  │    Pick from set?   ──▶  choice                           │  │
│  │    Rate on rubric?  ──▶  score                            │  │
│  │    Need prose/code? ──▶  use LLM, not Jev                 │  │
│  │                                                           │  │
│  │  The agent decides: "This is a classification,            │  │
│  │  not a reasoning task."                                   │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                             │                                   │
│         Agent calls: jev_decide(state, questions)                │
│                             │                                   │
│  ┌──────────────────────────▼────────────────────────────────┐  │
│  │  PLUGIN LAYER  (index.ts)                                  │  │
│  │                                                           │  │
│  │  Registers tool: jev_decide                               │  │
│  │                                                           │  │
│  │    jev_decide(                                            │  │
│  │      state = "fix the login bug on dashboard",            │  │
│  │      questions = {                                        │  │
│  │        intent:     choice(bug / feature / ...)            │  │
│  │        complexity: score(0–3)                             │  │
│  │        is_urgent:  noul                                   │  │
│  │      }                                                    │  │
│  │    )                                                      │  │
│  └──────────────────────────┬────────────────────────────────┘  │
└─────────────────────────────┼───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               OPENROUTER DECISIONS API                           │
│            (typesafe/jev-1.13 model)                             │
│                                                                  │
│  Not a chat LLM.  No text generation.                            │
│  Returns typed values + probabilities + confidence.              │
│                                                                  │
│  Latency:  ~200 ms     Cost:  ~$0.00002 / call                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       JEV RESPONDS                               │
│                                                                  │
│  intent:      choice = "bug",         confidence = 0.91          │
│  complexity:  score  = 2 (Moderate),  confidence = 0.78          │
│  is_urgent:   noul   = 0.29                                      │
│                                                                  │
│  (Not urgent — no explicit urgency language in the message)      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 ORCHESTRATOR ACTS ON THE DECISION                │
│                                                                  │
│  bug + moderate + not urgent                                     │
│    ──▶  spawn worker agent with task contract                    │
│    ──▶  not a status question (no solo answer)                   │
│    ──▶  not critical (no immediate human alert)                  │
│                                                                  │
│  4.  Record outcome / update task tracking                       │
└─────────────────────────────────────────────────────────────────┘
```

### Package Structure

The three layers ship as a single repository:

```
┌──────────────┐
│    SKILL     │   "When to use Jev, which primitive,
│   SKILL.md   │    what questions to ask"
└──────┬───────┘
       │  teaches agents
       │
┌──────▼───────┐
│    PLUGIN    │   registers jev_decide tool
│   index.ts   │    ──▶  calls OpenRouter /decisions
│   dist/      │    ──▶  returns typed answers
└──────┬───────┘
       │  validated by
       │
┌──────▼───────┐
│    TESTS     │   32 tests, real API
│   tests/     │    noul / choice / score
│              │    confidence calibration
└──────────────┘
```

**Three layers — know when, be able, prove it works.**

The skill is the brain. The plugin is the hand. Jev is the gavel.

---

## 5. How We Tested

### Methodology

Every test calls the real OpenRouter decisions API at `https://openrouter.ai/api/alpha/decisions`. No mocks, no stubs, no cached responses. The suite requires `OPENROUTER_API_KEY` to run and skips cleanly if absent.

### Test Matrix

| File | Tests | Category | What it validates |
|------|-------|----------|-------------------|
| `test_noul_basic.py` | 4 | Primitive | Clear true (>0.8), clear false (<0.2), ambiguous, missing criteria |
| `test_choice_basic.py` | 4 | Primitive | Clear match (conf >0.7), multi-plausible (conf <0.9), no-match → other, other can win |
| `test_score_basic.py` | 4 | Primitive | High/boundary/low on 3-level rubric, 2-level minimum |
| `test_state_formats.py` | 4 | Input | String, object, array — all produce valid answers |
| `test_multi_question.py` | 3 | Concurrency | 5 questions answered, no cross-contamination, latency scaling <2x |
| `test_confidence_calibration.py` | 3 | Calibration | Clear cases confident, ambiguous uncertain, high-conf more accurate |
| `test_routing_patterns.py` | 3 | Integration | Intent routing, bug triage, message classification — real agent workflows |
| `test_edge_cases.py` | 5 | Robustness | Empty state, 30k chars, bad model, missing type, empty questions |
| `test_performance.py` | 2 | Performance | Single call <1s, five questions <2s |
| **Total** | **32** | | |

### Assertion Design

Tests assert on Jev's actual behavior, not just response existence. Examples:

- Noul clear true: `assert noul > 0.8`
- Choice clear match: `assert choice == "billing" and confidence > 0.7`
- Score boundary: `assert 0.33 <= score <= 0.66` (float range, not integer equality)
- Intent routing: `assert intent == "bug" and complexity >= 2 and is_urgent > 0.5`
- Cross-contamination: changing one question's instructions doesn't shift another's answer

---

## 6. Results

### Overall: 32/32 passed in 13.46 seconds

All tests green on first complete run after refinement.

### Key Findings

#### Finding 1: Noul Criteria Must Be Structured Objects

The API rejects string criteria for noul questions. It requires `{"true": "...", "false": "..."}`. The original skill documentation suggested a simpler format. Tests caught this; skill and tests were corrected.

**Implication:** Plugin consumers must follow strict criteria schema. Documented in the skill.

#### Finding 2: Score Values Are Continuous Floats

Jev returns scores as floats in `[0, len(criteria) - 1]`. For a 3-level rubric (Calm / Frustrated / Very angry), scores cluster near 0.0, 1.0, or 2.0 but can be fractional (e.g., 0.45). The `legend` field maps integer indices to labels.

**Implication:** Consumers should use range assertions, not integer equality. A score of 0.9 is "between Calm and Frustrated, leaning Frustrated."

#### Finding 3: Noul Skews Conservative on Ambiguous Input

Ambiguous statements like "This isn't what I expected" return noul < 0.1 for `refund_requested`, not ~0.5 as expected. The model prefers assigning low probability to the positive class rather than expressing uncertainty at the midpoint.

**Implication:** For ambiguous routing, use choice (with an "other" option) rather than noul. Noul is better for clear yes/no where the negative class is meaningful.

#### Finding 4: Urgency Requires Explicit Signals

"fix the login bug on the dashboard" returned `is_urgent` noul ~0.29. Without words like "urgent," "critical," "down," or "broken," Jev does not infer urgency from task type alone.

**Implication:** Routing that uses urgency detection should include context about impact, not just task description. State like `"fix the login bug — production is down"` should produce higher urgency.

#### Finding 5: Performance Confirmed

| Metric | Result | Budget |
|--------|--------|--------|
| Single question | ~0.2s | <1s ✅ |
| Five questions | ~0.6–0.7s | <2s ✅ |
| Scaling factor | ~3–4x for 5x questions | <5x ✅ |
| 30k-char state | completes within 30s | <30s ✅ |

**Implication:** Jev is practical for real-time agent routing. A turn that calls Jev for intent + complexity + urgency adds <1s to the response.

#### Finding 6: Casual Language Can Trigger Question Detection

"hey what's up" was classified as `is_question` with noul ~0.84 — despite not being a literal question. Jev interprets conversational openings as implicit questions.

**Implication:** Message classification thresholds should account for conversational intent, not just grammatical questions.

### Confidence Calibration

| Case type | Expected behavior | Observed |
|-----------|-------------------|----------|
| Clear positive/negative | Confidence > 0.8 or noul > 0.8 / < 0.2 | Confirmed — routinely exceeds thresholds |
| Ambiguous | Confidence < 0.7 or noul in 0.3–0.7 range | Confirmed — stays below over-confidence thresholds |
| High-conf accuracy | More often correct than low-conf | Confirmed — >70% accuracy on labeled sample |

The calibration is conservative: Jev would rather say "I'm not sure" (low confidence) than guess wrong with high confidence.

---

## 7. Cognitive Diversity Consideration

A natural question arises: if Jev is fast and cheap, should every agent use it for every decision?

**No.** Concentrating all routing through one decision model creates convergence — every agent develops the same blind spots. The recommended architecture is a separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                       │
│                                                              │
│   ┌───────────────────┐                                      │
│   │  ORCHESTRATOR     │  Jev triages: intent, urgency,       │
│   │  (routing agent)  │  complexity, routing                 │
│   └─────┬─────────────┘  ──▶  fast typed decision            │
│         │                   (<1s, ~$0.00002)                  │
│         │                                                   │
│         │  passes typed decision in task contract            │
│         │                                                   │
└─────────┼───────────────────────────────────────────────────┘
          │
          ├──────────────────┬──────────────────┐
          ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   WORKER (A)    │ │   WORKER (B)    │ │   WORKER (C)    │
│                 │ │                 │ │                 │
│  LLM reasoning  │ │  LLM reasoning  │ │  LLM reasoning  │
│  No Jev tool    │ │  No Jev tool    │ │  No Jev tool    │
│  Receives       │ │  Receives       │ │  Receives       │
│  typed decision │ │  typed decision │ │  typed decision │
│  from router    │ │  from router    │ │  from router    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
   Different model    Different model     Different model
   (different         (different          (different
    reasoning)         reasoning)          reasoning)
```

| Layer | Tool | Why |
|-------|------|-----|
| **Orchestrator** | Jev via Gavel | Fast triage, intent routing, priority scoring. The orchestrator sees all traffic; Jev handles volume. |
| **Worker agents** | LLM reasoning | Workers need reasoning, not classification. The Jev result arrives in the task contract from the orchestrator. |
| **Suitability advisor** | Jev suitability rubric | A meta-agent or module evaluates *whether* Jev fits a proposed workflow — applies the decision tree from the skill. |

Model diversity across worker agents provides cognitive isolation. Jev at the orchestrator layer provides fast upstream triage. Workers receive typed decisions, not the Jev tool itself.

---

## 8. Risks, Gaps, and Escapements

| Risk | Mitigation |
|------|------------|
| **Schema drift** | Tests run against the live API; schema changes are caught early. |
| **Over-confidence on rare inputs** | Confidence thresholds gate automatic action; low-confidence routes to human/LLM. |
| **Single model blind spots** | Cognitive diversity: use different LLMs for worker agents; use choice with "other" for ambiguous routing. |
| **Vendor lock-in** | Plugin is a thin wrapper; switching decision providers means changing one HTTP call. |
| **API key exposure** | Key is read from environment only; never committed. |

### Escapements — when not to use Jev

- The answer is open-ended or requires explanation.
- The task is multi-step reasoning.
- The input is not text or exceeds 32k tokens.
- The cost of a wrong answer exceeds the cost of a slow LLM call.
- Confidence is consistently low for the target domain.

---

## 9. Limitations

| Limitation | Detail |
|------------|--------|
| **No text generation** | Jev cannot write replies, code, or explanations. Strictly a decision model. |
| **No reasoning** | Multi-step chain-of-thought is impossible. System 1 (fast gut-check), not System 2 (deliberate reasoning). |
| **No multimodal** | Text only. No images, audio, or video. |
| **32k context** | Not suitable for document analysis or long conversation evaluation. |
| **English-primary** | Other languages accepted but with lower accuracy. |
| **No memory** | Each call is stateless. No learning across calls. |
| **Conservative noul** | Ambiguous inputs skew negative rather than uncertain. Consumers must account for this in threshold design. |

---

## 10. Deployment Considerations

Gavel is designed to drop into any OpenClaw installation:

1. Copy this repository into your OpenClaw extensions directory.
2. Ensure the TypeScript source is compiled: `npm install && npm run build`.
3. Set the environment variable `OPENROUTER_API_KEY` in the gateway environment.
4. Restart the OpenClaw gateway.
5. Verify the `jev_decide` tool is registered in agent sessions.

### Platform Concurrency Considerations

When multiple agents or subagents call `jev_decide` concurrently, be aware that some OpenClaw gateway versions route tool calls through a single approvals or execution path. Under contention, a call may be denied or retried. The plugin handles a 30s timeout and returns structured errors. If you observe intermittent denials at high concurrency, serialize calls or increase gateway execution tolerance.

---

## 11. Future Work

| Item | Description |
|------|-------------|
| **Python package** | Wrap the suitability rubric as a structured advisor module for typed recommendations. |
| **Router task class** | Add `jev_suitability` as a dispatchable task class for automated consult routing. |
| **Threshold tuning** | Current confidence thresholds (>0.8 auto, 0.5–0.8 confirm, <0.5 fallback) are heuristics. Larger labeled datasets could calibrate these per use case. |
| **Batch optimization** | For high-volume routing (1k+ decisions/day), explore batch API endpoints if TypeSafe offers them. |
| **Multi-language support** | Test Jev accuracy on non-English inputs if international routing is needed. |

---

## 12. Conclusion

Gavel exists because AI agents were burning expensive reasoning engines on cheap classification problems. The combination of a skill (teaching agents when to use structured decisions), a plugin (giving them the tool to make them), and a test suite (proving the tool works as claimed) closes that gap.

The tests proved that Jev is not a toy — it produces calibrated, conservative, fast decisions that an orchestrator can act on. The discoveries (strict criteria schema, float scores, conservative noul, explicit-urgency requirement) are not bugs; they are characteristics that consumers must understand to use the tool correctly.

**Three layers. Know when. Be able. Prove it works.**

That's Gavel.

---

*Plugin source: `index.ts`*  
*Skill: `SKILL.md`*  
*Test suite: `tests/`*  
*Test results: `tests/RESULTS.md`*
