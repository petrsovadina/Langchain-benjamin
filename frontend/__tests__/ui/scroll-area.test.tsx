import { render } from "@testing-library/react";
import { ScrollArea } from "@/components/ui/scroll-area";

describe("ScrollArea", () => {
  test("renders with default variant", () => {
    const { container } = render(
      <ScrollArea>
        <div>Content</div>
      </ScrollArea>
    );
    const scrollArea = container.querySelector('[data-slot="scroll-area"]');
    expect(scrollArea).toHaveAttribute("data-variant", "default");
  });

  test("renders with thin variant", () => {
    const { container } = render(
      <ScrollArea variant="thin">
        <div>Content</div>
      </ScrollArea>
    );
    const scrollArea = container.querySelector('[data-slot="scroll-area"]');
    expect(scrollArea).toHaveAttribute("data-variant", "thin");
  });

  test("hides scrollbar when hideScrollbar is true", () => {
    const { container } = render(
      <ScrollArea hideScrollbar>
        <div>Content</div>
      </ScrollArea>
    );
    const scrollbar = container.querySelector('[data-slot="scroll-area-scrollbar"]');
    expect(scrollbar).not.toBeInTheDocument();
  });

  test("shows scrollbar by default", () => {
    const { container } = render(
      <ScrollArea>
        <div>Content</div>
      </ScrollArea>
    );
    const scrollbar = container.querySelector('[data-slot="scroll-area-scrollbar"]');
    expect(scrollbar).toBeInTheDocument();
  });

  test("snapshot test", () => {
    const { container } = render(
      <ScrollArea variant="default">
        <div>Content</div>
      </ScrollArea>
    );
    expect(container.firstChild).toMatchSnapshot();
  });
});
