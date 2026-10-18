"use client";

import { useEffect, useRef, useState, type KeyboardEvent, type PointerEvent } from "react";

export const RAIL_WIDTH = { min: 220, max: 480, default: 272 };
const KEYBOARD_STEP = 16;
const STORAGE_KEY = "darya.railWidth";

const clamp = (width: number) => Math.min(RAIL_WIDTH.max, Math.max(RAIL_WIDTH.min, Math.round(width)));

/** The rail width, remembered in this browser. Starts at the default so server and client render the same. */
export function useRailWidth() {
  const [width, setWidth] = useState(RAIL_WIDTH.default);

  useEffect(() => {
    try {
      const saved = Number(localStorage.getItem(STORAGE_KEY));
      // eslint-disable-next-line react-hooks/set-state-in-effect -- reading browser storage after hydration
      if (saved) setWidth(clamp(saved));
    } catch {
      // Storage can be blocked (private mode). The default width is fine.
    }
  }, []);

  function changeWidth(next: number) {
    const clamped = clamp(next);
    setWidth(clamped);
    try {
      localStorage.setItem(STORAGE_KEY, String(clamped));
    } catch {
      // See above.
    }
  }

  return [width, changeWidth] as const;
}

interface RailResizeHandleProps {
  width: number;
  onChange: (width: number) => void;
}

/** Drag, or focus and use the arrow keys, to resize the rail. Double-click resets it. */
export function RailResizeHandle({ width, onChange }: RailResizeHandleProps) {
  const drag = useRef<{ startX: number; startWidth: number } | null>(null);
  const [dragging, setDragging] = useState(false);

  function handlePointerDown(event: PointerEvent<HTMLDivElement>) {
    event.currentTarget.setPointerCapture(event.pointerId);
    drag.current = { startX: event.clientX, startWidth: width };
    setDragging(true);
  }

  function handlePointerMove(event: PointerEvent<HTMLDivElement>) {
    if (!drag.current) return;
    onChange(drag.current.startWidth + event.clientX - drag.current.startX);
  }

  function handlePointerUp() {
    drag.current = null;
    setDragging(false);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    const next: Record<string, number> = {
      ArrowLeft: width - KEYBOARD_STEP,
      ArrowRight: width + KEYBOARD_STEP,
      Home: RAIL_WIDTH.min,
      End: RAIL_WIDTH.max,
    };
    if (event.key in next) {
      event.preventDefault();
      onChange(next[event.key]);
    }
  }

  return (
    <div
      role="separator"
      aria-orientation="vertical"
      aria-label="Resize the side panel"
      aria-valuenow={width}
      aria-valuemin={RAIL_WIDTH.min}
      aria-valuemax={RAIL_WIDTH.max}
      tabIndex={0}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
      onKeyDown={handleKeyDown}
      onDoubleClick={() => onChange(RAIL_WIDTH.default)}
      title="Drag to resize. Double-click to reset."
      className="group absolute inset-y-0 -right-1.5 z-20 flex w-3 cursor-col-resize touch-none justify-center"
    >
      <span
        className={`w-0.5 ${dragging ? "bg-channel" : "bg-transparent group-hover:bg-rule-strong group-focus-visible:bg-channel"}`}
      />
    </div>
  );
}
