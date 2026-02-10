"use client";

import { useEffect, useCallback, useRef } from "react";
import dynamic from "next/dynamic";
import { Omnibox } from "@/components/Omnibox";
import type { OmniboxHandle } from "@/components/Omnibox";
import { ChatLayout } from "@/components/ChatLayout";
import { UserMessage } from "@/components/UserMessage";
import { AssistantMessage } from "@/components/AssistantMessage";
import { ProgressBar } from "@/components/ProgressBar";
import { useConsult } from "@/hooks/useConsult";

const AgentThoughtStream = dynamic(
  () =>
    import("@/components/AgentThoughtStream").then((mod) => ({
      default: mod.AgentThoughtStream,
    })),
  { ssr: false }
);

export default function HomePage() {
  const { messages, isLoading, error, agentStatuses, sendQuery, retry } = useConsult();
  const omniboxRef = useRef<OmniboxHandle>(null);

  const isZenMode = messages.length === 0;

  const handleSwipeDown = useCallback(() => {
    omniboxRef.current?.focus();
  }, []);

  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isZenMode) {
        omniboxRef.current?.focus();
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, [isZenMode]);

  return (
    <>
      <ProgressBar isLoading={isLoading} />
      <ChatLayout isZenMode={isZenMode} onSwipeDown={handleSwipeDown}>
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
                  retrieved_docs={msg.retrieved_docs}
                />
              )
            )}
          </div>
        )}

        <Omnibox
          ref={omniboxRef}
          onSubmit={sendQuery}
          isLoading={isLoading}
          isActive={!isZenMode}
          error={error?.message}
          onRetry={retry}
        />
      </ChatLayout>
    </>
  );
}
