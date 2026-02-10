import { useState, useCallback, useRef } from "react";
import {
  sendMessage,
  type ConsultRequest,
  type SSEEvent,
  type RetrievedDocument,
} from "@/lib/api";
import { useRetry } from "./useRetry";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  retrieved_docs?: RetrievedDocument[];
  latency_ms?: number;
  timestamp: Date;
}

export interface AgentStatus {
  name: string;
  status: "idle" | "running" | "complete";
}

export function useConsult() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [agentStatuses, setAgentStatuses] = useState<AgentStatus[]>([]);
  const lastQueryRef = useRef<{ query: string; mode: "quick" | "deep" } | null>(null);

  const { isAutoRetrying, scheduleRetry, resetRetry, shouldRetry } = useRetry({
    maxRetries: 3,
    baseDelayMs: 1000,
    maxDelayMs: 8000,
  });

  const executeQuery = useCallback(
    async (query: string, mode: "quick" | "deep", assistantMessageId: string) => {
      const request: ConsultRequest = { query, mode };

      await sendMessage(
        request,
        (event: SSEEvent) => {
          if (event.type === "agent_start" && event.agent) {
            setAgentStatuses((prev) => [
              ...prev.filter((a) => a.name !== event.agent),
              { name: event.agent!, status: "running" },
            ]);
          } else if (event.type === "agent_complete" && event.agent) {
            setAgentStatuses((prev) =>
              prev.map((a) =>
                a.name === event.agent ? { ...a, status: "complete" } : a
              )
            );
          } else if (event.type === "final") {
            resetRetry();
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? {
                      ...msg,
                      content: event.answer || "",
                      retrieved_docs: event.retrieved_docs,
                      latency_ms: event.latency_ms,
                    }
                  : msg
              )
            );
          }
        },
        (err: Error) => {
          if (shouldRetry(err)) {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId ? { ...msg, content: "" } : msg
              )
            );
            setAgentStatuses([]);
            scheduleRetry(() => {
              executeQuery(query, mode, assistantMessageId);
            });
          } else {
            setError(err);
            setIsLoading(false);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: `Chyba: ${err.message}` }
                  : msg
              )
            );
            setAgentStatuses([]);
          }
        },
        () => {
          if (!isAutoRetrying) {
            setIsLoading(false);
            setAgentStatuses([]);
          }
        }
      );
    },
    [resetRetry, shouldRetry, scheduleRetry, isAutoRetrying]
  );

  const sendQuery = useCallback(
    async (query: string, mode: "quick" | "deep" = "quick") => {
      setIsLoading(true);
      setError(null);
      setAgentStatuses([]);
      resetRetry();
      lastQueryRef.current = { query, mode };

      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: query,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);

      const assistantMessageId = crypto.randomUUID();
      const assistantMessage: Message = {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      await executeQuery(query, mode, assistantMessageId);
    },
    [executeQuery, resetRetry]
  );

  const retry = useCallback(() => {
    if (lastQueryRef.current) {
      setMessages((prev) => prev.slice(0, -2));
      resetRetry();
      setError(null);
      sendQuery(lastQueryRef.current.query, lastQueryRef.current.mode);
    }
  }, [sendQuery, resetRetry]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    agentStatuses,
    sendQuery,
    retry,
    clearMessages,
  };
}
