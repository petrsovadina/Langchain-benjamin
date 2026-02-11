"use client"

import * as React from "react"
import { ScrollArea as ScrollAreaPrimitive } from "radix-ui"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const scrollBarVariants = cva(
  "flex touch-none p-px transition-colors select-none",
  {
    variants: {
      variant: {
        default: "w-2.5",
        thin: "w-1.5",
      },
      orientation: {
        vertical: "h-full border-l border-l-transparent",
        horizontal: "h-2.5 flex-col border-t border-t-transparent",
      },
    },
    defaultVariants: {
      variant: "default",
      orientation: "vertical",
    },
  }
)

interface ScrollAreaProps
  extends React.ComponentProps<typeof ScrollAreaPrimitive.Root>,
    VariantProps<typeof scrollBarVariants> {
  hideScrollbar?: boolean;
}

function ScrollArea({
  className,
  children,
  variant = "default",
  hideScrollbar = false,
  ...props
}: ScrollAreaProps) {
  return (
    <ScrollAreaPrimitive.Root
      data-slot="scroll-area"
      data-variant={variant}
      className={cn("relative", className)}
      {...props}
    >
      <ScrollAreaPrimitive.Viewport
        data-slot="scroll-area-viewport"
        className="focus-visible:ring-ring/50 size-full rounded-[inherit] transition-[color,box-shadow] outline-none focus-visible:ring-[3px] focus-visible:outline-1"
      >
        {children}
      </ScrollAreaPrimitive.Viewport>
      {!hideScrollbar && <ScrollBar variant={variant} />}
      <ScrollAreaPrimitive.Corner />
    </ScrollAreaPrimitive.Root>
  )
}

interface ScrollBarProps
  extends Omit<React.ComponentProps<typeof ScrollAreaPrimitive.ScrollAreaScrollbar>, "orientation">,
    VariantProps<typeof scrollBarVariants> {}

function ScrollBar({
  className,
  orientation = "vertical",
  variant = "default",
  ...props
}: ScrollBarProps) {
  return (
    <ScrollAreaPrimitive.ScrollAreaScrollbar
      data-slot="scroll-area-scrollbar"
      data-variant={variant}
      orientation={orientation ?? "vertical"}
      className={cn(scrollBarVariants({ variant, orientation }), className)}
      {...props}
    >
      <ScrollAreaPrimitive.ScrollAreaThumb
        data-slot="scroll-area-thumb"
        className="bg-border relative flex-1 rounded-full"
      />
    </ScrollAreaPrimitive.ScrollAreaScrollbar>
  )
}

export { ScrollArea, ScrollBar }
