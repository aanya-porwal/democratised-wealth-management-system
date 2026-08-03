"use client";

// AI message renderer — renders one rich assistant/user message.
// Each message can contain multiple blocks: text (markdown), tables,
// tool traces, action cards, follow-up suggestions and explainability.

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Bot, User, Sparkles } from "lucide-react";
import type {
  AiAction,
  AiMessageBlock,
  AiRichMessage,
  AiTable,
} from "@/types/api";
import { cn } from "@/lib/utils";
import { AiToolTrace } from "@/components/ai/ai-tool-trace";
import { AiActionCard } from "@/components/ai/ai-action-card";
import { AiExplainability } from "@/components/ai/ai-explainability";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";

function TextBlock({ text }: { text: string }) {
  return (
    <div className="prose prose-sm max-w-none dark:prose-invert prose-p:leading-relaxed prose-p:my-2">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
    </div>
  );
}

function TableBlock({ block }: { block: AiMessageBlock }) {
  const table = block.table as AiTable | undefined;
  if (!table) return null;
  return (
    <div className="overflow-x-auto rounded-lg border">
      <Table>
        {table.title ? (
          <caption className="py-2 text-xs font-medium">{table.title}</caption>
        ) : null}
        <TableHeader>
          <TableRow>
            {table.columns.map((col) => (
              <TableHead key={col.key}>{col.header}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {table.rows.map((row, rIdx) => (
            <TableRow key={rIdx}>
              {table.columns.map((col) => (
                <TableCell key={col.key}>{String(row[col.key] ?? "—")}</TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function ActionCardBlock({ block }: { block: AiMessageBlock }) {
  const actions = block.actions as AiAction[] | undefined;
  if (!actions?.length) return null;
  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        Suggested actions
      </p>
      {actions.map((action) => (
        <AiActionCard key={action.id} action={action} />
      ))}
    </div>
  );
}

function FollowupsBlock({
  block,
  onSend,
}: {
  block: AiMessageBlock;
  onSend: (text: string) => void;
}) {
  const followups = block.followups as string[] | undefined;
  if (!followups?.length) return null;
  return (
    <div className="flex flex-wrap gap-1.5">
      {followups.map((q) => (
        <Button
          key={q}
          variant="outline"
          size="sm"
          className="h-auto rounded-full px-3 py-1 text-xs"
          onClick={() => onSend(q)}
        >
          <Sparkles className="mr-1.5 h-3 w-3 text-primary" aria-hidden />
          {q}
        </Button>
      ))}
    </div>
  );
}

export function AiMessage({
  message,
  onSendFollowup,
}: {
  message: AiRichMessage;
  onSendFollowup?: (text: string) => void;
}) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex w-full gap-3",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {!isUser ? (
        <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border bg-muted">
          <Bot className="h-4 w-4 text-primary" aria-hidden />
        </div>
      ) : null}

      <div
        className={cn(
          "min-w-0 max-w-[85%] space-y-2 rounded-xl px-3.5 py-2.5 text-sm",
          isUser ? "bg-primary text-primary-foreground" : "border bg-muted/30"
        )}
      >
        {message.pending ? (
          <div className="flex items-center gap-2 text-muted-foreground">
            <span className="h-2 w-2 animate-pulse rounded-full bg-primary" />
            Thinking…
          </div>
        ) : (
          <>
            {message.blocks?.map((block) => {
              switch (block.type) {
                case "text":
                  return <TextBlock key={block.id} text={block.text ?? ""} />;
                case "table":
                  return <TableBlock key={block.id} block={block} />;
                case "toolTrace":
                  return (
                    <AiToolTrace
                      key={block.id}
                      toolCalls={block.toolCalls ?? []}
                    />
                  );
                case "actionCard":
                  return <ActionCardBlock key={block.id} block={block} />;
                case "followups":
                  return onSendFollowup ? (
                    <FollowupsBlock
                      key={block.id}
                      block={block}
                      onSend={onSendFollowup}
                    />
                  ) : null;
                case "explainability":
                  return block.explainability ? (
                    <AiExplainability
                      key={block.id}
                      explainability={block.explainability}
                    />
                  ) : null;
                default:
                  return null;
              }
            })}
          </>
        )}
      </div>

      {isUser ? (
        <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border bg-muted">
          <User className="h-4 w-4" aria-hidden />
        </div>
      ) : null}
    </div>
);
}

