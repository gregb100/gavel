# Gavel

Structured decision model plugin for OpenClaw — fast, cheap, typed decisions via TypeSafe Jev.

Gavel turns classification, routing, scoring, and boolean checks into a single tool call instead of a full LLM round-trip. It is useful when an agent needs a typed answer from a known set of options, a rubric level, or a calibrated probability — not prose, code, or reasoning.

The plugin registers `jev_decide` in OpenClaw. The skill teaches agents when and how to use it. The test suite proves it works against the live OpenRouter decisions API.

## Requirements

- OpenClaw gateway >= `2026.9.4`
- An [OpenRouter](https://openrouter.ai) API key with access to `typesafe/jev-1.13`

## Installation

1. Copy this directory into your OpenClaw extensions directory, for example:

   ```bash
   cp -r gavel-public ~/.openclaw/extensions/gavel
   ```

2. Install dependencies and build:

   ```bash
   cd ~/.openclaw/extensions/gavel
   npm install
   npm run build
   ```

3. Set the environment variable in the gateway environment:

   ```bash
   export OPENROUTER_API_KEY=sk-or-...
   ```

4. Restart the OpenClaw gateway.

5. Verify the plugin loaded by checking that `jev_decide` is available in an agent session.

## Usage

Agents call the tool with a state string and a set of typed questions:

```json
{
  "state": "My card was charged twice and I need the money back.",
  "questions": {
    "refund_requested": {
      "type": "noul",
      "instructions": "Does the customer request a refund?",
      "criteria": {
        "true": "Explicitly asks for money back",
        "false": "No refund request expressed"
      }
    },
    "department": {
      "type": "choice",
      "instructions": "Which team should handle this?",
      "criteria": {
        "billing": "Payments, invoicing, refunds",
        "technical": "Bugs, outages, integrations",
        "sales": "Pricing, upgrades, new accounts",
        "other": "None of the above clearly fit"
      }
    },
    "frustration": {
      "type": "score",
      "instructions": "How frustrated is the customer?",
      "criteria": ["Calm", "Frustrated", "Very angry"]
    }
  }
}
```

See [SKILL.md](./SKILL.md) for complete guidance: when to use Jev, how to structure state, confidence thresholds, and example routing patterns.

## Three primitives

| Primitive | Question | Output |
|-----------|----------|--------|
| **Noul** | Is this true? | Probability 0–1 |
| **Choice** | Which option? | Selected option + distribution + confidence |
| **Score** | Which level? | Rubric level + distribution + confidence |

## Architecture

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

## Testing

Tests hit the live OpenRouter decisions API and require `OPENROUTER_API_KEY`:

```bash
cd tests
python3 -m pytest -v
```

Tests marked `slow` are skipped by default. Include them with:

```bash
python3 -m pytest -v -m "slow"
```

All tests are also marked `costs` because each call consumes a small amount of API credit.

## Documentation

- [SKILL.md](./SKILL.md) — how to use Jev from an agent
- [docs/GAVEL-WHITE-PAPER.md](./docs/GAVEL-WHITE-PAPER.md) — design, test methodology, results, and deployment guidance
- [tests/RESULTS.md](./tests/RESULTS.md) — latest test run findings

## License

MIT
