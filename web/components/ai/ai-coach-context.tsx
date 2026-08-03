"use client";

// AI Coach context — the global, persistent assistant state.
// - Holds the open/closed state of the assistant panel.
// - Send messages via the /ai/chat endpoint and renders rich blocks.
// - Never computes financial figures — only sends the user's message plus
//   a context summary (already-fetched backend data) to the backend.

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { api } from "@/lib/api/client";
import { buildAiContext } from "@/lib/ai/context";
import {
  buildPendingMessage,
  buildUserMessage,
  parseChatResponse,
} from "@/lib/ai/parser";
import type { AiRichMessage } from "@/types/api";

export interface SendMessageOptions {
  context?: Record<string, unknown>;
  onError?: (message: string) => void;
}

interface AiCoachContextValue {
  isOpen: boolean;
  open: (opts?: { message?: string; context?: Record<string, unknown> }) => void;
  close: () => void;
  toggle: () => void;
  isStreaming: boolean;
  messages: AiRichMessage[];
  sendMessage: (text: string, opts?: SendMessageOptions) => Promise<void>;
  reset: () => void;
  sessionId: string | null;
}

const AiCoachContext = createContext<AiCoachContextValue | null>(null);

export function AiCoachProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<AiRichMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const sessionIdRef = useRef<string | null>(null);

const close = useCallback(() => setIsOpen(false), []);
  const toggle = useCallback(() => setIsOpen((v) => !v), []);

  const reset = useCallback(() => {
    setMessages([]);
    sessionIdRef.current = null;
  }, []);

  const sendMessage = useCallback(
    async (text: string, opts?: SendMessageOptions) => {
      const content = text.trim();
      if (!content || isStreaming) return;

      setMessages((prev) => [...prev, buildUserMessage(content)]);
      setMessages((prev) => [...prev, buildPendingMessage()]);
      setIsStreaming(true);

      try {
        const context = opts?.context ?? {};
        const response = await api.aiChat({
          session_id: sessionIdRef.current,
          message: content,
          context: {
            ...buildAiContext({ page: "assistant" }),
            ...context,
          },
        });
        sessionIdRef.current = response.session_id;
        setMessages((prev) => {
          const copy = [...prev];
          // Replace the trailing pending message with the parsed response.
          copy.pop();
          return [...copy, parseChatResponse(response)];
        });
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : "Sorry, I couldn't reach the AI service. Please make sure the backend AI layer is running and try again.";
        setMessages((prev) => {
          const copy = [...prev];
          copy.pop();
          return [
            ...copy,
            {
              id: `err_${Date.now()}`,
              role: "assistant",
              content: message,
              blocks: [{ id: `err_${Date.now()}`, type: "text", text: message }],
              createdAt: new Date().toISOString(),
            },
          ];
        });
        opts?.onError?.(message);
      } finally {
        setIsStreaming(false);
      }
    },
    [isStreaming]
  );

  // `open` needs to call `sendMessage`, so use a ref to avoid stale closure.
  const sendMessageRef = useRef(sendMessage);
  sendMessageRef.current = sendMessage;

  const open = useCallback(
    (opts?: { message?: string; context?: Record<string, unknown> }) => {
      setIsOpen(true);
      if (opts?.message) {
        void sendMessageRef.current(opts.message, opts.context ? { context: opts.context } : undefined);
      }
    },
    []
  );

  const value = useMemo<AiCoachContextValue>(
    () => ({
      isOpen,
      open,
      close,
      toggle,
      isStreaming,
      messages,
      sendMessage,
      reset,
      sessionId: sessionIdRef.current,
    }),
    [isOpen, open, close, toggle, isStreaming, messages, sendMessage, reset]
  );

  return <AiCoachContext.Provider value={value}>{children}</AiCoachContext.Provider>;
}

export function useAiCoach(): AiCoachContextValue {
  const ctx = useContext(AiCoachContext);
  if (!ctx) {
    throw new Error("useAiCoach must be used within an AiCoachProvider");
  }
  return ctx;
}
