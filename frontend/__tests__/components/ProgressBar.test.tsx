import { render, screen, waitFor } from "@testing-library/react";
import { ProgressBar } from "@/components/ProgressBar";

describe("ProgressBar", () => {
  test("renders when isLoading is true", async () => {
    render(<ProgressBar isLoading={true} />);
    await waitFor(() => {
      expect(screen.getByRole("progressbar")).toBeInTheDocument();
    });
  });

  test("does not render when isLoading is false", () => {
    render(<ProgressBar isLoading={false} />);
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });

  test("renders with correct variant", async () => {
    const { container } = render(<ProgressBar isLoading={true} variant="secondary" />);
    await waitFor(() => {
      const progressBar = container.querySelector('[data-slot="progress-bar"]');
      expect(progressBar).toHaveAttribute("data-variant", "secondary");
    });
  });

  test("renders at bottom position", async () => {
    const { container } = render(<ProgressBar isLoading={true} position="bottom" />);
    await waitFor(() => {
      const progressBar = container.querySelector('[data-slot="progress-bar"]');
      expect(progressBar).toHaveAttribute("data-position", "bottom");
    });
  });

  test("has correct accessibility attributes", async () => {
    render(<ProgressBar isLoading={true} />);
    await waitFor(() => {
      const progressBar = screen.getByRole("progressbar");
      expect(progressBar).toHaveAttribute("aria-label", "Průběh načítání");
      expect(progressBar).toHaveAttribute("aria-valuemin", "0");
      expect(progressBar).toHaveAttribute("aria-valuemax", "100");
    });
  });
});
