import { useRef, useEffect, useCallback } from "react";

interface UseRetryOptions {
  maxRetries: number;
  baseDelayMs?: number;
  maxDelayMs?: number;
  isRetryable?: (error: Error) => boolean;
}

interface UseRetryReturn {
  retryCount: number;
  isAutoRetrying: boolean;
  scheduleRetry: (fn: () => void) => void;
  resetRetry: () => void;
  cancelRetry: () => void;
  shouldRetry: (error: Error) => boolean;
}

const DEFAULT_RETRYABLE = (err: Error): boolean => {
  const msg = err.message.toLowerCase();
  return (
    msg.includes("network") ||
    msg.includes("fetch") ||
    msg.includes("timeout") ||
    msg.includes("failed to fetch") ||
    msg.includes("503") ||
    msg.includes("502") ||
    msg.includes("429")
  );
};

export function useRetry({
  maxRetries,
  baseDelayMs = 1000,
  maxDelayMs = 8000,
  isRetryable = DEFAULT_RETRYABLE,
}: UseRetryOptions): UseRetryReturn {
  const retryCountRef = useRef(0);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isAutoRetryingRef = useRef(false);

  useEffect(() => {
    return () => {
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
    };
  }, []);

  const cancelRetry = useCallback(() => {
    if (retryTimerRef.current) {
      clearTimeout(retryTimerRef.current);
      retryTimerRef.current = null;
    }
    isAutoRetryingRef.current = false;
  }, []);

  const resetRetry = useCallback(() => {
    cancelRetry();
    retryCountRef.current = 0;
  }, [cancelRetry]);

  const shouldRetry = useCallback(
    (error: Error): boolean => {
      return isRetryable(error) && retryCountRef.current < maxRetries;
    },
    [isRetryable, maxRetries]
  );

  const scheduleRetry = useCallback(
    (fn: () => void) => {
      retryCountRef.current += 1;
      isAutoRetryingRef.current = true;
      const delay = Math.min(baseDelayMs * 2 ** (retryCountRef.current - 1), maxDelayMs);
      retryTimerRef.current = setTimeout(fn, delay);
    },
    [baseDelayMs, maxDelayMs]
  );

  return {
    get retryCount() {
      return retryCountRef.current;
    },
    get isAutoRetrying() {
      return isAutoRetryingRef.current;
    },
    scheduleRetry,
    resetRetry,
    cancelRetry,
    shouldRetry,
  };
}
