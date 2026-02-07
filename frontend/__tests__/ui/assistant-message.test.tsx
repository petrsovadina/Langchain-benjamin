import { render, screen } from "@testing-library/react";
import { AssistantMessage } from "@/components/AssistantMessage";

// Mock CitedResponse component
vi.mock("@/components/CitedResponse", () => ({
  CitedResponse: ({ answer }: { answer: string }) => (
    <div data-testid="cited-response">{answer}</div>
  ),
}));

// Mock ReactMarkdown
vi.mock("react-markdown", () => ({
  default: ({ children }: { children: string }) => (
    <div data-testid="markdown">{children}</div>
  ),
}));

// Mock remark-gfm
vi.mock("remark-gfm", () => ({
  default: () => {},
}));

const defaultProps = {
  content: "Test response content",
  timestamp: new Date("2026-01-01T12:00:00"),
};

describe("AssistantMessage", () => {
  describe("Loading State", () => {
    test("renders MessageSkeleton when loading with no content", () => {
      const { container } = render(
        <AssistantMessage {...defaultProps} content="" isLoading={true} />
      );
      expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
    });

    test("renders processing text when loading with content", () => {
      render(
        <AssistantMessage {...defaultProps} content="partial" isLoading={true} />
      );
      expect(screen.getByText("Zpracovávám dotaz...")).toBeInTheDocument();
    });
  });

  describe("Streaming State", () => {
    test("shows typing indicator when streaming", () => {
      render(
        <AssistantMessage {...defaultProps} isStreaming={true} />
      );
      expect(screen.getByTestId("streaming-indicator")).toBeInTheDocument();
      expect(screen.getByText("Píšu odpověď...")).toBeInTheDocument();
    });

    test("streaming indicator has bouncing dots", () => {
      render(
        <AssistantMessage {...defaultProps} isStreaming={true} />
      );
      const indicator = screen.getByTestId("streaming-indicator");
      const dots = indicator.querySelectorAll(".animate-bounce");
      expect(dots).toHaveLength(3);
    });

    test("Bot icon pulses when streaming", () => {
      render(
        <AssistantMessage {...defaultProps} isStreaming={true} />
      );
      const message = screen.getByTestId("assistant-message");
      const botIcon = message.querySelector(".animate-pulse");
      expect(botIcon).toBeInTheDocument();
    });

    test("sets aria-busy when streaming", () => {
      render(
        <AssistantMessage {...defaultProps} isStreaming={true} />
      );
      const message = screen.getByTestId("assistant-message");
      expect(message).toHaveAttribute("aria-busy", "true");
    });

    test("sets aria-live polite when streaming", () => {
      render(
        <AssistantMessage {...defaultProps} isStreaming={true} />
      );
      const message = screen.getByTestId("assistant-message");
      expect(message).toHaveAttribute("aria-live", "polite");
    });

    test("has sr-only text for screen readers when streaming", () => {
      render(
        <AssistantMessage {...defaultProps} isStreaming={true} />
      );
      expect(screen.getByText("Asistent píše odpověď")).toBeInTheDocument();
    });
  });

  describe("No-Citations State", () => {
    test("renders plain markdown when no citations", () => {
      render(
        <AssistantMessage {...defaultProps} retrieved_docs={[]} />
      );
      expect(screen.getByTestId("markdown")).toBeInTheDocument();
      expect(screen.queryByTestId("cited-response")).not.toBeInTheDocument();
    });

    test("has slate border-left accent when no citations", () => {
      render(
        <AssistantMessage {...defaultProps} retrieved_docs={[]} />
      );
      const message = screen.getByTestId("assistant-message");
      const card = message.querySelector("[class*='border-l-slate']");
      expect(card).toBeInTheDocument();
    });
  });

  describe("With-Citations State", () => {
    const docsWithCitations = [
      {
        page_content: "Test content",
        metadata: { source: "PubMed", pmid: "123" },
      },
    ];

    test("renders CitedResponse when citations present", () => {
      render(
        <AssistantMessage
          {...defaultProps}
          retrieved_docs={docsWithCitations}
        />
      );
      expect(screen.getByTestId("cited-response")).toBeInTheDocument();
      expect(screen.queryByTestId("markdown")).not.toBeInTheDocument();
    });

    test("has citation-badge-text border-left when citations present", () => {
      render(
        <AssistantMessage
          {...defaultProps}
          retrieved_docs={docsWithCitations}
        />
      );
      const message = screen.getByTestId("assistant-message");
      const card = message.querySelector("[class*='border-l-citation-badge-text']");
      expect(card).toBeInTheDocument();
    });
  });

  describe("Metadata Display", () => {
    test("renders timestamp", () => {
      render(<AssistantMessage {...defaultProps} />);
      // Czech locale time format
      expect(screen.getByText(/12:00/)).toBeInTheDocument();
    });

    test("renders latency when provided", () => {
      render(
        <AssistantMessage {...defaultProps} latency_ms={2500} />
      );
      expect(screen.getByText(/2\.5s/)).toBeInTheDocument();
    });
  });

  describe("Snapshots", () => {
    test("default state", () => {
      const { container } = render(<AssistantMessage {...defaultProps} />);
      expect(container).toMatchSnapshot();
    });

    test("streaming state", () => {
      const { container } = render(
        <AssistantMessage {...defaultProps} isStreaming={true} />
      );
      expect(container).toMatchSnapshot();
    });

    test("loading state", () => {
      const { container } = render(
        <AssistantMessage {...defaultProps} content="" isLoading={true} />
      );
      expect(container).toMatchSnapshot();
    });

    test("with citations", () => {
      const { container } = render(
        <AssistantMessage
          {...defaultProps}
          retrieved_docs={[
            {
              page_content: "Test",
              metadata: { source: "PubMed", pmid: "123" },
            },
          ]}
        />
      );
      expect(container).toMatchSnapshot();
    });
  });
});
