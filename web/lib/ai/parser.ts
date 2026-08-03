// lib/ai/parser.ts
// Parses the backend ChatResponse into structured, renderable message blocks.
// Streaming-ready: accepts partial chunks and always returns a safe shape.

import type {
  AiAction,
  AiMessageBlock,
  AiRichMessage,
  AiToolCall,
  ChatResponse,
  ToolResult,
} from "@/types/api";

const TOOL_FRIENDLY_NAMES: Record<string, string> = {
  risk_tool: "Risk analysis",
  goal_tool: "Goals retrieved",
  allocation_tool: "Allocation computed",
  security_tool: "Security research",
  portfolio_tool: "Portfolio retrieved",
  simulation_tool: "Monte Carlo complete",
  scenario_tool: "Scenario analysis",
  research_tool: "Research generated",
  database_tool: "Data lookup",
  market_data_tool: "Market data fetched",
  health_score_tool: "Health score computed",
  comparison_tool: "Comparison built",
  profile_tool: "Profile loaded",
};

export function friendlyToolName(name: string): string {
  return TOOL_FRIENDLY_NAMES[name] ?? name.replace(/_/g, " ");
}

export function uid(prefix = "b"): string {
  return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function countLeadingBullets(text: string): number {
  const lines = text
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
  return lines.filter((l) => /^[-*•]/.test(l)).length;
}

/** Convert a raw tool_calls entry (loose dict) into a typed AiToolCall. */
function normalizeToolCall(raw: Record<string, unknown>, index: number): AiToolCall {
  const name = String(raw?.name ?? raw?.tool ?? "tool");
  return {
    id: String(raw?.id ?? uid(`tool_${index}`)),
    name,
    friendlyName: friendlyToolName(name),
    status: "done",
    arguments: (raw?.arguments as Record<string, unknown>) ?? {},
    summary: raw?.summary ? String(raw.summary) : undefined,
    latencyMs: typeof raw?.latency_ms === "number" ? raw.latency_ms : undefined,
  };
}

/** Try to detect a table from a markdown-ish block. */
function tryParseTable(text: string): AiMessageBlock["table"] | null {
  const lines = text.trim().split("\n");
  const separatorIdx = lines.findIndex((l) => /^\s*\|?[\s:|-]+\|?\s*$/.test(l) && l.includes("-"));
  if (separatorIdx < 1) return null;
  const headerLine = lines[separatorIdx - 1];
  if (!headerLine.includes("|")) return null;

  const headers = headerLine
    .split("|")
    .map((h) => h.trim())
    .filter(Boolean);
  if (headers.length < 2) return null;

  const rows: Array<Record<string, string | number>> = [];
  for (let i = separatorIdx + 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line.includes("|")) break;
    const cells = line
      .split("|")
      .map((c) => c.trim())
      .filter((c, idx) => !(idx === 0 && c === "") && !(idx === headers.length && c === ""));
    if (cells.length < headers.length) continue;
    const row: Record<string, string | number> = {};
    headers.forEach((h, idx) => {
      const raw = cells[idx] ?? "";
      const num = Number(raw.replace(/[₹,\s%]/g, ""));
      row[h] = Number.isFinite(num) && raw.replace(/[₹,\s%]/g, "").length > 0 ? num : raw;
    });
    rows.push(row);
  }

  if (rows.length === 0) return null;
  return {
    columns: headers.map((h) => ({ key: h, header: h })),
    rows,
  };
}

/**
 * Build a rich assistant message from a ChatResponse.
 * Splits the reply into text/table/action blocks and appends tool trace,
 * follow-ups and explainability.
 */
export function parseChatResponse(response: ChatResponse): AiRichMessage {
  const blocks: AiMessageBlock[] = [];
  const reply = response.reply ?? "";

  // 1. Tool trace block (visualize orchestration)
  if (response.tool_calls && response.tool_calls.length > 0) {
    blocks.push({
      id: uid("tools"),
      type: "toolTrace",
      toolCalls: response.tool_calls.map(normalizeToolCall),
    });
  }

  // 2. Split reply into text/table blocks
  const segments = reply.split(/\n{2,}/);
  let currentText = "";
  for (const segment of segments) {
    const table = tryParseTable(segment);
    if (table) {
      if (currentText.trim()) {
        blocks.push({ id: uid("txt"), type: "text", text: currentText.trim() });
        currentText = "";
      }
      blocks.push({ id: uid("tbl"), type: "table", table });
    } else {
      currentText += `${currentText ? "\n\n" : ""}${segment}`;
    }
  }
  if (currentText.trim()) {
    blocks.push({ id: uid("txt"), type: "text", text: currentText.trim() });
  }

  // 3. Action cards derived from tool calls + metadata
  const actions = deriveActions(response, blocks);
  if (actions.length > 0) {
    blocks.push({ id: uid("act"), type: "actionCard", actions });
  }

  // 4. Follow-up questions
  if (response.followup_questions && response.followup_questions.length > 0) {
    blocks.push({
      id: uid("fu"),
      type: "followups",
      followups: response.followup_questions,
    });
  }

  // 5. Explainability
  blocks.push({
    id: uid("exp"),
    type: "explainability",
    explainability: {
      agentsUsed: response.agents_used ?? [],
      toolsUsed: (response.tool_calls ?? []).map((t) => String(t?.name ?? t?.tool ?? "")),
      dataSources: [],
      calculations: [],
      disclaimer: response.disclaimer,
    },
  });

  return {
    id: uid("msg"),
    role: "assistant",
    content: reply,
    blocks,
    createdAt: new Date().toISOString(),
  };
}

function deriveActions(response: ChatResponse, blocks: AiMessageBlock[]): AiAction[] {
  const actions: AiAction[] = [];
  const toolNames = (response.tool_calls ?? []).map((t) => String(t?.name ?? t?.tool ?? ""));

  if (toolNames.includes("simulation_tool") || /monte carlo|simulation/i.test(response.reply)) {
    actions.push({
      id: uid("a"),
      type: "run_simulation",
      label: "Run Monte Carlo",
      description: "Simulate your portfolio to the target horizon.",
      primary: true,
    });
  }
  if (toolNames.includes("allocation_tool") || /allocation|rebalance/i.test(response.reply)) {
    actions.push({
      id: uid("a"),
      type: "apply_allocation",
      label: "Apply Allocation",
      description: "Rebalance toward the recommended target weights.",
      primary: true,
    });
  }
  if (toolNames.includes("research_tool") || /research|etf|fund|stock/i.test(response.reply)) {
    actions.push({
      id: uid("a"),
      type: "view_research",
      label: "View Research Report",
    });
  }
  if (toolNames.includes("comparison_tool") || /compare/i.test(response.reply)) {
    actions.push({
      id: uid("a"),
      type: "compare_securities",
      label: "Compare Securities",
    });
  }
  if (toolNames.includes("scenario_tool") || /scenario|what if|salary increase|salary decrease/i.test(response.reply)) {
    actions.push({
      id: uid("a"),
      type: "run_scenario",
      label: "Run Scenario Analysis",
    });
  }
  if (toolNames.includes("goal_tool") || /goal|sip|retire/i.test(response.reply)) {
    actions.push({
      id: uid("a"),
      type: "update_goal",
      label: "Update Goal",
    });
  }
  if (toolNames.includes("health_score_tool")) {
    actions.push({
      id: uid("a"),
      type: "generate_recommendations",
      label: "Generate Recommendations",
    });
  }

  // Follow-up if no actions derived
  if (actions.length === 0) {
    actions.push({
      id: uid("a"),
      type: "navigate",
      label: "View in Dashboard",
      meta: { href: "/app" },
    });
  }

  return actions;
}

/** Build a user message object. */
export function buildUserMessage(text: string): AiRichMessage {
  return {
    id: uid("user"),
    role: "user",
    content: text,
    blocks: [{ id: uid("txt"), type: "text", text }],
    createdAt: new Date().toISOString(),
  };
}

/** A pending assistant "thinking" message to animate tool progress. */
export function buildPendingMessage(): AiRichMessage {
  return {
    id: uid("pending"),
    role: "assistant",
    content: "",
    blocks: [
      {
        id: uid("tools"),
        type: "toolTrace",
        toolCalls: [{ id: uid("t"), name: "thinking", friendlyName: "Planning…", status: "running" }],
      },
    ],
    createdAt: new Date().toISOString(),
    pending: true,
  };
}

/** Merge a tool result into a pending message's tool trace. */
export function appendToolResult(
  message: AiRichMessage,
  result: ToolResult
): AiRichMessage {
  const toolBlocks = message.blocks
    .filter((b) => b.type === "toolTrace")
    .map((b) => ({ ...b, toolCalls: [...(b.toolCalls ?? [])] }));
  const toolCalls = toolBlocks[0]?.toolCalls ?? [];
  const existing = toolCalls.find((t) => t.name === result.tool);
  if (existing) {
    existing.status = result.ok ? "done" : "error";
    existing.latencyMs = result.latency_ms;
    existing.summary = result.ok ? friendlyToolName(result.tool) : result.error ?? "Error";
  } else {
    toolCalls.push({
      id: uid("t"),
      name: result.tool,
      friendlyName: friendlyToolName(result.tool),
      status: result.ok ? "done" : "error",
      latencyMs: result.latency_ms,
      summary: result.ok ? friendlyToolName(result.tool) : result.error ?? "Error",
    });
  }
  return { ...message, blocks: toolBlocks };
}

/** Count leading bullet sentences for summary heuristics. */
export { countLeadingBullets };
