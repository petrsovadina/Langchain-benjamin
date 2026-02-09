import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ErrorBoundary } from "@/components/ErrorBoundary";

const ThrowError = () => {
  throw new Error("Test error");
};

describe("ErrorBoundary", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  test("renders children when no error", () => {
    render(
      <ErrorBoundary>
        <div>Test content</div>
      </ErrorBoundary>
    );
    expect(screen.getByText("Test content")).toBeInTheDocument();
  });

  test("renders default error UI when error occurs", () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("Něco se pokazilo")).toBeInTheDocument();
  });

  test("renders minimal variant", () => {
    const { container } = render(
      <ErrorBoundary variant="minimal">
        <ThrowError />
      </ErrorBoundary>
    );
    const errorBoundary = container.querySelector('[data-slot="error-boundary"]');
    expect(errorBoundary).toHaveAttribute("data-variant", "minimal");
  });

  test("renders custom fallback", () => {
    render(
      <ErrorBoundary fallback={<div>Custom error</div>}>
        <ThrowError />
      </ErrorBoundary>
    );
    expect(screen.getByText("Custom error")).toBeInTheDocument();
  });

  test("calls onReset when reset button clicked", async () => {
    const user = userEvent.setup();
    const onReset = vi.fn();
    render(
      <ErrorBoundary onReset={onReset}>
        <ThrowError />
      </ErrorBoundary>
    );
    await user.click(screen.getByText("Zkusit znovu"));
    expect(onReset).toHaveBeenCalledTimes(1);
  });
});
