"use client";

import { useState, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { RetrievedDocument } from "@/lib/api";
import { parseCitations } from "@/lib/citations";
import type { Citation } from "@/lib/types/citations";
import { CitationBadge } from "./CitationBadge";
import { CitationPopup } from "./CitationPopup";
import { ReferencesSection } from "./ReferencesSection";

interface CitedResponseProps {
  answer: string;
  retrievedDocs: RetrievedDocument[];
}

export function CitedResponse({ answer, retrievedDocs }: CitedResponseProps) {
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(
    null
  );
  const [popupOpen, setPopupOpen] = useState(false);

  const { segments, citations } = useMemo(
    () => parseCitations(answer, retrievedDocs),
    [answer, retrievedDocs]
  );

  const citationMap = useMemo(
    () => new Map(citations.map((c) => [c.number, c])),
    [citations]
  );

  const handleCitationClick = (citation: Citation) => {
    setSelectedCitation(citation);
    setPopupOpen(true);
  };

  return (
    <div className="space-y-4">
      <div className="prose prose-sm dark:prose-invert max-w-none">
        {segments.map((segment, index) => {
          if (segment.type === "text") {
            return (
              <ReactMarkdown key={index} remarkPlugins={[remarkGfm]}>
                {segment.content}
              </ReactMarkdown>
            );
          }

          const citation = citationMap.get(segment.citationNumber);
          if (!citation) return null;

          return (
            <CitationBadge
              key={index}
              citation={citation}
              onClick={() => handleCitationClick(citation)}
            />
          );
        })}
      </div>

      <ReferencesSection citations={citations} />

      <CitationPopup
        citation={selectedCitation}
        open={popupOpen}
        onClose={() => setPopupOpen(false)}
      />
    </div>
  );
}
