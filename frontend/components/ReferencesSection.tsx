import { Card } from "@/components/ui/card";
import type { Citation } from "@/lib/types/citations";
import { ExternalLink } from "lucide-react";

interface ReferencesSectionProps {
  citations: Citation[];
}

export function ReferencesSection({ citations }: ReferencesSectionProps) {
  if (citations.length === 0) return null;

  return (
    <Card className="mt-6 p-4 bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-700">
      <h3 className="text-lg font-semibold mb-3 text-slate-900 dark:text-slate-100">
        Reference
      </h3>
      <ol className="space-y-3">
        {citations.map((citation) => (
          <li key={citation.number} className="text-sm">
            <div className="flex items-start gap-2">
              <span className="font-medium text-slate-700 dark:text-slate-300 min-w-[2rem]">
                [{citation.number}]
              </span>
              <div className="flex-1">
                <p className="text-slate-900 dark:text-slate-100">
                  {citation.fullCitation}
                </p>
                {"url" in citation.metadata && citation.metadata.url && (
                  <a
                    href={citation.metadata.url as string}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 mt-1 text-xs text-blue-600 hover:underline"
                  >
                    <ExternalLink className="h-3 w-3" />
                    Otevrit zdroj
                  </a>
                )}
              </div>
            </div>
          </li>
        ))}
      </ol>
    </Card>
  );
}
