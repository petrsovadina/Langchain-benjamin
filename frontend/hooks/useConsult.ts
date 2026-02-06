import { useState, useCallback } from "react";
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

export function useConsult() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [agentStatuses, setAgentStatuses] = useState<AgentStatus[]>([]);

  const sendQuery = useCallback(
    async (query: string, mode: "quick" | "deep" = "quick") => {
      setIsLoading(true);
      setError(null);
      setAgentStatuses([]);

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
        },
        () => {
          setIsLoading(false);
          setAgentStatuses([]);
        }
      );
    },
    []
  );

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
    clearMessages,
  };
}
