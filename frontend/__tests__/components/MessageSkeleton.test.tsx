import { render, screen } from "@testing-library/react";
import { MessageSkeleton } from "@/components/MessageSkeleton";

describe("MessageSkeleton", () => {
  test("renders with default props", () => {
    const { container } = render(<MessageSkeleton />);
    expect(container.firstChild).toHaveAttribute("data-slot", "message-skeleton");
    expect(container.firstChild).toHaveAttribute("data-variant", "assistant");
  });

  test("renders user variant", () => {
    const { container } = render(<MessageSkeleton variant="user" />);
    expect(container.firstChild).toHaveAttribute("data-variant", "user");
  });

  test("renders correct number of lines", () => {
    const { container } = render(<MessageSkeleton lines={5} />);
    const lines = container.querySelectorAll(".h-4");
    expect(lines).toHaveLength(5);
  });

  test("hides avatar when showAvatar is false", () => {
    const { container } = render(<MessageSkeleton showAvatar={false} />);
    const avatar = container.querySelector(".rounded-full");
    expect(avatar).not.toBeInTheDocument();
  });

  test("has correct accessibility attributes", () => {
    render(<MessageSkeleton />);
    expect(screen.getByRole("status")).toHaveAttribute("aria-label", "Načítání zprávy");
  });

  test("snapshot test", () => {
    const { container } = render(<MessageSkeleton variant="assistant" lines={3} />);
    expect(container.firstChild).toMatchSnapshot();
  });
});
