import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Badge } from "@/components/ui/badge";

const VARIANTS = [
  "default",
  "secondary",
  "destructive",
  "outline",
  "ghost",
  "link",
] as const;

describe("Badge Variants", () => {
  VARIANTS.forEach((variant) => {
    test(`renders ${variant} variant correctly`, () => {
      render(<Badge variant={variant}>Test</Badge>);
      const badge = screen.getByText("Test");
      expect(badge).toHaveAttribute("data-variant", variant);
      expect(badge).toHaveAttribute("data-slot", "badge");
    });
  });

  test("defaults to 'default' variant when no variant specified", () => {
    render(<Badge>Default</Badge>);
    const badge = screen.getByText("Default");
    expect(badge).toHaveAttribute("data-variant", "default");
  });
});

describe("Badge States", () => {
  test("focus-visible ring classes are present", () => {
    render(<Badge>Focus Test</Badge>);
    const badge = screen.getByText("Focus Test");
    expect(badge.className).toContain("focus-visible:ring-ring/50");
    expect(badge.className).toContain("focus-visible:ring-[3px]");
    expect(badge.className).toContain("focus-visible:border-ring");
  });

  test("aria-invalid classes are present", () => {
    render(<Badge aria-invalid="true">Invalid</Badge>);
    const badge = screen.getByText("Invalid");
    expect(badge.className).toContain("aria-invalid:ring-destructive/20");
    expect(badge.className).toContain("aria-invalid:border-destructive");
  });
});

describe("Badge asChild", () => {
  test("renders as child element when asChild is true", () => {
    render(
      <Badge asChild>
        <a href="/test">Link Badge</a>
      </Badge>
    );
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/test");
    expect(link).toHaveAttribute("data-slot", "badge");
  });

  test("renders as span element when asChild is false", () => {
    render(<Badge>Span Badge</Badge>);
    const badge = screen.getByText("Span Badge");
    expect(badge.tagName).toBe("SPAN");
  });

  test("anchor badge is keyboard focusable", async () => {
    const user = userEvent.setup();
    render(
      <Badge asChild>
        <a href="/test">Link</a>
      </Badge>
    );

    await user.tab();
    expect(screen.getByRole("link")).toHaveFocus();
  });
});

describe("Badge Hover Classes (Anchor)", () => {
  VARIANTS.forEach((variant) => {
    test(`${variant} variant has appropriate hover class for anchors`, () => {
      render(
        <Badge variant={variant} asChild>
          <a href="#">Hover Test</a>
        </Badge>
      );
      const link = screen.getByRole("link");
      // All variants except ghost and link should have [a&]:hover classes
      // ghost and link have their own hover patterns
      if (variant === "default") {
        expect(link.className).toContain("[a&]:hover:bg-primary/90");
      } else if (variant === "secondary") {
        expect(link.className).toContain("[a&]:hover:bg-secondary/90");
      } else if (variant === "destructive") {
        expect(link.className).toContain("[a&]:hover:bg-destructive/90");
      } else if (variant === "outline") {
        expect(link.className).toContain("[a&]:hover:bg-accent");
      } else if (variant === "ghost") {
        expect(link.className).toContain("[a&]:hover:bg-accent");
      } else if (variant === "link") {
        expect(link.className).toContain("[a&]:hover:underline");
      }
    });
  });
});

describe("Badge Custom Props", () => {
  test("passes className to the element", () => {
    render(<Badge className="custom-class">Test</Badge>);
    expect(screen.getByText("Test").className).toContain("custom-class");
  });

  test("passes data attributes", () => {
    render(<Badge data-testid="my-badge">Test</Badge>);
    expect(screen.getByTestId("my-badge")).toBeInTheDocument();
  });
});

describe("Badge Visual Regression (Snapshots)", () => {
  VARIANTS.forEach((variant) => {
    test(`${variant} variant snapshot`, () => {
      const { container } = render(
        <Badge variant={variant}>Snapshot</Badge>
      );
      expect(container.firstChild).toMatchSnapshot();
    });
  });

  test("asChild anchor snapshot", () => {
    const { container } = render(
      <Badge asChild>
        <a href="#">Link Snapshot</a>
      </Badge>
    );
    expect(container.firstChild).toMatchSnapshot();
  });
});
