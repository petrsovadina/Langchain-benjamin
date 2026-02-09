"use client";

import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const messageSkeletonVariants = cva(
  "space-y-3 animate-pulse",
  {
    variants: {
      variant: {
        user: "flex justify-end",
        assistant: "flex justify-start",
      },
    },
    defaultVariants: {
      variant: "assistant",
    },
  }
);

interface MessageSkeletonProps extends VariantProps<typeof messageSkeletonVariants> {
  lines?: 1 | 2 | 3 | 4 | 5;
  showAvatar?: boolean;
  className?: string;
}

export function MessageSkeleton({
  variant = "assistant",
  lines = 2,
  showAvatar = true,
  className,
}: MessageSkeletonProps) {
  return (
    <div
      data-slot="message-skeleton"
      data-variant={variant}
      className={cn(messageSkeletonVariants({ variant }), className)}
      role="status"
      aria-label="Načítání zprávy"
    >
      <div className="flex items-start gap-3 max-w-3xl">
        {showAvatar && variant === "assistant" && (
          <div className="h-8 w-8 rounded-full bg-surface-muted shrink-0" />
        )}
        <div className="flex-1 space-y-2">
          {Array.from({ length: lines }).map((_, i) => (
            <div
              key={i}
              className={cn(
                "h-4 bg-surface-muted rounded",
                i === lines - 1 ? "w-1/2" : "w-3/4"
              )}
            />
          ))}
        </div>
        {showAvatar && variant === "user" && (
          <div className="h-8 w-8 rounded-full bg-surface-muted shrink-0" />
        )}
      </div>
    </div>
  );
}
