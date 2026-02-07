"use client";

import { useState, useRef, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Mic, Paperclip, Send, RefreshCw, Loader2, AlertCircle, WifiOff } from "lucide-react";
import { cn } from "@/lib/utils";
import { useOnlineStatus } from "@/hooks/useOnlineStatus";

interface OmniboxProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
  isActive: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export function Omnibox({ onSubmit, isLoading, isActive, error, onRetry }: OmniboxProps) {
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const isOnline = useOnlineStatus();

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
    if (query.trim() && !isLoading && isOnline) {
      onSubmit(query.trim());
      setQuery("");
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      role="search"
      aria-label="Lékařský dotaz"
      aria-busy={isLoading}
      className={`
        w-full max-w-3xl mx-auto px-4 sm:px-0 pb-safe
        transition-all duration-500 ease-out
        ${isActive ? "fixed bottom-4 md:bottom-8 left-1/2 -translate-x-1/2 z-40" : ""}
      `}
    >
      {!isOnline && (
        <div
          className="mb-2 bg-destructive/10 border border-destructive rounded-lg px-4 py-2 text-sm text-destructive flex items-center gap-2 animate-pulse animate-in slide-in-from-top-2"
          role="alert"
          aria-live="polite"
        >
          <WifiOff className="h-4 w-4 shrink-0" aria-hidden="true" />
          Jste offline. Připojte se k internetu pro odeslání dotazu.
        </div>
      )}

      {error && (
        <div
          className="mb-2 flex items-center gap-2 bg-destructive/10 border border-destructive rounded-lg px-4 py-2 text-sm text-destructive animate-in slide-in-from-top-2"
          role="alert"
          aria-live="assertive"
        >
          <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
          <span className="flex-1">{error}</span>
          {onRetry && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={onRetry}
              className="shrink-0 text-destructive hover:text-destructive hover:bg-destructive/20"
              aria-label="Zkusit znovu"
            >
              <RefreshCw className="h-4 w-4 mr-1" aria-hidden="true" />
              Znovu
            </Button>
          )}
        </div>
      )}

      <div
        className={cn(
          "relative flex items-center gap-1 md:gap-2",
          "bg-white dark:bg-slate-900 rounded-full shadow-lg",
          "border border-slate-200 dark:border-slate-700",
          "px-4 py-3 transition-all duration-200",
          "focus-within:border-primary focus-within:ring-2 focus-within:ring-ring/20"
        )}
        data-testid="omnibox"
      >
        <Input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={!isOnline ? "Offline - připojte se k internetu" : isLoading ? "Zpracovávám dotaz..." : "Zadejte lékařský dotaz..."}
          disabled={isLoading || !isOnline}
          aria-label="Zadejte lékařský dotaz"
          aria-describedby="omnibox-hint"
          aria-invalid={error ? "true" : "false"}
          className="flex-1 border-0 focus-visible:ring-0 text-base bg-transparent"
          autoFocus
        />
        <span id="omnibox-hint" className="sr-only">
          Stiskněte Enter pro odeslání nebo / pro zaměření
        </span>

        <div className="flex items-center gap-1 md:gap-2">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="text-slate-400 hover:text-slate-600 active:bg-slate-100 dark:active:bg-slate-800 min-h-[44px] min-w-[44px]"
            disabled={isLoading}
            aria-label="Hlasový vstup"
          >
            <Mic className="h-5 w-5" aria-hidden="true" />
          </Button>

          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="text-slate-400 hover:text-slate-600 active:bg-slate-100 dark:active:bg-slate-800 min-h-[44px] min-w-[44px]"
            disabled={isLoading}
            aria-label="Přiložit soubor"
          >
            <Paperclip className="h-5 w-5" aria-hidden="true" />
          </Button>

          <Button
            type="submit"
            size="icon"
            disabled={isLoading || !query.trim() || !isOnline}
            className="rounded-full min-h-[44px] min-w-[44px]"
            aria-label="Odeslat dotaz"
            aria-disabled={isLoading || !query.trim() || !isOnline}
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
            ) : (
              <Send className="h-5 w-5" aria-hidden="true" />
            )}
          </Button>
        </div>
      </div>
    </form>
  );
}
