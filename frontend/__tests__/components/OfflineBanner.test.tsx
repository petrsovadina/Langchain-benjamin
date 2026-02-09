import { render, screen } from "@testing-library/react";
import { OfflineBanner } from "@/components/OfflineBanner";

describe("OfflineBanner", () => {
  test("renders with default message", () => {
    render(<OfflineBanner />);
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Jste offline. Připojte se k internetu pro odeslání dotazu."
    );
  });

  test("renders with custom message", () => {
    render(<OfflineBanner message="Custom offline message" />);
    expect(screen.getByText("Custom offline message")).toBeInTheDocument();
  });

  test("has correct accessibility attributes", () => {
    render(<OfflineBanner />);
    const banner = screen.getByRole("alert");
    expect(banner).toHaveAttribute("aria-live", "polite");
    expect(banner).toHaveAttribute("data-slot", "offline-banner");
  });

  test("snapshot test", () => {
    const { container } = render(<OfflineBanner />);
    expect(container.firstChild).toMatchSnapshot();
  });
});
