import { render } from "@testing-library/react";
import { HoverCard, HoverCardTrigger, HoverCardContent } from "@/components/ui/hover-card";

describe("HoverCard", () => {
  test("renders trigger with data-slot", () => {
    const { container } = render(
      <HoverCard>
        <HoverCardTrigger>Trigger</HoverCardTrigger>
        <HoverCardContent>Content</HoverCardContent>
      </HoverCard>
    );
    const trigger = container.querySelector('[data-slot="hover-card-trigger"]');
    expect(trigger).toBeInTheDocument();
  });

  test("renders content with default size", () => {
    const { container } = render(
      <HoverCard open>
        <HoverCardTrigger>Trigger</HoverCardTrigger>
        <HoverCardContent>Content</HoverCardContent>
      </HoverCard>
    );
    const content = container.ownerDocument.querySelector('[data-slot="hover-card-content"]');
    expect(content).toHaveAttribute("data-size", "md");
  });

  test("renders content with sm size", () => {
    const { container } = render(
      <HoverCard open>
        <HoverCardTrigger>Trigger</HoverCardTrigger>
        <HoverCardContent size="sm">Small Content</HoverCardContent>
      </HoverCard>
    );
    const content = container.ownerDocument.querySelector('[data-slot="hover-card-content"]');
    expect(content).toHaveAttribute("data-size", "sm");
  });

  test("renders content with lg size", () => {
    const { container } = render(
      <HoverCard open>
        <HoverCardTrigger>Trigger</HoverCardTrigger>
        <HoverCardContent size="lg">Large Content</HoverCardContent>
      </HoverCard>
    );
    const content = container.ownerDocument.querySelector('[data-slot="hover-card-content"]');
    expect(content).toHaveAttribute("data-size", "lg");
  });
});
