import {
  formatSUKLCitation,
  formatPubMedCitation,
  formatGuidelinesCitation,
  parseCitations,
} from "@/lib/citations";
import type {
  SUKLMetadata,
  PubMedMetadata,
  GuidelinesMetadata,
} from "@/lib/types/citations";

describe("Citation Formatting", () => {
  test("formatSUKLCitation", () => {
    const metadata: SUKLMetadata = {
      source: "sukl",
      source_type: "drug_search",
      registration_number: "0012345",
      atc_code: "M01AE01",
    };

    const citation = formatSUKLCitation(metadata, 1);

    expect(citation.number).toBe(1);
    expect(citation.shortCitation).toContain("SUKL Reg. 0012345");
    expect(citation.fullCitation).toContain("[1]");
    expect(citation.fullCitation).toContain("0012345");
    expect(citation.fullCitation).toContain("sukl.cz");
  });

  test("formatSUKLCitation with custom url", () => {
    const metadata: SUKLMetadata = {
      source: "sukl",
      source_type: "drug_details",
      registration_number: "9876543",
      url: "https://custom.sukl.cz/detail/9876543",
    };

    const citation = formatSUKLCitation(metadata, 2);

    expect(citation.number).toBe(2);
    expect(citation.fullCitation).toContain("custom.sukl.cz");
  });

  test("formatPubMedCitation", () => {
    const metadata: PubMedMetadata = {
      source: "PubMed",
      pmid: "12345678",
      url: "https://pubmed.ncbi.nlm.nih.gov/12345678",
      title: "Test Article",
      authors: "Smith, John; Doe, Jane",
      journal: "NEJM",
      publication_date: "2024-06-15",
    };

    const citation = formatPubMedCitation(metadata, 2);

    expect(citation.number).toBe(2);
    expect(citation.shortCitation).toContain("Smith et al. (2024)");
    expect(citation.fullCitation).toContain("PMID: 12345678");
    expect(citation.fullCitation).toContain("[2]");
    expect(citation.fullCitation).toContain("NEJM");
  });

  test("formatPubMedCitation handles missing date", () => {
    const metadata: PubMedMetadata = {
      source: "PubMed",
      pmid: "99999999",
      url: "https://pubmed.ncbi.nlm.nih.gov/99999999",
      title: "Unknown Date Article",
      authors: "Doe, Jane",
      journal: "Nature",
      publication_date: "",
    };

    const citation = formatPubMedCitation(metadata, 1);

    expect(citation.shortCitation).toContain("Unknown");
  });

  test("formatGuidelinesCitation", () => {
    const metadata: GuidelinesMetadata = {
      source: "cls_jep",
      source_type: "clinical_guidelines",
      guideline_id: "CLS-JEP-2024-001",
      url: "https://www.cls.cz/guidelines/001",
      publication_date: "2024-01-15",
    };

    const citation = formatGuidelinesCitation(metadata, 3);

    expect(citation.number).toBe(3);
    expect(citation.shortCitation).toContain("CLS JEP");
    expect(citation.shortCitation).toContain("CLS-JEP-2024-001");
    expect(citation.fullCitation).toContain("[3]");
    expect(citation.fullCitation).toContain("2024");
  });

  test("formatGuidelinesCitation with ESC source", () => {
    const metadata: GuidelinesMetadata = {
      source: "esc",
      source_type: "clinical_guidelines",
      guideline_id: "ESC-HF-2023",
      url: "https://www.escardio.org/guidelines/hf-2023",
      publication_date: "2023-08-01",
    };

    const citation = formatGuidelinesCitation(metadata, 1);

    expect(citation.shortCitation).toContain("European Society of Cardiology");
  });
});

describe("Citation Parsing", () => {
  test("parseCitations with inline citations", () => {
    const answer =
      "Metformin je lek prvni volby [1]. Kontraindikovany pri eGFR <30 [2].";
    const retrievedDocs = [
      {
        page_content: "SUKL doc",
        metadata: {
          source: "sukl",
          source_type: "drug_search",
          registration_number: "0012345",
        },
      },
      {
        page_content: "PubMed doc",
        metadata: {
          source: "PubMed",
          pmid: "12345678",
          url: "https://pubmed.ncbi.nlm.nih.gov/12345678",
          title: "Test",
          authors: "Smith, J",
          journal: "NEJM",
          publication_date: "2024-01-01",
        },
      },
    ];

    const result = parseCitations(answer, retrievedDocs);

    expect(result.citations).toHaveLength(2);
    expect(result.segments).toHaveLength(5); // text, [1], text, [2], text
    expect(result.segments[1].type).toBe("citation");
    expect(result.segments[1].citationNumber).toBe(1);
    expect(result.segments[3].type).toBe("citation");
    expect(result.segments[3].citationNumber).toBe(2);
  });

  test("parseCitations without citations in text", () => {
    const answer = "Plain text without citations.";
    const retrievedDocs: never[] = [];

    const result = parseCitations(answer, retrievedDocs);

    expect(result.citations).toHaveLength(0);
    expect(result.segments).toHaveLength(1);
    expect(result.segments[0].type).toBe("text");
    expect(result.segments[0].content).toBe("Plain text without citations.");
  });

  test("parseCitations with consecutive citations", () => {
    const answer = "Viz studie [1][2][3].";
    const retrievedDocs = [
      {
        page_content: "Doc 1",
        metadata: {
          source: "sukl",
          source_type: "drug_search",
          registration_number: "001",
        },
      },
      {
        page_content: "Doc 2",
        metadata: {
          source: "sukl",
          source_type: "drug_details",
          registration_number: "002",
        },
      },
      {
        page_content: "Doc 3",
        metadata: {
          source: "sukl",
          source_type: "reimbursement",
          registration_number: "003",
        },
      },
    ];

    const result = parseCitations(answer, retrievedDocs);

    expect(result.citations).toHaveLength(3);
    const citationSegments = result.segments.filter(
      (s) => s.type === "citation"
    );
    expect(citationSegments).toHaveLength(3);
    expect(citationSegments[0].citationNumber).toBe(1);
    expect(citationSegments[1].citationNumber).toBe(2);
    expect(citationSegments[2].citationNumber).toBe(3);
  });

  test("parseCitations preserves page_content", () => {
    const answer = "Test [1].";
    const retrievedDocs = [
      {
        page_content: "This is the actual document content",
        metadata: {
          source: "PubMed",
          pmid: "11111111",
          url: "https://pubmed.ncbi.nlm.nih.gov/11111111",
          title: "Test",
          authors: "Author, A",
          journal: "Journal",
          publication_date: "2024-01-01",
        },
      },
    ];

    const result = parseCitations(answer, retrievedDocs);

    expect(result.citations[0].page_content).toBe(
      "This is the actual document content"
    );
  });

  test("parseCitations with only text at beginning", () => {
    const answer = "[1] is the first citation.";
    const retrievedDocs = [
      {
        page_content: "Doc",
        metadata: {
          source: "sukl",
          source_type: "drug_search",
          registration_number: "001",
        },
      },
    ];

    const result = parseCitations(answer, retrievedDocs);

    expect(result.segments[0].type).toBe("citation");
    expect(result.segments[0].citationNumber).toBe(1);
    expect(result.segments[1].type).toBe("text");
  });
});
