import { Card } from "@/components/ui/card";
import { Bot } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { CitedResponse } from "./CitedResponse";
import type { RetrievedDocument } from "@/lib/api";

interface AssistantMessageProps {
  content: string;
  timestamp: Date;
  latency_ms?: number;
  isLoading?: boolean;
  retrieved_docs?: RetrievedDocument[];
}

export function AssistantMessage({
  content,
  timestamp,
  latency_ms,
  isLoading,
  retrieved_docs = [],
}: AssistantMessageProps) {
  return (
    <div className="flex items-start gap-3" data-testid="assistant-message">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
        <Bot className="h-4 w-4 text-white" />
      </div>
      <Card className="max-w-2xl bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 px-4 py-3">
        {isLoading ? (
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <div className="animate-pulse">Zpracovavam dotaz...</div>
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
