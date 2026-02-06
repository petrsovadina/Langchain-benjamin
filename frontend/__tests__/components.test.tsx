import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CitationBadge } from "@/components/CitationBadge";
import { CitationPopup } from "@/components/CitationPopup";
import { ReferencesSection } from "@/components/ReferencesSection";
import type { Citation } from "@/lib/types/citations";

const suklCitation: Citation = {
  number: 1,
  metadata: {
    source: "sukl",
    source_type: "drug_search",
    registration_number: "0012345",
    atc_code: "M01AE01",
  },
  page_content: "SUKL document content",
  shortCitation: "SUKL Reg. 0012345",
  fullCitation:
    "[1] SUKL - drug_search. Registracni cislo: 0012345. https://www.sukl.cz/modules/medication/detail.php?code=0012345",
};

const pubmedCitation: Citation = {
  number: 2,
  metadata: {
    source: "PubMed",
    pmid: "12345678",
    url: "https://pubmed.ncbi.nlm.nih.gov/12345678",
    title: "Efficacy of Metformin",
    authors: "Smith, John; Doe, Jane",
    journal: "NEJM",
    publication_date: "2024-06-15",
    doi: "10.1056/NEJMoa2401234",
  },
  page_content: "PubMed abstract content",
  shortCitation: "Smith et al. (2024)",
  fullCitation:
    "[2] Smith, John; Doe, Jane. Efficacy of Metformin. NEJM. 2024. PMID: 12345678. https://pubmed.ncbi.nlm.nih.gov/12345678",
};

const guidelinesCitation: Citation = {
  number: 3,
  metadata: {
    source: "cls_jep",
    source_type: "clinical_guidelines",
    guideline_id: "CLS-JEP-2024-001",
    url: "https://www.cls.cz/guidelines/001",
    publication_date: "2024-01-15",
  },
  page_content: "Guidelines content",
  shortCitation: "CLS JEP CLS-JEP-2024-001",
  fullCitation:
    "[3] CLS JEP. CLS-JEP-2024-001. 2024. https://www.cls.cz/guidelines/001",
};

describe("CitationBadge", () => {
  test("renders citation number", () => {
    render(<CitationBadge citation={suklCitation} />);
    expect(screen.getByTestId("citation-badge")).toHaveTextContent("[1]");
  });

  test("renders with correct data-testid", () => {
    render(<CitationBadge citation={pubmedCitation} />);
    expect(screen.getByTestId("citation-badge")).toBeInTheDocument();
    expect(screen.getByTestId("citation-badge")).toHaveTextContent("[2]");
  });

  test("calls onClick when badge is clicked", async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();

    render(<CitationBadge citation={suklCitation} onClick={handleClick} />);
    await user.click(screen.getByTestId("citation-badge"));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test("does not crash without onClick", async () => {
    const user = userEvent.setup();

    render(<CitationBadge citation={suklCitation} />);
    await user.click(screen.getByTestId("citation-badge"));

    expect(screen.getByTestId("citation-badge")).toBeInTheDocument();
  });
});

describe("CitationPopup", () => {
  test("renders nothing when citation is null", () => {
    const { container } = render(
      <CitationPopup citation={null} open={false} onClose={() => {}} />
    );
    expect(container.innerHTML).toBe("");
  });

  test("renders citation title when open", () => {
    render(
      <CitationPopup citation={suklCitation} open={true} onClose={() => {}} />
    );
    expect(screen.getByText("Citace [1]")).toBeInTheDocument();
  });

  test("renders short and full citation text", () => {
    render(
      <CitationPopup
        citation={pubmedCitation}
        open={true}
        onClose={() => {}}
      />
    );
    expect(screen.getByText("Kratka citace")).toBeInTheDocument();
    expect(screen.getByText("Smith et al. (2024)")).toBeInTheDocument();
    expect(screen.getByText("Uplna citace")).toBeInTheDocument();
  });

  test("renders SUKL source details", () => {
    render(
      <CitationPopup citation={suklCitation} open={true} onClose={() => {}} />
    );
    expect(screen.getByText("SUKL Detaily")).toBeInTheDocument();
    expect(screen.getByText("0012345")).toBeInTheDocument();
    expect(screen.getByText("M01AE01")).toBeInTheDocument();
  });

  test("renders PubMed source details", () => {
    render(
      <CitationPopup
        citation={pubmedCitation}
        open={true}
        onClose={() => {}}
      />
    );
    expect(screen.getByText("PubMed Detaily")).toBeInTheDocument();
    expect(screen.getByText("12345678")).toBeInTheDocument();
    expect(screen.getByText("NEJM")).toBeInTheDocument();
    expect(screen.getByText("Smith, John; Doe, Jane")).toBeInTheDocument();
    expect(screen.getByText("2024-06-15")).toBeInTheDocument();
    expect(screen.getByText("10.1056/NEJMoa2401234")).toBeInTheDocument();
  });

  test("renders Guidelines source details", () => {
    render(
      <CitationPopup
        citation={guidelinesCitation}
        open={true}
        onClose={() => {}}
      />
    );
    expect(screen.getByText("Guidelines Detaily")).toBeInTheDocument();
    expect(screen.getByText("CLS-JEP-2024-001")).toBeInTheDocument();
    expect(screen.getByText("CLS_JEP")).toBeInTheDocument();
  });

  test("renders external link for PubMed citation", () => {
    render(
      <CitationPopup
        citation={pubmedCitation}
        open={true}
        onClose={() => {}}
      />
    );
    const link = screen.getByText("Otevrit zdroj");
    expect(link).toHaveAttribute(
      "href",
      "https://pubmed.ncbi.nlm.nih.gov/12345678"
    );
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  test("calls onClose when dialog is closed", async () => {
    const user = userEvent.setup();
    const handleClose = vi.fn();

    render(
      <CitationPopup
        citation={suklCitation}
        open={true}
        onClose={handleClose}
      />
    );

    // Press Escape to close dialog
    await user.keyboard("{Escape}");
    expect(handleClose).toHaveBeenCalled();
  });
});

describe("ReferencesSection", () => {
  test("renders nothing when citations array is empty", () => {
    const { container } = render(<ReferencesSection citations={[]} />);
    expect(container.innerHTML).toBe("");
  });

  test("renders heading", () => {
    render(<ReferencesSection citations={[suklCitation]} />);
    expect(screen.getByText("Reference")).toBeInTheDocument();
  });

  test("renders citation numbers", () => {
    render(
      <ReferencesSection
        citations={[suklCitation, pubmedCitation, guidelinesCitation]}
      />
    );
    expect(screen.getByText("[1]")).toBeInTheDocument();
    expect(screen.getByText("[2]")).toBeInTheDocument();
    expect(screen.getByText("[3]")).toBeInTheDocument();
  });

  test("renders full citation text for each citation", () => {
    render(
      <ReferencesSection citations={[suklCitation, pubmedCitation]} />
    );
    expect(
      screen.getByText(suklCitation.fullCitation)
    ).toBeInTheDocument();
    expect(
      screen.getByText(pubmedCitation.fullCitation)
    ).toBeInTheDocument();
  });

  test("renders external link for citations with URL", () => {
    render(<ReferencesSection citations={[pubmedCitation]} />);
    const links = screen.getAllByText("Otevrit zdroj");
    expect(links[0]).toHaveAttribute(
      "href",
      "https://pubmed.ncbi.nlm.nih.gov/12345678"
    );
    expect(links[0]).toHaveAttribute("target", "_blank");
  });

  test("renders external link for guidelines citation", () => {
    render(<ReferencesSection citations={[guidelinesCitation]} />);
    const link = screen.getByText("Otevrit zdroj");
    expect(link).toHaveAttribute(
      "href",
      "https://www.cls.cz/guidelines/001"
    );
  });
});
