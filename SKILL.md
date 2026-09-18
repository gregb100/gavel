---
name: "gavel"
description: "Use Gavel / Jev (TypeSafe System One) for fast structured decisions — classification, routing, scoring, boolean checks. Activate on jev, typesafe, decision model, classify, route, score, noul, choice."
---

# Gavel — Structured Decision Model

## When to use Gavel vs an LLM

Use Gavel when you need a **fast, cheap, typed decision** — not prose, not reasoning, not code.

| Use Gavel | Use an LLM |
|---------|-----------|
| Classify intent (bug vs feature vs research) | Write a response |
| Route a ticket (billing/technical/sales) | Explain reasoning |
| Score severity (0-3) | Generate code |
| Boolean check (is this urgent?) | Summarize a document |
| Confidence-gated routing | Multi-step reasoning |
| Batch parallel judgments | Creative writing |

**Rule:** If the answer is one of a known set of options, a number on a scale, or a yes/no — Gavel. If you need words back — LLM.

## What Gavel is

- Structured decision model (TypeSafe AI, System One class)
- Not a chat LLM — no text generation, no hallucination
- Returns typed values + calibrated probabilities + confidence
- 70-500ms per call, $0.042/MTok input, $0 output
- 32k context, text only (strings, JSON, arrays)
- Endpoint: OpenRouter `/api/alpha/decisions` (NOT chat completions)
- Model ID: `typesafe/jev-1.13`

## Tool: `jev_decide`

The OpenClaw plugin registers tool `jev_decide` with parameters:
- `state` (string): Content to evaluate — plain text, JSON, or array
- `questions` (object): Map of question IDs to typed questions
- `model` (optional): Override model ID (default `typesafe/jev-1.13`)

## Three primitives

### Noul — "Is this true?"

Yes/no question. Returns probability 0-1.

```json
"refund_requested": {
  "type": "noul",
  "instructions": "Does the customer request a refund?",
  "criteria": {
    "true": "Explicitly asks for money back",
    "false": "No refund request expressed"
  }
}
```

Response: `{ "type": "noul", "noul": 0.95 }`

**When:** Clean boolean check. Cheapest, simplest. No confidence score (the noul value IS the probability).

### Choice — "Which option?"

Pick one from a set. Returns choice + full probability distribution + confidence.

```json
"department": {
  "type": "choice",
  "instructions": "Which team should handle this?",
  "criteria": {
    "billing": "Payments, invoicing, refunds",
    "technical": "Bugs, outages, integrations",
    "sales": "Pricing, upgrades, new accounts",
    "other": "None of the above clearly fit"
  }
}
```

Response: `{ "type": "choice", "choice": "billing", "probabilities": {...}, "confidence": 0.88 }`

**When:** Routing, classification, categorization. Always include an "other" option when the list might not cover every input.

### Score — "Which level?"

Rate on an ordered rubric. Returns score + probability distribution + confidence.

```json
"frustration": {
  "type": "score",
  "instructions": "How frustrated is the customer?",
  "criteria": ["Calm", "Frustrated", "Very angry"]
}
```

Response: `{ "type": "score", "score": 2, "legend": {...}, "probabilities": {...}, "confidence": 1.0 }`

**When:** Severity, priority, sentiment, quality. Define at least 2 levels. More levels = more granularity but harder decisions.

## State — how to structure it

State is the content Gavel evaluates. All questions in one call see the same state.

| Format | When | Example |
|--------|------|---------|
| String | Simple message | `"My card was charged twice."` |
| Object | Named fields, records | `{"message": "...", "order_id": "A-104", "policy": "..."}` |
| Array | Conversation/sequence | `["Hi", "My card was charged twice.", "Please help"]` |

**Best practices:**
- Use object for most requests — named fields keep relationships clear
- Include relevant context (policies, records, prior messages)
- Separate content (state) from judgments (questions)
- Keep state under 32k tokens total

## Asking multiple questions

All questions in one call are evaluated **in parallel and independently**. Adding questions barely changes response time. No context rot between questions.

```json
{
  "state": "My payouts have been failing for 3 days and I am very angry.",
  "questions": {
    "is_urgent": { "type": "noul", "instructions": "Does this convey urgency?" },
    "department": { "type": "choice", "instructions": "Which team?", "criteria": {...} },
    "frustration": { "type": "score", "instructions": "How frustrated?", "criteria": ["Calm", "Frustrated", "Very angry"] }
  }
}
```

One call, three independent answers, ~200ms, ~$0.00002.

## Decomposition — atomic questions

Gavel works best on **one focused judgment per question**. Think "gut check a knowledgeable person makes in a few seconds."

**Bad:** "Analyze this startup pitch and determine the best course of action"
**Good:** Break into market_size, technical_feasibility, differentiation — then combine in code with weights.

When priorities shift, change the weights in your code, not the prompt.

## Confidence-gated routing

Every Choice and Score answer includes `confidence` (0-1), derived from the probability distribution. Use it to gate actions:

| Confidence | Action |
|------------|--------|
| **High (>0.8)** | Act automatically |
| **Medium (0.5-0.8)** | Proceed with caution — confirm, flag, or gather more info |
| **Low (<0.5)** | Do not act — route to human, request clarification, fall back to LLM |

Thresholds scale with risk: a $10 refund can auto-approve at 0.7; a $10,000 transfer needs 0.95.

## Example routing patterns

### Pattern: Intent routing
Classify an incoming engineering request before deciding how to handle it:

```json
{
  "state": "<user message>",
  "questions": {
    "intent": {
      "type": "choice",
      "instructions": "What kind of work is this?",
      "criteria": {
        "status": "Status check or quick question",
        "bug": "Bug report or issue to fix",
        "feature": "New feature or enhancement",
        "research": "Research or investigation",
        "ops": "Ops/infra/config/deploy",
        "chat": "Conversation or discussion"
      }
    },
    "complexity": {
      "type": "score",
      "instructions": "How complex is this?",
      "criteria": ["Trivial — solo", "Simple — solo", "Moderate — delegate", "Complex — decompose + delegate"]
    },
    "is_urgent": {
      "type": "noul",
      "instructions": "Does this require immediate action?"
    }
  }
}
```

Use intent + complexity + urgency to decide: solo fix, spawn an agent, queue for later, or escalate.

### Pattern: Bug triage
Classify incoming bug reports:

```json
{
  "state": "<bug report text>",
  "questions": {
    "severity": {
      "type": "score",
      "instructions": "How severe is this bug?",
      "criteria": ["Cosmetic", "Minor", "Moderate", "Major", "Critical"]
    },
    "category": {
      "type": "choice",
      "instructions": "What type of bug?",
      "criteria": {
        "crash": "Application crashes or hangs",
        "data_loss": "Data corruption or loss",
        "regression": "Previously working feature broke",
        "performance": "Slow or resource issue",
        "ui": "Visual or interaction issue",
        "security": "Security vulnerability"
      }
    },
    "is_blocker": {
      "type": "noul",
      "instructions": "Does this block normal operation?"
    }
  }
}
```

### Pattern: Message classification
For incoming bot messages or channel traffic:

```json
{
  "state": "<message text>",
  "questions": {
    "is_command": { "type": "noul", "instructions": "Is this a directive/command to the bot?" },
    "is_question": { "type": "noul", "instructions": "Is this asking for information?" },
    "tone": {
      "type": "score",
      "instructions": "How urgent is the tone?",
      "criteria": ["Casual", "Normal", "Time-sensitive", "Critical"]
    }
  }
}
```

### Pattern: Speculative fan-out
Send many questions at once, including speculative ones. Let code decide what's relevant:

```json
{
  "state": "<some content>",
  "questions": {
    "is_spam": { "type": "noul", "instructions": "Is this spam?" },
    "is_urgent": { "type": "noul", "instructions": "Is this urgent?" },
    "category": { "type": "choice", "instructions": "What category?", "criteria": {...} },
    "priority": { "type": "score", "instructions": "Priority level?", "criteria": ["Low", "Medium", "High"] },
    "needs_human": { "type": "noul", "instructions": "Does this need human review?" }
  }
}
```

5 questions, one call, ~200ms, ~$0.00002. Cheaper and faster than 5 LLM calls.

## System discovery — know your environment before using Gavel

Before an agent uses Gavel for the first time, it should understand the target
system. If any of these are unknown, ask the operator before proceeding:

1. **Available models** — Which LLMs are configured? Which is the cheapest fast
   model suitable for classification fallback when Gavel is unavailable?
2. **Routing decisions** — What classifications does this system actually need?
   What are the categories? What routing actions map to each category?
3. **Confidence thresholds** — What risk level warrants auto-action vs
   confirmation? What is the blast radius of a wrong routing decision?
4. **Fallback chain** — When Gavel fails, which model takes over? What if that
   model also fails? What is the safe default when all models are unavailable?
5. **Safe state** — What data can leave the system for a cloud API? What is
   PII? What is internal? What must never be sent as Gavel state?

If these are not answered, the agent should discover them before relying on
Gavel for production routing. Guessing thresholds or fallback models is a defect.

## Fallback strategy — when Gavel is unavailable

Gavel calls an external API. It will fail. The plugin throws on error (timeout, 4xx,
5xx, network, missing API key). The agent must implement fallback — the plugin
is a pipe, not a policy engine.

### Tiered fallback (agent-implemented)

| Tier | Trigger | What runs | Cost | Latency |
|------|---------|-----------|------|---------|
| **1 — Gavel** | Normal path | `jev_decide` | ~$0.00002 | ~200ms |
| **2 — Fast LLM** | Gavel error/timeout | Cheapest configured fast model with structured classification prompt | ~$0.001-0.01 | ~1-3s |
| **3 — Lite LLM** | Fast LLM fails | Cheapest lite model with same structured prompt | ~$0.0005 | ~1-2s |
| **4 — Hardcoded** | All models fail | Route to safe default ("unknown" bucket, queue for manual review) | $0 | instant |

### Fallback prompt design

The fallback LLM call should be structured the **same way** as the Gavel call —
same question, same answer set, same state. Ask the LLM to return only the
label, not reasoning. Downstream code should not need to know whether Gavel or
the LLM made the decision.

Example fallback prompt for a choice question:
```
Classify the following message into exactly one category.
Return only the category label, nothing else.

Categories: status, bug, feature, research, ops, chat, other

Message: "fix the login bug on dashboard"
```

### When to fall back vs when to stop

- **Fall back (tier 2-3):** Gavel timeout, 5xx, network error — transient failures
- **Fall back (tier 2-3):** 401 auth error — but also alert operator to fix API key
- **Fall back (tier 2-3):** 429 rate limit — but also back off and reduce call frequency
- **Stop and alert (tier 4):** All models failing — system-level problem, do not retry silently

### Cost of fallback

Falling back to an LLM is 50-500x more expensive than Gavel per call. At low
volume (<50 Gavel calls/day), fallback cost is negligible. At scale (1k+
calls/day), frequent fallback indicates a systemic problem — investigate root
cause, do not accept fallback as normal.

## Limitations

- **No text generation** — cannot write replies, code, or explanations
- **No reasoning** — fast gut-checks only (System 1 thinking, not System 2)
- **No multimodal** — text only (no images, audio, video)
- **32k context** — not for document analysis
- **English-primary** — other languages accepted but lower accuracy
- **No memory** — each call is stateless
- **Not a session model** — cannot be used as `/model jev113` in OpenClaw

## Cost comparison

| Task | Gavel | General-purpose LLM |
|------|-----|---------------------|
| 1 classification | ~$0.00002 | ~$0.01-0.05 |
| 1000 classifications | ~$0.02 | ~$10-50 |
| 10k classifications/day | ~$0.20 | ~$100-500 |

For high-volume routing decisions, Gavel is 500-2500x cheaper.

## Related

- TypeSafe docs: https://docs.typesafe.ai
- TypeSafe API reference: https://docs.typesafe.ai/api
- OpenRouter model page: https://openrouter.ai/typesafe/jev-1.13
