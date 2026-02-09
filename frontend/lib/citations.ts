import type { RetrievedDocument } from "@/lib/api";
import type {
  Citation,
  CitedText,
  CitationMetadata,
  SUKLMetadata,
  PubMedMetadata,
  GuidelinesMetadata,
  TextSegment,
} from "@/lib/types/citations";

export function formatSUKLCitation(
  metadata: SUKLMetadata,
  number: number
): Citation {
  const shortCitation = `SUKL Reg. ${metadata.registration_number}`;
  const url =
    metadata.url ||
    `https://www.sukl.cz/modules/medication/detail.php?code=${metadata.registration_number}`;
  const fullCitation =
    `[${number}] SUKL - ${metadata.source_type}. ` +
    `Registracni cislo: ${metadata.registration_number}. ${url}`;

  return { number, metadata, shortCitation, fullCitation, page_content: "" };
}

export function formatPubMedCitation(
  metadata: PubMedMetadata,
  number: number
): Citation {
  const year = metadata.publication_date?.slice(0, 4) || "Unknown";
  const firstAuthor = metadata.authors?.split(",")[0]?.trim() || "Unknown";

  const shortCitation = `${firstAuthor} et al. (${year})`;
  const fullCitation =
    `[${number}] ${metadata.authors}. ${metadata.title}. ` +
    `${metadata.journal}. ${year}. PMID: ${metadata.pmid}. ${metadata.url}`;

  return { number, metadata, shortCitation, fullCitation, page_content: "" };
}

export function formatGuidelinesCitation(
  metadata: GuidelinesMetadata,
  number: number
): Citation {
  const sourceNames: Record<string, string> = {
    cls_jep: "CLS JEP",
    esc: "European Society of Cardiology",
    ers: "European Respiratory Society",
  };

  const sourceName =
    sourceNames[metadata.source] || metadata.source.toUpperCase();
  const year = metadata.publication_date?.slice(0, 4) || "Unknown";

  const shortCitation = `${sourceName} ${metadata.guideline_id}`;
  const fullCitation =
    `[${number}] ${sourceName}. ${metadata.guideline_id}. ` +
    `${year}. ${metadata.url}`;

  return { number, metadata, shortCitation, fullCitation, page_content: "" };
}

function isSUKLMetadata(metadata: CitationMetadata): metadata is SUKLMetadata {
  return metadata.source === "sukl";
}

function isPubMedMetadata(
  metadata: CitationMetadata
): metadata is PubMedMetadata {
  return metadata.source === "PubMed";
}

export function parseCitations(
  answer: string,
  retrievedDocs: RetrievedDocument[]
): CitedText {
  const citations: Citation[] = retrievedDocs.map((doc, index) => {
    const number = index + 1;
    const metadata = doc.metadata as CitationMetadata;

    let citation: Citation;
    if (isSUKLMetadata(metadata)) {
      citation = formatSUKLCitation(metadata, number);
    } else if (isPubMedMetadata(metadata)) {
      citation = formatPubMedCitation(metadata, number);
    } else {
      citation = formatGuidelinesCitation(
        metadata as GuidelinesMetadata,
        number
      );
    }

    citation.page_content = doc.page_content;
    return citation;
  });

  const citationPattern = /\[(\d+)\]/g;
  const segments: TextSegment[] = [];
  let lastIndex = 0;

  let match;
  while ((match = citationPattern.exec(answer)) !== null) {
    if (match.index > lastIndex) {
      segments.push({
        type: "text",
        content: answer.slice(lastIndex, match.index),
      });
    }

    const citationNumber = parseInt(match[1]!, 10);
    segments.push({
      type: "citation",
      content: match[0],
      citationNumber,
    });

    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < answer.length) {
    segments.push({
      type: "text",
      content: answer.slice(lastIndex),
    });
  }

  return { text: answer, citations, segments };
}
