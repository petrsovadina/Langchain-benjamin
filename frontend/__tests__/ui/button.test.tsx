import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Button } from "@/components/ui/button";

const VARIANTS = [
  "default",
  "destructive",
  "outline",
  "secondary",
  "ghost",
  "link",
] as const;

const SIZES = [
  "default",
  "xs",
  "sm",
  "lg",
  "icon",
  "icon-xs",
  "icon-sm",
  "icon-lg",
  "touch",
  "icon-touch",
] as const;

describe("Button Variants", () => {
  VARIANTS.forEach((variant) => {
    test(`renders ${variant} variant correctly`, () => {
      render(<Button variant={variant}>Test</Button>);
      const button = screen.getByRole("button");
      expect(button).toHaveAttribute("data-variant", variant);
      expect(button).toHaveAttribute("data-slot", "button");
    });
  });

  test("defaults to 'default' variant when no variant specified", () => {
    render(<Button>Default</Button>);
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("data-variant", "default");
  });
});

describe("Button Sizes", () => {
  SIZES.forEach((size) => {
    test(`renders ${size} size correctly`, () => {
      render(
        <Button size={size}>{size === "icon" ? "X" : "Test"}</Button>
      );
      const button = screen.getByRole("button");
      expect(button).toHaveAttribute("data-size", size);
    });
  });

  test("defaults to 'default' size when no size specified", () => {
    render(<Button>Default</Button>);
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("data-size", "default");
  });
});

describe("Button Variant × Size Matrix", () => {
  VARIANTS.forEach((variant) => {
    SIZES.forEach((size) => {
      test(`renders ${variant}/${size} combination`, () => {
        const { container } = render(
          <Button variant={variant} size={size}>
            Test
          </Button>
        );
        const button = container.firstChild as HTMLElement;
        expect(button).toHaveAttribute("data-variant", variant);
        expect(button).toHaveAttribute("data-size", size);
        expect(button).toBeInTheDocument();
      });
    });
  });
});

describe("Button States", () => {
  test("disabled state prevents interaction", () => {
    const handleClick = vi.fn();
    render(
      <Button disabled onClick={handleClick}>
        Disabled
      </Button>
    );
    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("disabled");
  });

  test("disabled button has correct CSS classes", () => {
    render(<Button disabled>Disabled</Button>);
    const button = screen.getByRole("button");
    expect(button.className).toContain("disabled:pointer-events-none");
    expect(button.className).toContain("disabled:opacity-50");
  });

  test("focus-visible ring classes are present", () => {
    render(<Button>Focus Test</Button>);
    const button = screen.getByRole("button");
    expect(button.className).toContain("focus-visible:ring-ring/50");
    expect(button.className).toContain("focus-visible:ring-[3px]");
    expect(button.className).toContain("focus-visible:border-ring");
  });

  test("aria-invalid classes are present", () => {
    render(<Button aria-invalid="true">Invalid</Button>);
    const button = screen.getByRole("button");
    expect(button.className).toContain("aria-invalid:ring-destructive/20");
    expect(button.className).toContain("aria-invalid:border-destructive");
  });

  test("keyboard activation fires onClick", async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click Me</Button>);

    await user.tab();
    expect(screen.getByRole("button")).toHaveFocus();

    await user.keyboard("{Enter}");
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test("space key activates button", async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click Me</Button>);

    await user.tab();
    await user.keyboard(" ");
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});

describe("Button asChild", () => {
  test("renders as child element when asChild is true", () => {
    render(
      <Button asChild>
        <a href="/test">Link Button</a>
      </Button>
    );
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/test");
    expect(link).toHaveAttribute("data-slot", "button");
  });

  test("renders as button element when asChild is false", () => {
    render(<Button>Normal Button</Button>);
    expect(screen.getByRole("button")).toBeInTheDocument();
  });
});

describe("Button Custom Props", () => {
  test("passes className to the element", () => {
    render(<Button className="custom-class">Test</Button>);
    expect(screen.getByRole("button").className).toContain("custom-class");
  });

  test("passes data attributes", () => {
    render(<Button data-testid="my-button">Test</Button>);
    expect(screen.getByTestId("my-button")).toBeInTheDocument();
  });

  test("passes type attribute", () => {
    render(<Button type="submit">Submit</Button>);
    expect(screen.getByRole("button")).toHaveAttribute("type", "submit");
  });
});

describe("Button Visual Regression (Snapshots)", () => {
  VARIANTS.forEach((variant) => {
    test(`${variant} variant snapshot`, () => {
      const { container } = render(
        <Button variant={variant}>Snapshot</Button>
      );
      expect(container.firstChild).toMatchSnapshot();
    });
  });

  SIZES.forEach((size) => {
    test(`${size} size snapshot`, () => {
      const { container } = render(
        <Button size={size}>Snapshot</Button>
      );
      expect(container.firstChild).toMatchSnapshot();
    });
  });

  test("disabled state snapshot", () => {
    const { container } = render(<Button disabled>Disabled</Button>);
    expect(container.firstChild).toMatchSnapshot();
  });
});
