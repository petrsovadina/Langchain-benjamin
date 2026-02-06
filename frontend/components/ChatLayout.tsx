"use client";

import { ReactNode } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";

interface ChatLayoutProps {
  children: ReactNode;
  isZenMode: boolean;
}

export function ChatLayout({ children, isZenMode }: ChatLayoutProps) {
  return (
    <div className="h-screen flex flex-col bg-slate-50 dark:bg-slate-950">
      <header className="border-b border-slate-200 dark:border-slate-800 px-6 py-4">
        <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
          Czech MedAI
        </h1>
      </header>

      <main className="flex-1 flex flex-col overflow-hidden">
        {isZenMode ? (
          <div className="flex-1 flex items-center justify-center">
            {children}
          </div>
        ) : (
          <div className="flex-1 flex flex-col">
            <ScrollArea className="flex-1 px-6 py-8">{children}</ScrollArea>
          </div>
        )}
      </main>
    </div>
  );
}
