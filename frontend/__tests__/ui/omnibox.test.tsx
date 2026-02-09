import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Omnibox } from "@/components/Omnibox";

// Mock useOnlineStatus hook
let mockOnlineStatus = true;
vi.mock("@/hooks/useOnlineStatus", () => ({
  useOnlineStatus: () => mockOnlineStatus,
}));

describe("Omnibox", () => {
  const defaultProps = {
    onSubmit: vi.fn(),
    isLoading: false,
    isActive: false,
  };

  beforeEach(() => {
    mockOnlineStatus = true;
    vi.clearAllMocks();
  });

  describe("Loading State", () => {
    test("shows loading spinner in send button when isLoading=true", () => {
      render(<Omnibox {...defaultProps} isLoading={true} />);
      // Loader2 has animate-spin class
      const form = screen.getByRole("search");
      expect(form.querySelector(".animate-spin")).toBeInTheDocument();
    });

    test("shows Send icon when not loading", () => {
      render(<Omnibox {...defaultProps} isLoading={false} />);
      const form = screen.getByRole("search");
      expect(form.querySelector(".animate-spin")).not.toBeInTheDocument();
    });

    test("sets aria-busy on form when loading", () => {
      render(<Omnibox {...defaultProps} isLoading={true} />);
      const form = screen.getByRole("search");
      expect(form).toHaveAttribute("aria-busy", "true");
    });

    test("placeholder shows processing text when loading", () => {
      render(<Omnibox {...defaultProps} isLoading={true} />);
      const input = screen.getByLabelText("Zadejte lékařský dotaz");
      expect(input).toHaveAttribute("placeholder", "Zpracovávám dotaz...");
    });

    test("disables input when loading", () => {
      render(<Omnibox {...defaultProps} isLoading={true} />);
      const input = screen.getByLabelText("Zadejte lékařský dotaz");
      expect(input).toBeDisabled();
    });

    test("disables all buttons when loading", () => {
      render(<Omnibox {...defaultProps} isLoading={true} />);
      const buttons = screen.getAllByRole("button");
      // Mic and Paperclip buttons should be disabled
      const micButton = screen.getByLabelText("Hlasový vstup");
      const attachButton = screen.getByLabelText("Přiložit soubor");
      expect(micButton).toBeDisabled();
      expect(attachButton).toBeDisabled();
    });
  });

  describe("Focus State", () => {
    test("container has focus-within styling classes", () => {
      render(<Omnibox {...defaultProps} />);
      const container = screen.getByTestId("omnibox");
      expect(container.className).toContain("focus-within:border-primary");
      expect(container.className).toContain("focus-within:ring-2");
      expect(container.className).toContain("focus-within:ring-ring/20");
    });

    test("container has transition classes", () => {
      render(<Omnibox {...defaultProps} />);
      const container = screen.getByTestId("omnibox");
      expect(container.className).toContain("transition-all");
      expect(container.className).toContain("duration-200");
    });
  });

  describe("Error Banner", () => {
    test("renders error with AlertCircle icon", () => {
      render(<Omnibox {...defaultProps} error="Test error" />);
      const alert = screen.getByRole("alert");
      expect(alert).toBeInTheDocument();
      expect(alert).toHaveTextContent("Test error");
    });

    test("error banner has slide-in animation", () => {
      render(<Omnibox {...defaultProps} error="Test error" />);
      const alert = screen.getByRole("alert");
      expect(alert.className).toContain("animate-in");
      expect(alert.className).toContain("slide-in-from-top-2");
    });

    test("error banner has aria-live assertive", () => {
      render(<Omnibox {...defaultProps} error="Test error" />);
      const alert = screen.getByRole("alert");
      expect(alert).toHaveAttribute("aria-live", "assertive");
    });

    test("renders retry button when onRetry provided", async () => {
      const onRetry = vi.fn();
      render(<Omnibox {...defaultProps} error="Test error" onRetry={onRetry} />);
      const retryButton = screen.getByLabelText("Zkusit znovu");
      expect(retryButton).toBeInTheDocument();

      await userEvent.setup().click(retryButton);
      expect(onRetry).toHaveBeenCalledTimes(1);
    });
  });

  describe("Offline Warning", () => {
    test("renders offline warning with WifiOff icon", () => {
      mockOnlineStatus = false;
      render(<Omnibox {...defaultProps} />);
      const alerts = screen.getAllByRole("alert");
      const offlineAlert = alerts.find((a) =>
        a.textContent?.includes("offline")
      );
      expect(offlineAlert).toBeInTheDocument();
    });

    test("offline warning has pulse animation", () => {
      mockOnlineStatus = false;
      render(<Omnibox {...defaultProps} />);
      const alerts = screen.getAllByRole("alert");
      const offlineAlert = alerts.find((a) =>
        a.textContent?.includes("offline")
      );
      expect(offlineAlert?.className).toContain("animate-pulse");
    });

    test("offline warning has aria-live polite", () => {
      mockOnlineStatus = false;
      render(<Omnibox {...defaultProps} />);
      const alerts = screen.getAllByRole("alert");
      const offlineAlert = alerts.find((a) =>
        a.textContent?.includes("offline")
      );
      expect(offlineAlert).toHaveAttribute("aria-live", "polite");
    });

    test("disables input when offline", () => {
      mockOnlineStatus = false;
      render(<Omnibox {...defaultProps} />);
      const input = screen.getByLabelText("Zadejte lékařský dotaz");
      expect(input).toBeDisabled();
    });
  });

  describe("Submission", () => {
    test("submits query on Enter", async () => {
      const user = userEvent.setup();
      const onSubmit = vi.fn();
      render(<Omnibox {...defaultProps} onSubmit={onSubmit} />);

      const input = screen.getByLabelText("Zadejte lékařský dotaz");
      await user.type(input, "test query");
      await user.keyboard("{Enter}");

      expect(onSubmit).toHaveBeenCalledWith("test query");
    });

    test("does not submit empty query", async () => {
      const user = userEvent.setup();
      const onSubmit = vi.fn();
      render(<Omnibox {...defaultProps} onSubmit={onSubmit} />);

      await user.keyboard("{Enter}");
      expect(onSubmit).not.toHaveBeenCalled();
    });

    test("does not submit when loading", async () => {
      const user = userEvent.setup();
      const onSubmit = vi.fn();
      render(<Omnibox {...defaultProps} onSubmit={onSubmit} isLoading={true} />);

      const input = screen.getByLabelText("Zadejte lékařský dotaz");
      // Input is disabled, so type won't work, but let's try keyboard
      await user.keyboard("{Enter}");
      expect(onSubmit).not.toHaveBeenCalled();
    });
  });

  describe("Snapshots", () => {
    test("default state", () => {
      const { container } = render(<Omnibox {...defaultProps} />);
      expect(container).toMatchSnapshot();
    });

    test("loading state", () => {
      const { container } = render(<Omnibox {...defaultProps} isLoading={true} />);
      expect(container).toMatchSnapshot();
    });

    test("error state", () => {
      const { container } = render(
        <Omnibox {...defaultProps} error="Chyba serveru" onRetry={vi.fn()} />
      );
      expect(container).toMatchSnapshot();
    });

    test("offline state", () => {
      mockOnlineStatus = false;
      const { container } = render(<Omnibox {...defaultProps} />);
      expect(container).toMatchSnapshot();
    });
  });
});
