"use client";

import { ReactNode } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useSwipeGesture } from "@/hooks/useSwipeGesture";

interface ChatLayoutProps {
  children: ReactNode;
  isZenMode: boolean;
  onSwipeDown?: () => void;
}

export function ChatLayout({ children, isZenMode, onSwipeDown }: ChatLayoutProps) {
  const { onPointerDown, onPointerUp } = useSwipeGesture({
    onSwipeDown,
  });

  return (
    <div
      className="h-screen flex flex-col bg-slate-50 dark:bg-slate-950"
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

      <header className="border-b border-slate-200 dark:border-slate-800 px-4 md:px-6 py-4">
        <h1 className="text-lg md:text-xl font-semibold text-slate-900 dark:text-slate-100">
          Czech MedAI
        </h1>
      </header>

      <main id="main-content" className="flex-1 flex flex-col overflow-hidden">
        {isZenMode ? (
          <div className="flex-1 flex items-center justify-center">
            {children}
          </div>
        ) : (
          <div className="flex-1 flex flex-col">
            <ScrollArea className="flex-1 px-4 md:px-6 py-8">{children}</ScrollArea>
          </div>
        )}
      </main>
    </div>
  );
}
