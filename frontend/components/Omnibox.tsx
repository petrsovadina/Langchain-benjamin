"use client";

import { useState, useRef, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Mic, Paperclip, Send } from "lucide-react";

interface OmniboxProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
  isActive: boolean;
}

export function Omnibox({ onSubmit, isLoading, isActive }: OmniboxProps) {
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === "/" && document.activeElement !== inputRef.current) {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
      setQuery("");
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={`
        w-full max-w-3xl mx-auto px-4 sm:px-0
        transition-all duration-500 ease-out
        ${isActive ? "fixed bottom-4 sm:bottom-8 left-1/2 -translate-x-1/2 z-40" : ""}
      `}
    >
      <div className="relative flex items-center gap-2 bg-white dark:bg-slate-900 rounded-full shadow-lg border border-slate-200 dark:border-slate-700 px-4 py-3">
        <Input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Zadejte lékařský dotaz..."
          disabled={isLoading}
          className="flex-1 border-0 focus-visible:ring-0 text-base bg-transparent"
          autoFocus
        />

        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="text-slate-400 hover:text-slate-600"
            disabled={isLoading}
          >
            <Mic className="h-5 w-5" />
          </Button>

          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="text-slate-400 hover:text-slate-600"
            disabled={isLoading}
          >
            <Paperclip className="h-5 w-5" />
          </Button>

          <Button
            type="submit"
            size="icon"
            disabled={isLoading || !query.trim()}
            className="rounded-full"
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </form>
  );
}
