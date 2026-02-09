export type SUKLMetadata = {
  source: "sukl";
  source_type: "drug_search" | "drug_details" | "reimbursement" | "availability";
  registration_number: string;
  atc_code?: string;
  url?: string;
  [key: string]: unknown;
};

export type PubMedMetadata = {
  source: "PubMed";
  pmid: string;
  url: string;
  title: string;
  authors: string;
  journal: string;
  publication_date: string;
  doi?: string;
  [key: string]: unknown;
};

export type GuidelinesMetadata = {
  source: "cls_jep" | "esc" | "ers";
  source_type: "clinical_guidelines";
  guideline_id: string;
  url: string;
  publication_date: string;
  [key: string]: unknown;
};

export type CitationMetadata = SUKLMetadata | PubMedMetadata | GuidelinesMetadata;

export interface Citation {
  number: number;
  metadata: CitationMetadata;
  page_content: string;
  shortCitation: string;
  fullCitation: string;
}

export interface TextSegment {
  type: "text" | "citation";
  content: string;
  citationNumber?: number;
}

export interface CitedText {
  text: string;
  citations: Citation[];
  segments: TextSegment[];
}
