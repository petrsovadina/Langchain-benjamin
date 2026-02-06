"use client";

import { Badge } from "@/components/ui/badge";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import type { Citation } from "@/lib/types/citations";

interface CitationBadgeProps {
  citation: Citation;
  onClick?: () => void;
}

export function CitationBadge({ citation, onClick }: CitationBadgeProps) {
  return (
    <HoverCard>
      <HoverCardTrigger asChild>
        <Badge
          variant="outline"
          className="cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900 active:bg-blue-100 dark:active:bg-blue-800 mx-0.5 text-xs md:text-sm px-2 py-1 md:px-3 md:py-1.5 min-h-[44px] min-w-[44px] inline-flex items-center justify-center text-blue-600 dark:text-blue-400"
          data-testid="citation-badge"
          onClick={onClick}
          onKeyDown={(e) => {
            if ((e.key === "Enter" || e.key === " ") && onClick) {
              e.preventDefault();
              onClick();
            }
          }}
          role="button"
          tabIndex={0}
          aria-label={`Citace ${citation.number}: ${citation.shortCitation}`}
          aria-haspopup="dialog"
        >
          [{citation.number}]
        </Badge>
      </HoverCardTrigger>
      <HoverCardContent className="w-80">
        <div className="space-y-2">
          <p className="text-sm font-medium">{citation.shortCitation}</p>
          <p className="text-xs text-slate-600 dark:text-slate-400">
            {citation.fullCitation}
          </p>
          {"url" in citation.metadata && citation.metadata.url && (
            <a
              href={citation.metadata.url as string}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-600 hover:underline"
            >
              Otevrit zdroj &rarr;
            </a>
          )}
        </div>
      </HoverCardContent>
    </HoverCard>
  );
}
