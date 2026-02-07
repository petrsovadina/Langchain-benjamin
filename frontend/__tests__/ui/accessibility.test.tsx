import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe, toHaveNoViolations } from "jest-axe";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

expect.extend(toHaveNoViolations);

const BUTTON_VARIANTS = [
  "default",
  "destructive",
  "outline",
  "secondary",
  "ghost",
  "link",
] as const;

const BADGE_VARIANTS = [
  "default",
  "secondary",
  "destructive",
  "outline",
  "ghost",
  "link",
] as const;

describe("Button Accessibility (axe-core)", () => {
  BUTTON_VARIANTS.forEach((variant) => {
    test(`${variant} variant passes axe`, async () => {
      const { container } = render(
        <Button variant={variant}>Test Button</Button>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  test("disabled button passes axe", async () => {
    const { container } = render(<Button disabled>Disabled</Button>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  test("button with aria-label passes axe", async () => {
    const { container } = render(
      <Button size="icon" aria-label="Hledat">
        X
      </Button>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  test("asChild anchor button passes axe", async () => {
    const { container } = render(
      <main>
        <Button asChild>
          <a href="/test">Link Button</a>
        </Button>
      </main>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});

describe("Badge Accessibility (axe-core)", () => {
  BADGE_VARIANTS.forEach((variant) => {
    test(`${variant} variant passes axe`, async () => {
      const { container } = render(
        <Badge variant={variant}>Test Badge</Badge>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  test("badge with link passes axe", async () => {
    const { container } = render(
      <main>
        <Badge asChild>
          <a href="/test">Link Badge</a>
        </Badge>
      </main>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});

describe("Button Keyboard Navigation", () => {
  test("button is focusable via Tab", async () => {
    const user = userEvent.setup();
    render(<Button>Focus Me</Button>);

    await user.tab();
    expect(screen.getByRole("button")).toHaveFocus();
  });

  test("button activates on Enter", async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click Me</Button>);

    await user.tab();
    await user.keyboard("{Enter}");
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test("button activates on Space", async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click Me</Button>);

    await user.tab();
    await user.keyboard(" ");
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test("disabled button is not focusable via Tab", async () => {
    const user = userEvent.setup();
    render(
      <div>
        <Button>First</Button>
        <Button disabled>Disabled</Button>
        <Button>Third</Button>
      </div>
    );

    await user.tab();
    expect(screen.getByText("First")).toHaveFocus();
    await user.tab();
    // Disabled button is skipped, focus moves to Third
    expect(screen.getByText("Third")).toHaveFocus();
  });

  test("multiple buttons can be tab-navigated in order", async () => {
    const user = userEvent.setup();
    render(
      <div>
        <Button>First</Button>
        <Button>Second</Button>
        <Button>Third</Button>
      </div>
    );

    await user.tab();
    expect(screen.getByText("First")).toHaveFocus();
    await user.tab();
    expect(screen.getByText("Second")).toHaveFocus();
    await user.tab();
    expect(screen.getByText("Third")).toHaveFocus();
  });
});

describe("Badge Keyboard Navigation", () => {
  test("badge link is focusable via Tab", async () => {
    const user = userEvent.setup();
    render(
      <Badge asChild>
        <a href="/test">Link Badge</a>
      </Badge>
    );

    await user.tab();
    expect(screen.getByRole("link")).toHaveFocus();
  });

  test("badge span is not focusable by default", async () => {
    const user = userEvent.setup();
    render(
      <div>
        <Button>Button</Button>
        <Badge>Not Focusable</Badge>
      </div>
    );

    await user.tab();
    expect(screen.getByRole("button")).toHaveFocus();
    await user.tab();
    // Badge span should not receive focus
    expect(screen.getByText("Not Focusable")).not.toHaveFocus();
  });
});

describe("Button Focus Visible Classes", () => {
  test("contains focus-visible ring classes", () => {
    render(<Button>Focus Ring</Button>);
    const button = screen.getByRole("button");
    expect(button.className).toContain("focus-visible:ring-ring/50");
    expect(button.className).toContain("focus-visible:ring-[3px]");
  });

  test("contains outline-none to prevent default outline", () => {
    render(<Button>No Outline</Button>);
    const button = screen.getByRole("button");
    expect(button.className).toContain("outline-none");
  });
});

describe("Button Disabled State Accessibility", () => {
  test("disabled button has disabled attribute", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole("button")).toHaveAttribute("disabled");
  });

  test("disabled button has pointer-events-none class", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole("button").className).toContain(
      "disabled:pointer-events-none"
    );
  });

  test("disabled button has reduced opacity class", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole("button").className).toContain(
      "disabled:opacity-50"
    );
  });
});

describe("ARIA Invalid State", () => {
  test("button with aria-invalid has destructive ring classes", () => {
    render(<Button aria-invalid="true">Invalid</Button>);
    const button = screen.getByRole("button");
    expect(button.className).toContain("aria-invalid:ring-destructive/20");
    expect(button.className).toContain("aria-invalid:border-destructive");
  });

  test("badge with aria-invalid has destructive ring classes", () => {
    render(<Badge aria-invalid="true">Invalid</Badge>);
    const badge = screen.getByText("Invalid");
    expect(badge.className).toContain("aria-invalid:ring-destructive/20");
    expect(badge.className).toContain("aria-invalid:border-destructive");
  });
});

describe("Touch Target Size (WCAG 2.1 AA)", () => {
  test("touch size button has min 44px height class", () => {
    render(<Button size="touch">Touch</Button>);
    const button = screen.getByRole("button");
    // h-11 = 2.75rem = 44px
    expect(button.className).toContain("h-11");
  });

  test("icon-touch button has min 44px size class", () => {
    render(
      <Button size="icon-touch" aria-label="Touch Icon">
        X
      </Button>
    );
    const button = screen.getByRole("button");
    // size-11 = 2.75rem = 44px
    expect(button.className).toContain("size-11");
  });
});
