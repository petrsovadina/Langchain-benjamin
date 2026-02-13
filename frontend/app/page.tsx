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

const SCROLL_THRESHOLD = 150; // px from bottom to trigger auto-scroll

export default function HomePage() {
  const { messages, isLoading, error, agentStatuses, sendQuery, retry } = useConsult();
  const omniboxRef = useRef<OmniboxHandle>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const isUserNearBottomRef = useRef(true);

  const isZenMode = messages.length === 0;

  // Track whether user is near the bottom of the scroll area
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      isUserNearBottomRef.current =
        scrollHeight - scrollTop - clientHeight < SCROLL_THRESHOLD;
    };

    container.addEventListener("scroll", handleScroll, { passive: true });
    return () => container.removeEventListener("scroll", handleScroll);
  }, [isZenMode]);

  // Auto-scroll to bottom only when user is near bottom
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (container && isUserNearBottomRef.current) {
      container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
    }
  }, [messages.length, isLoading]);

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
      <ChatLayout
        isZenMode={isZenMode}
        onSwipeDown={handleSwipeDown}
        scrollContainerRef={scrollContainerRef}
      >
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
