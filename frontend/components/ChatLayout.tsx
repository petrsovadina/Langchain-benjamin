"use client";

import { ReactNode, type Ref } from "react";
import { useSwipeGesture } from "@/hooks/useSwipeGesture";

interface ChatLayoutProps {
  children: ReactNode;
  isZenMode: boolean;
  onSwipeDown?: () => void;
  scrollContainerRef?: Ref<HTMLDivElement>;
}

export function ChatLayout({ children, isZenMode, onSwipeDown, scrollContainerRef }: ChatLayoutProps) {
  const { onPointerDown, onPointerUp } = useSwipeGesture({
    onSwipeDown,
  });

  return (
    <div
      className="h-screen flex flex-col bg-surface"
      data-testid="chat-container"
      onPointerDown={onPointerDown}
      onPointerUp={onPointerUp}
    >
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md"
      >
        Přeskočit na hlavní obsah
      </a>

      <header className="border-b border-default px-4 md:px-6 py-4">
        <h1 className="text-lg md:text-xl font-semibold text-primary">
          Czech MedAI
        </h1>
      </header>

      <main id="main-content" className="flex-1 flex flex-col overflow-hidden">
        {isZenMode ? (
          <div className="flex-1 flex items-center justify-center">
            {children}
          </div>
        ) : (
          <div
            ref={scrollContainerRef}
            className="flex-1 overflow-y-auto px-4 md:px-6 py-8 scroll-smooth"
          >
            {children}
          </div>
        )}
      </main>
    </div>
  );
}
