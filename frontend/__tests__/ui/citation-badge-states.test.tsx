import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CitationBadge } from "@/components/CitationBadge";
import type { Citation } from "@/lib/types/citations";

const testCitation: Citation = {
  number: 1,
  metadata: {
    source: "PubMed",
    pmid: "12345678",
    url: "https://pubmed.ncbi.nlm.nih.gov/12345678",
    title: "Efficacy of Metformin",
    authors: "Smith, John",
    journal: "NEJM",
    publication_date: "2024-06-15",
  },
  page_content: "Test content",
  shortCitation: "Smith et al. (2024)",
  fullCitation: "[1] Smith, John. Efficacy of Metformin. NEJM. 2024.",
};

describe("CitationBadge States", () => {
  describe("Hover State", () => {
    test("has hover:bg-citation-badge-hover class", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge.className).toContain("hover:bg-citation-badge-hover");
    });

    test("has hover:border-citation-badge-text class", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge.className).toContain("hover:border-citation-badge-text");
    });

    test("has hover:scale-105 class", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge.className).toContain("hover:scale-105");
    });
  });

  describe("Active State", () => {
    test("has active:bg-citation-badge-active class", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge.className).toContain("active:bg-citation-badge-active");
    });

    test("has active:scale-95 class", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge.className).toContain("active:scale-95");
    });
  });

  describe("Focus State", () => {
    test("has focus-visible:ring-2 class", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge.className).toContain("focus-visible:ring-2");
    });

    test("has focus-visible:ring-ring/50 class", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge.className).toContain("focus-visible:ring-ring/50");
    });

    test("has focus-visible:border-citation-badge-text class", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge.className).toContain("focus-visible:border-citation-badge-text");
    });
  });

  describe("HoverCard Open State", () => {
    test("has data-[state=open]:bg-citation-badge-active class", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge.className).toContain("data-[state=open]:bg-citation-badge-active");
    });

    test("has data-[state=open]:ring-2 class", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge.className).toContain("data-[state=open]:ring-2");
    });

    test("has data-[state=open]:ring-citation-badge-text class", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge.className).toContain("data-[state=open]:ring-citation-badge-text");
    });
  });

  describe("Transitions", () => {
    test("has transition-all class", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge.className).toContain("transition-all");
    });

    test("has duration-200 class", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge.className).toContain("duration-200");
    });
  });

  describe("Design Tokens", () => {
    test("uses citation-badge-text color", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge.className).toContain("text-citation-badge-text");
    });

    test("uses citation-badge-text/30 border", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge.className).toContain("border-citation-badge-text/30");
    });
  });

  describe("Accessibility", () => {
    test("has role=button", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge).toHaveAttribute("role", "button");
    });

    test("has tabIndex=0", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge).toHaveAttribute("tabindex", "0");
    });

    test("has aria-label with citation info", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge).toHaveAttribute("aria-label", "Citace 1: Smith et al. (2024)");
    });

    test("has aria-haspopup=dialog", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge).toHaveAttribute("aria-haspopup", "dialog");
    });

    test("responds to Enter key", async () => {
      const user = userEvent.setup();
      const onClick = vi.fn();
      render(<CitationBadge citation={testCitation} onClick={onClick} />);

      const badge = screen.getByTestId("citation-badge");
      badge.focus();
      await user.keyboard("{Enter}");

      expect(onClick).toHaveBeenCalledTimes(1);
    });

    test("responds to Space key", async () => {
      const user = userEvent.setup();
      const onClick = vi.fn();
      render(<CitationBadge citation={testCitation} onClick={onClick} />);

      const badge = screen.getByTestId("citation-badge");
      badge.focus();
      await user.keyboard(" ");

      expect(onClick).toHaveBeenCalledTimes(1);
    });

    test("touch target is at least 44x44px", () => {
      render(<CitationBadge citation={testCitation} />);
      const badge = screen.getByTestId("citation-badge");
      expect(badge.className).toContain("min-h-[44px]");
      expect(badge.className).toContain("min-w-[44px]");
    });
  });

  describe("Snapshots", () => {
    test("default state", () => {
      const { container } = render(
        <CitationBadge citation={testCitation} onClick={vi.fn()} />
      );
      expect(container).toMatchSnapshot();
    });
  });
});
