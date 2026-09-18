import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { defineToolPlugin } from "openclaw/plugin-sdk/tool-plugin";
import { Type, type Static } from "typebox";

const endpoint = "https://openrouter.ai/api/alpha/decisions";
const defaultModel = "typesafe/jev-1.13";

interface QuestionSpec {
  type: "noul" | "choice" | "score";
  instructions: string;
  criteria?: unknown;
}

interface DecisionRequest {
  model: string;
  state: string;
  questions: Record<string, QuestionSpec>;
}

interface DecisionResponse {
  model: string;
  answers: Record<string, unknown>;
  usage?: unknown;
  id?: string;
}

async function postDecisions(body: DecisionRequest): Promise<DecisionResponse> {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    throw new Error("OPENROUTER_API_KEY is not set");
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30_000);

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    const text = await response.text();
    let parsed: unknown;
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = { raw: text };
    }

    if (!response.ok) {
      const message =
        typeof parsed === "object" &&
        parsed !== null &&
        "error" in parsed &&
        parsed.error !== null &&
        typeof parsed.error === "object" &&
        "message" in parsed.error
          ? String(parsed.error.message)
          : `OpenRouter returned ${response.status}`;
      const error = new Error(message);
      (error as Error & { status?: number }).status = response.status;
      throw error;
    }

    if (
      typeof parsed !== "object" ||
      parsed === null ||
      !("answers" in parsed)
    ) {
      throw new Error("OpenRouter response missing answers");
    }

    return parsed as DecisionResponse;
  } finally {
    clearTimeout(timeout);
  }
}

function formatAnswers(answers: Record<string, unknown>): string {
  const lines: string[] = [];
  for (const [key, value] of Object.entries(answers)) {
    if (value === null || value === undefined) {
      lines.push(`${key}: (no answer)`);
    } else if (typeof value === "object") {
      lines.push(`${key}: ${JSON.stringify(value)}`);
    } else {
      lines.push(`${key}: ${String(value)}`);
    }
  }
  return lines.join("\n");
}

const parametersSchema = Type.Object({
  state: Type.String({
    description:
      "The content to evaluate — plain string, JSON, or array of text",
  }),
  questions: Type.Record(
    Type.String(),
    Type.Object({
      type: Type.Union(
        [
          Type.Literal("noul"),
          Type.Literal("choice"),
          Type.Literal("score"),
        ],
        {
          description:
            "Question type: noul (yes/no), choice (pick from options), score (rate on rubric)",
        },
      ),
      instructions: Type.String({
        description: "What the model should decide/rate/evaluate",
      }),
      criteria: Type.Optional(
        Type.Any({
          description:
            "For noul: {true: '...', false: '...'}. For choice: {option_key: 'description'}. For score: ['level0', 'level1', 'level2']",
        }),
      ),
    }),
  ),
  model: Type.Optional(
    Type.String({ description: "Model ID, default typesafe/jev-1.13" }),
  ),
});

export default definePluginEntry(
  defineToolPlugin({
    id: "jev",
    name: "Jev Decisions",
    description:
      "TypeSafe Jev structured decision model via OpenRouter decisions API",
    activation: { onStartup: true },
    tools: (registerTool) => [
      registerTool({
        name: "jev_decide",
        label: "Jev Decide",
        description:
          "Ask TypeSafe Jev structured decision questions about a piece of state via the OpenRouter decisions API.",
        parameters: parametersSchema,
        outputSchema: Type.Object(
          {
            model: Type.String(),
            answers: Type.Record(Type.String(), Type.Any()),
            usage: Type.Optional(Type.Any()),
            id: Type.Optional(Type.String()),
          },
          { additionalProperties: false },
        ),
        async execute(params: Static<typeof parametersSchema>) {
          const requestBody: DecisionRequest = {
            model: params.model || defaultModel,
            state: params.state,
            questions: params.questions,
          };

          try {
            const response = await postDecisions(requestBody);

            const answers = response.answers ?? {};
            const summary =
              Object.keys(answers).length === 0
                ? "Jev returned no answers."
                : formatAnswers(answers);

            return {
              content: [
                { type: "text", text: `Model: ${response.model}` },
                { type: "text", text: summary },
              ],
              details: response,
            };
          } catch (error) {
            const message =
              error instanceof Error ? error.message : String(error);
            const status =
              error && typeof error === "object" && "status" in error
                ? Number(error.status)
                : undefined;

            const err = new Error(message);
            if (status !== undefined) {
              (err as Error & { status?: number }).status = status;
            }
            throw err;
          }
        },
      }),
    ],
  }),
);
