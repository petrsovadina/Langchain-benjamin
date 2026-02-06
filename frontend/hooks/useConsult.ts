import { useState, useCallback, useRef, useEffect } from "react";
import {
  sendMessage,
  type ConsultRequest,
  type SSEEvent,
  type RetrievedDocument,
} from "@/lib/api";

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

const MAX_RETRIES = 3;

function isRetryableError(err: Error): boolean {
  const msg = err.message.toLowerCase();
  return (
    msg.includes("network") ||
    msg.includes("fetch") ||
    msg.includes("timeout") ||
    msg.includes("failed to fetch") ||
    msg.includes("503") ||
    msg.includes("502") ||
    msg.includes("429")
  );
}

export function useConsult() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [agentStatuses, setAgentStatuses] = useState<AgentStatus[]>([]);
  const retryCountRef = useRef(0);
  const lastQueryRef = useRef<{ query: string; mode: "quick" | "deep" } | null>(null);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isAutoRetryingRef = useRef(false);

  useEffect(() => {
    return () => {
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
    };
  }, []);

  const executeQuery = useCallback(
    async (query: string, mode: "quick" | "deep", assistantMessageId: string) => {
      isAutoRetryingRef.current = false;
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
            retryCountRef.current = 0;
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
          } else if (event.type === "cache_hit") {
            console.log("Cache hit");
          }
        },
        (err: Error) => {
          if (isRetryableError(err) && retryCountRef.current < MAX_RETRIES) {
            retryCountRef.current += 1;
            isAutoRetryingRef.current = true;
            const delay = Math.min(1000 * 2 ** (retryCountRef.current - 1), 8000);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId ? { ...msg, content: "" } : msg
              )
            );
            setAgentStatuses([]);
            retryTimerRef.current = setTimeout(() => {
              executeQuery(query, mode, assistantMessageId);
            }, delay);
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
          if (!isAutoRetryingRef.current) {
            setIsLoading(false);
            setAgentStatuses([]);
          }
        }
      );
    },
    []
  );

  const sendQuery = useCallback(
    async (query: string, mode: "quick" | "deep" = "quick") => {
      setIsLoading(true);
      setError(null);
      setAgentStatuses([]);
      retryCountRef.current = 0;
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
    [executeQuery]
  );

  const retry = useCallback(() => {
    if (lastQueryRef.current) {
      setMessages((prev) => prev.slice(0, -2));
      retryCountRef.current = 0;
      setError(null);
      sendQuery(lastQueryRef.current.query, lastQueryRef.current.mode);
    }
  }, [sendQuery]);

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
