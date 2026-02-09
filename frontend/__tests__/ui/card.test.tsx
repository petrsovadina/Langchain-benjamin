import { render } from "@testing-library/react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";

describe("Card", () => {
  test("renders with default variant", () => {
    const { container } = render(<Card>Content</Card>);
    const card = container.querySelector('[data-slot="card"]');
    expect(card).toBeInTheDocument();
    expect(card).toHaveAttribute("data-variant", "default");
    expect(card).toHaveAttribute("data-padding", "default");
  });

  test("renders with elevated variant", () => {
    const { container } = render(<Card variant="elevated">Content</Card>);
    const card = container.querySelector('[data-slot="card"]');
    expect(card).toHaveAttribute("data-variant", "elevated");
  });

  test("renders with outline variant", () => {
    const { container } = render(<Card variant="outline">Content</Card>);
    const card = container.querySelector('[data-slot="card"]');
    expect(card).toHaveAttribute("data-variant", "outline");
  });

  test("renders with compact padding", () => {
    const { container } = render(<Card padding="compact">Content</Card>);
    const card = container.querySelector('[data-slot="card"]');
    expect(card).toHaveAttribute("data-padding", "compact");
  });

  test("renders with spacious padding", () => {
    const { container } = render(<Card padding="spacious">Content</Card>);
    const card = container.querySelector('[data-slot="card"]');
    expect(card).toHaveAttribute("data-padding", "spacious");
  });

  test("renders all sub-components", () => {
    const { container } = render(
      <Card>
        <CardHeader>
          <CardTitle>Title</CardTitle>
          <CardDescription>Description</CardDescription>
        </CardHeader>
        <CardContent>Body</CardContent>
        <CardFooter>Footer</CardFooter>
      </Card>
    );

    expect(container.querySelector('[data-slot="card"]')).toBeInTheDocument();
    expect(container.querySelector('[data-slot="card-header"]')).toBeInTheDocument();
    expect(container.querySelector('[data-slot="card-title"]')).toBeInTheDocument();
    expect(container.querySelector('[data-slot="card-description"]')).toBeInTheDocument();
    expect(container.querySelector('[data-slot="card-content"]')).toBeInTheDocument();
    expect(container.querySelector('[data-slot="card-footer"]')).toBeInTheDocument();
  });

  test("snapshot test", () => {
    const { container } = render(
      <Card variant="elevated" padding="compact">
        <CardHeader>
          <CardTitle>Test</CardTitle>
        </CardHeader>
        <CardContent>Content</CardContent>
      </Card>
    );
    expect(container.firstChild).toMatchSnapshot();
  });
});
