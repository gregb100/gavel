# Gavel — Stop Burning LLM Calls on Classification

**Turn routing decisions into 200ms typed answers instead of 2-second LLM round-trips.**

Gavel is an OpenClaw plugin that gives AI agents a fast, cheap, structured decision tool. It wraps TypeSafe's Jev model (`typesafe/jev-1.13`) through the OpenRouter decisions API and teaches agents exactly when to use it — and when not to.

## The pitch

Every time your agent classifies an incoming message, routes a bug report, or gauges urgency, it's burning a full LLM call on what's really a one-word answer. Gavel makes that decision in 200ms for $0.00002 — **500 to 2,500x cheaper** than a standard LLM call.

It can't hallucinate an answer outside your defined options. It returns calibrated confidence you can gate actions on. And it never generates prose when all you needed was a label.

## What it does

Three primitives. That's it.

| Primitive | Question | Returns |
|-----------|----------|---------|
| **Noul** | Is this true? | Probability 0–1 |
| **Choice** | Which option? | Selection + full distribution + confidence |
| **Score** | What level? | Rubric level + distribution + confidence |

## What it doesn't do

Write code. Generate prose. Reason through problems. Explain decisions. Process images. Remember past calls.

**That's the point.** Gavel handles the routing decision so your LLM can focus on the actual work.

## How it fits

```
User says "fix the login bug"
         │
         ▼
   GAVEL classifies (200ms, $0.00002)
   intent=bug  complexity=moderate  urgency=low
         │
         ▼
   LLM builds the fix (reasoning, code generation)
         │
         ▼
   Done
```

Gavel decides *what kind of work this is*. The LLM does the work. Clean separation.

## What's in the box

- **Plugin** (`index.ts`) — registers `jev_decide` tool, calls OpenRouter, returns typed answers
- **Skill** (`SKILL.md`) — teaches agents when to use Gavel, when to use LLM, and how to construct questions
- **Tests** — 32 integration tests against the live API, all passing
- **White paper** — architecture, risks, gaps, escapements, and a real-world case study showing 40% context savings
- **README** — drop-in install for any OpenClaw system

## Install

```bash
cp -r gavel ~/.openclaw/extensions/gavel
cd ~/.openclaw/extensions/gavel
npm install && npm run build
export OPENROUTER_API_KEY=sk-or-...
# restart your gateway
```

## Requirements

- OpenClaw gateway >= 2026.9.4
- OpenRouter API key with access to `typesafe/jev-1.13`

## License

MIT

## Links

- [White paper](docs/GAVEL-WHITE-PAPER.md) — full architecture, testing, and analysis
- [Case study](docs/CASE-STUDY-CONTEXT-SAVINGS.md) — 40% context savings on real classification work
- [TypeSafe docs](https://docs.typesafe.ai)
- [OpenRouter model page](https://openrouter.ai/typesafe/jev-1.13)
