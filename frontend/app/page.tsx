"use client";

import { useEffect } from "react";
import { Omnibox } from "@/components/Omnibox";
import { ChatLayout } from "@/components/ChatLayout";
import { UserMessage } from "@/components/UserMessage";
import { AssistantMessage } from "@/components/AssistantMessage";
import { AgentThoughtStream } from "@/components/AgentThoughtStream";
import { useConsult } from "@/hooks/useConsult";

export default function HomePage() {
  const { messages, isLoading, agentStatuses, sendQuery } = useConsult();

  const isZenMode = messages.length === 0;

  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isZenMode) {
        console.log("Escape pressed");
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, [isZenMode]);

  return (
    <ChatLayout isZenMode={isZenMode}>
      <AgentThoughtStream agents={agentStatuses} />

      {!isZenMode && (
        <div className="space-y-6 mb-32">
          {messages.map((msg) =>
            msg.role === "user" ? (
              <UserMessage
                key={msg.id}
                content={msg.content}
                timestamp={msg.timestamp}
              />
            ) : (
              <AssistantMessage
                key={msg.id}
                content={msg.content}
                timestamp={msg.timestamp}
                latency_ms={msg.latency_ms}
                isLoading={!msg.content && isLoading}
              />
            )
          )}
        </div>
      )}

      <Omnibox
        onSubmit={sendQuery}
        isLoading={isLoading}
        isActive={!isZenMode}
      />
    </ChatLayout>
  );
}
