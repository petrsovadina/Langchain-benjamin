"use client"

import * as React from "react"
import { HoverCard as HoverCardPrimitive } from "radix-ui"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const hoverCardContentVariants = cva(
  "bg-popover text-popover-foreground data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 z-50 rounded-md border p-4 shadow-md outline-hidden",
  {
    variants: {
      size: {
        sm: "w-56",
        md: "w-72",
        lg: "w-96",
      },
    },
    defaultVariants: {
      size: "md",
    },
  }
)

interface HoverCardProps extends React.ComponentProps<typeof HoverCardPrimitive.Root> {
  openDelay?: number;
  closeDelay?: number;
}

function HoverCard({ openDelay = 200, closeDelay = 100, ...props }: HoverCardProps) {
  return (
    <HoverCardPrimitive.Root openDelay={openDelay} closeDelay={closeDelay} {...props} />
  )
}

function HoverCardTrigger({
  ...props
}: React.ComponentProps<typeof HoverCardPrimitive.Trigger>) {
  return <HoverCardPrimitive.Trigger data-slot="hover-card-trigger" {...props} />
}

interface HoverCardContentProps
  extends React.ComponentProps<typeof HoverCardPrimitive.Content>,
    VariantProps<typeof hoverCardContentVariants> {}

function HoverCardContent({
  className,
  align = "center",
  sideOffset = 4,
  size = "md",
  ...props
}: HoverCardContentProps) {
  return (
    <HoverCardPrimitive.Portal>
      <HoverCardPrimitive.Content
        data-slot="hover-card-content"
        data-size={size}
        align={align}
        sideOffset={sideOffset}
        className={cn(hoverCardContentVariants({ size }), className)}
        {...props}
      />
    </HoverCardPrimitive.Portal>
  )
}

export { HoverCard, HoverCardTrigger, HoverCardContent }
