import { render } from "@testing-library/react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

describe("Dialog", () => {
  test("renders dialog content with default size", () => {
    const { container } = render(
      <Dialog open>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Test Dialog</DialogTitle>
            <DialogDescription>Test description</DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    );
    const content = container.ownerDocument.querySelector('[data-slot="dialog-content"]');
    expect(content).toHaveAttribute("data-size", "lg");
  });

  test("renders dialog content with sm size", () => {
    const { container } = render(
      <Dialog open>
        <DialogContent size="sm">
          <DialogHeader>
            <DialogTitle>Small Dialog</DialogTitle>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    );
    const content = container.ownerDocument.querySelector('[data-slot="dialog-content"]');
    expect(content).toHaveAttribute("data-size", "sm");
  });

  test("renders dialog content with xl size", () => {
    const { container } = render(
      <Dialog open>
        <DialogContent size="xl">
          <DialogHeader>
            <DialogTitle>XL Dialog</DialogTitle>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    );
    const content = container.ownerDocument.querySelector('[data-slot="dialog-content"]');
    expect(content).toHaveAttribute("data-size", "xl");
  });

  test("renders dialog content with full size", () => {
    const { container } = render(
      <Dialog open>
        <DialogContent size="full">
          <DialogHeader>
            <DialogTitle>Full Dialog</DialogTitle>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    );
    const content = container.ownerDocument.querySelector('[data-slot="dialog-content"]');
    expect(content).toHaveAttribute("data-size", "full");
  });

  test("hides close button when showCloseButton is false", () => {
    const { container } = render(
      <Dialog open>
        <DialogContent showCloseButton={false}>
          <DialogHeader>
            <DialogTitle>No Close</DialogTitle>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    );
    const closeButtons = container.ownerDocument.querySelectorAll('[data-slot="dialog-close"]');
    expect(closeButtons).toHaveLength(0);
  });

  test("renders dialog content with default variant", () => {
    const { container } = render(
      <Dialog open>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Default Dialog</DialogTitle>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    );
    const content = container.ownerDocument.querySelector('[data-slot="dialog-content"]');
    expect(content).toHaveAttribute("data-variant", "default");
  });

  test("renders dialog content with centered variant", () => {
    const { container } = render(
      <Dialog open>
        <DialogContent variant="centered">
          <DialogHeader>
            <DialogTitle>Centered Dialog</DialogTitle>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    );
    const content = container.ownerDocument.querySelector('[data-slot="dialog-content"]');
    expect(content).toHaveAttribute("data-variant", "centered");
  });

  test("renders all sub-components", () => {
    const { container } = render(
      <Dialog open>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Title</DialogTitle>
            <DialogDescription>Description</DialogDescription>
          </DialogHeader>
          <DialogFooter>Footer</DialogFooter>
        </DialogContent>
      </Dialog>
    );
    expect(container.ownerDocument.querySelector('[data-slot="dialog-content"]')).toBeInTheDocument();
    expect(container.ownerDocument.querySelector('[data-slot="dialog-header"]')).toBeInTheDocument();
    expect(container.ownerDocument.querySelector('[data-slot="dialog-title"]')).toBeInTheDocument();
    expect(container.ownerDocument.querySelector('[data-slot="dialog-description"]')).toBeInTheDocument();
    expect(container.ownerDocument.querySelector('[data-slot="dialog-footer"]')).toBeInTheDocument();
  });
});
