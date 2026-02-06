import { useRef, useCallback } from "react";

interface SwipeHandlers {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
}

const SWIPE_THRESHOLD = 50;

export function useSwipeGesture(handlers: SwipeHandlers) {
  const startPos = useRef<{ x: number; y: number } | null>(null);

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    startPos.current = { x: e.clientX, y: e.clientY };
  }, []);

  const onPointerUp = useCallback(
    (e: React.PointerEvent) => {
      if (!startPos.current) return;

      const dx = e.clientX - startPos.current.x;
      const dy = e.clientY - startPos.current.y;
      startPos.current = null;

      if (Math.abs(dx) > Math.abs(dy)) {
        if (dx > SWIPE_THRESHOLD) handlers.onSwipeRight?.();
        else if (dx < -SWIPE_THRESHOLD) handlers.onSwipeLeft?.();
      } else {
        if (dy > SWIPE_THRESHOLD) handlers.onSwipeDown?.();
        else if (dy < -SWIPE_THRESHOLD) handlers.onSwipeUp?.();
      }
    },
    [handlers]
  );

  return { onPointerDown, onPointerUp };
}
