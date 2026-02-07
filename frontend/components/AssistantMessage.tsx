import { Card } from "@/components/ui/card";
import { Bot } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { CitedResponse } from "./CitedResponse";
import { MessageSkeleton } from "./MessageSkeleton";
import { cn } from "@/lib/utils";
import type { RetrievedDocument } from "@/lib/api";

interface AssistantMessageProps {
  content: string;
  timestamp: Date;
  latency_ms?: number;
  isLoading?: boolean;
  isStreaming?: boolean;
  retrieved_docs?: RetrievedDocument[];
}

export function AssistantMessage({
  content,
  timestamp,
  latency_ms,
  isLoading,
  isStreaming,
  retrieved_docs = [],
}: AssistantMessageProps) {
  if (isLoading && !content) {
    return <MessageSkeleton />;
  }

  return (
    <div
      className="flex items-start gap-3"
      data-testid="assistant-message"
      role="article"
      aria-label="Odpověď asistenta"
      aria-live={isLoading || isStreaming ? "polite" : "off"}
      aria-busy={isLoading || isStreaming}
    >
      <div className={cn(
        "flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center",
        isStreaming && "animate-pulse"
      )}>
        <Bot className="h-4 w-4 text-white" aria-hidden="true" />
      </div>
      <Card className={cn(
        "max-w-2xl bg-white dark:bg-slate-900 px-4 py-3",
        "border-slate-200 dark:border-slate-700",
        !isLoading && !isStreaming && retrieved_docs.length > 0
          ? "border-l-4 border-l-citation-badge-text"
          : !isLoading && !isStreaming
            ? "border-l-4 border-l-slate-300 dark:border-l-slate-600"
            : ""
      )}>
        {isStreaming ? (
          <div className="flex items-center gap-2 text-sm text-slate-500" data-testid="streaming-indicator">
            <div className="flex gap-1">
              <span className="h-2 w-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="h-2 w-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="h-2 w-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
            <span>Píšu odpověď...</span>
            <span className="sr-only">Asistent píše odpověď</span>
          </div>
        ) : isLoading ? (
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <div className="animate-pulse">Zpracovávám dotaz...</div>
            <div className="sr-only">Načítám odpověď...</div>
          </div>
        ) : (
          <>
            {retrieved_docs.length > 0 ? (
              <CitedResponse answer={content} retrievedDocs={retrieved_docs} />
            ) : (
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {content}
                </ReactMarkdown>
              </div>
            )}
            <div className="flex items-center gap-2 mt-2 text-xs text-slate-500 dark:text-slate-400">
              <time>
                {timestamp.toLocaleTimeString("cs-CZ", {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </time>
              {latency_ms && (
                <span>&bull; {(latency_ms / 1000).toFixed(1)}s</span>
              )}
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
