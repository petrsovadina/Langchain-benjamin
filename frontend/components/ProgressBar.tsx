"use client";

import { useEffect, useState } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const progressBarVariants = cva(
  "fixed left-0 right-0 h-1 bg-surface-muted z-50 transition-opacity duration-300",
  {
    variants: {
      variant: {
        primary: "[&>div]:bg-primary",
        secondary: "[&>div]:bg-secondary",
      },
      position: {
        top: "top-0",
        bottom: "bottom-0",
      },
    },
    defaultVariants: {
      variant: "primary",
      position: "top",
    },
  }
);

interface ProgressBarProps extends VariantProps<typeof progressBarVariants> {
  isLoading: boolean;
  className?: string;
}

export function ProgressBar({
  isLoading,
  variant = "primary",
  position = "top",
  className,
}: ProgressBarProps) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!isLoading) {
      setProgress(0);
      return;
    }

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) return prev;
        return prev + Math.random() * 10;
      });
    }, 300);

    return () => clearInterval(interval);
  }, [isLoading]);

  useEffect(() => {
    if (!isLoading && progress > 0) {
      setProgress(100);
      setTimeout(() => setProgress(0), 500);
    }
  }, [isLoading, progress]);

  if (progress === 0) return null;

  return (
    <div
      data-slot="progress-bar"
      data-variant={variant}
      data-position={position}
      className={cn(progressBarVariants({ variant, position }), className)}
      role="progressbar"
      aria-valuenow={Math.round(progress)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label="Průběh načítání"
    >
      <div
        className="h-full transition-all duration-300 ease-out"
        style={{ width: `${progress}%` }}
      />
    </div>
  );
}
