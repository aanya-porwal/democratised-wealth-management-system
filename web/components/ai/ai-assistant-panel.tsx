"use client";

// AI Assistant panel — a persistent, draggable floating panel that
// gives every page one-tap access to the financial AI coach.
// Uses AiCoachProvider under the hood (already wired at the app root).

import { useCallback, useRef, useEffect } from "react";
import { Bot, Loader2, Send, X, Eraser, Sparkles } from "lucide-react";
import { useAiCoach } from "@/components/ai/ai-coach-context";
import { AiMessage } from "@/components/ai/ai-message";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const SUGGESTIONS = [
  "Am I on track for retirement?",
  "What should I do with my monthly surplus?",
  "Run a market-crash scenario for me.",
  "How is my financial health?",
];

export function AiAssistantPanel({ className }: { className?: string }) {
  const {
    isOpen,
    open,
    close,
    toggle,
    isStreaming,
    messages,
    sendMessage,
    reset,
  } = useAiCoach();

  const composerRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Focus composer when panel opens
  useEffect(() => {
    if (isOpen) {
      // small delay so the panel animation finishes
      const t = setTimeout(() => composerRef.current?.focus(), 150);
      return () => clearTimeout(t);
    }
  }, [isOpen]);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  return (
    <>
      {/* Floating trigger button */}
      {!isOpen ? (
        <Button
          size="icon"
          className={cn("fixed bottom-4 right-4 z-50 h-12 w-12 rounded-full shadow-lg", className)}
          onClick={() => void open()}
          aria-label="Open AI Financial Coach"
        >
          <Bot className="h-5 w-5" aria-hidden />
        </Button>
      ) : null}

      {/* Panel */}
      {isOpen ? (
        <div
          className={cn(
            "fixed bottom-4 right-4 z-50 flex w-[420px] flex-col overflow-hidden rounded-xl border bg-background shadow-2xl",
            "h-[600px] max-h-[85vh]",
            "max-sm:inset-0 max-sm:h-full max-sm:w-full max-sm:rounded-none",
            className
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b px-4 py-2.5">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10">
                <Bot className="h-4 w-4 text-primary" aria-hidden />
              </div>
              <span className="text-sm font-semibold">Financial Coach</span>
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={reset}
                aria-label="Reset conversation"
              >
                <Eraser className="h-4 w-4" aria-hidden />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={close}
                aria-label="Close AI assistant"
              >
                <X className="h-4 w-4" aria-hidden />
              </Button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-3 px-4 py-3">
            {messages.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full border bg-muted">
                  <Sparkles className="h-6 w-6 text-primary" aria-hidden />
                </div>
                <div className="max-w-xs space-y-1">
                  <p className="text-sm font-medium">How can I help with your finances?</p>
                  <p className="text-xs text-muted-foreground">
                    Ask about your plan, portfolio, goals, or run a scenario analysis.
                  </p>
                </div>
                <div className="flex flex-wrap justify-center gap-1.5">
                  {SUGGESTIONS.map((s) => (
                    <Button
                      key={s}
                      variant="outline"
                      size="sm"
                      className="h-auto rounded-full px-2.5 py-1 text-xs"
                      onClick={() => void sendMessage(s)}
                    >
                      <Sparkles className="mr-1 h-2.5 w-2.5 text-primary" aria-hidden />
                      {s}
                    </Button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg) => (
                <AiMessage
                  key={msg.id}
                  message={msg}
                  onSendFollowup={(text) => void sendMessage(text)}
                />
              ))
            )}
            <div ref={bottomRef} />
          </div>

          {/* Composer */}
          <div className="border-t px-3 py-2.5">
            <form
              className="flex gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                const input = composerRef.current;
                if (input && input.value.trim()) {
                  void sendMessage(input.value);
                  input.value = "";
                }
              }}
            >
              <Input
                ref={composerRef}
                placeholder="Ask your financial coach…"
                aria-label="Message your AI coach"
                className="min-h-9 flex-1"
                disabled={isStreaming}
              />
              <Button
                type="submit"
                size="icon"
                className="h-9 w-9 shrink-0"
                disabled={isStreaming}
                aria-label="Send message"
              >
                {isStreaming ? (
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                ) : (
                  <Send className="h-4 w-4" aria-hidden />
                )}
              </Button>
            </form>
          </div>
        </div>
      ) : null}
    </>
  );
}

/**
 * Standalone AI coach page — uses the same context but renders full-page.
 */
export function AiCoachFullPage({ className }: { className?: string }) {
  const { isStreaming, messages, sendMessage, reset } = useAiCoach();
  const composerRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Header */}
      <div className="flex items-center justify-between border-b px-6 py-3">
        <div>
          <h2 className="text-lg font-bold tracking-tight">AI Financial Coach</h2>
          <p className="text-xs text-muted-foreground">
            Your persistent, conversational financial advisor.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={reset}>
          <Eraser className="mr-1.5 h-3.5 w-3.5" aria-hidden /> New chat
        </Button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 px-4 py-4 md:px-8 mx-auto w-full max-w-4xl">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
            <div className="rounded-full border bg-muted p-5">
              <Bot className="h-10 w-10 text-primary" aria-hidden />
            </div>
            <div className="max-w-md space-y-1">
              <h3 className="text-lg font-medium">How can I help with your finances today?</h3>
              <p className="text-sm text-muted-foreground">
                Ask about your plan, portfolio, goals, scenarios, or research.
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <Button
                  key={s}
                  variant="outline"
                  size="sm"
                  onClick={() => void sendMessage(s)}
                >
                  <Sparkles className="mr-1.5 h-3 w-3 text-primary" aria-hidden />
                  {s}
                </Button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <AiMessage
              key={msg.id}
              message={msg}
              onSendFollowup={(text) => void sendMessage(text)}
            />
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* Composer */}
      <div className="border-t px-4 py-3 md:px-8">
        <form
          className="mx-auto flex w-full max-w-4xl gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            const input = composerRef.current;
            if (input && input.value.trim()) {
              void sendMessage(input.value);
              input.value = "";
            }
          }}
        >
          <Input
            ref={composerRef}
            placeholder="Ask your financial coach…"
            aria-label="Message your AI coach"
            className="min-h-10 flex-1"
            disabled={isStreaming}
          />
          <Button type="submit" size="icon" className="h-10 w-10" disabled={isStreaming}>
            {isStreaming ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
            ) : (
              <Send className="h-4 w-4" aria-hidden />
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}
