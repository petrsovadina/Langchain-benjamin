"use client";

import { WifiOff } from "lucide-react";
import { cn } from "@/lib/utils";

interface OfflineBannerProps {
  message?: string;
  className?: string;
}

export function OfflineBanner({
  message = "Jste offline. Připojte se k internetu pro odeslání dotazu.",
  className,
}: OfflineBannerProps) {
  return (
    <div
      data-slot="offline-banner"
      className={cn(
        "bg-destructive/10 border border-destructive rounded-lg px-4 py-2",
        "text-sm text-destructive flex items-center gap-2",
        "animate-pulse animate-in slide-in-from-top-2",
        className
      )}
      role="alert"
      aria-live="polite"
    >
      <WifiOff className="h-4 w-4 shrink-0" aria-hidden="true" />
      {message}
    </div>
  );
}
