"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { Citation } from "@/lib/types/citations";
import { ExternalLink } from "lucide-react";

interface CitationPopupProps {
  citation: Citation | null;
  open: boolean;
  onClose: () => void;
}

export function CitationPopup({ citation, open, onClose }: CitationPopupProps) {
  if (!citation) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Citace [{citation.number}]</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Kratka citace
            </h4>
            <p className="text-sm">{citation.shortCitation}</p>
          </div>

          <div>
            <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Uplna citace
            </h4>
            <p className="text-sm">{citation.fullCitation}</p>
          </div>

          <SourceDetails citation={citation} />

          {"url" in citation.metadata && citation.metadata.url && (
            <a
              href={citation.metadata.url as string}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm text-blue-600 hover:underline"
            >
              <ExternalLink className="h-4 w-4" />
              Otevrit zdroj
            </a>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function SourceDetails({ citation }: { citation: Citation }) {
  const { metadata } = citation;

  if (metadata.source === "sukl") {
    return (
      <div>
        <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">
          SUKL Detaily
        </h4>
        <dl className="text-sm space-y-1">
          <div>
            <dt className="inline font-medium">Reg. cislo:</dt>{" "}
            <dd className="inline">{metadata.registration_number}</dd>
          </div>
          {metadata.atc_code && (
            <div>
              <dt className="inline font-medium">ATC kod:</dt>{" "}
              <dd className="inline">{metadata.atc_code}</dd>
            </div>
          )}
        </dl>
      </div>
    );
  }

  if (metadata.source === "PubMed") {
    return (
      <div>
        <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">
          PubMed Detaily
        </h4>
        <dl className="text-sm space-y-1">
          <div>
            <dt className="inline font-medium">PMID:</dt>{" "}
            <dd className="inline">{metadata.pmid}</dd>
          </div>
          <div>
            <dt className="inline font-medium">Autori:</dt>{" "}
            <dd className="inline">{metadata.authors}</dd>
          </div>
          <div>
            <dt className="inline font-medium">Casopis:</dt>{" "}
            <dd className="inline">{metadata.journal}</dd>
          </div>
          <div>
            <dt className="inline font-medium">Datum:</dt>{" "}
            <dd className="inline">{metadata.publication_date}</dd>
          </div>
          {metadata.doi && (
            <div>
              <dt className="inline font-medium">DOI:</dt>{" "}
              <dd className="inline">{metadata.doi}</dd>
            </div>
          )}
        </dl>
      </div>
    );
  }

  // Guidelines
  const guidelinesMeta = metadata as {
    source: string;
    guideline_id: string;
    publication_date: string;
  };
  return (
    <div>
      <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">
        Guidelines Detaily
      </h4>
      <dl className="text-sm space-y-1">
        <div>
          <dt className="inline font-medium">ID:</dt>{" "}
          <dd className="inline">{guidelinesMeta.guideline_id}</dd>
        </div>
        <div>
          <dt className="inline font-medium">Zdroj:</dt>{" "}
          <dd className="inline">
            {guidelinesMeta.source.toUpperCase()}
          </dd>
        </div>
        <div>
          <dt className="inline font-medium">Datum:</dt>{" "}
          <dd className="inline">{guidelinesMeta.publication_date}</dd>
        </div>
      </dl>
    </div>
  );
}
