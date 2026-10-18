"use client";

import { CaretDownIcon } from "@phosphor-icons/react";
import { useId, useState, type ReactNode } from "react";

interface CollapsibleProps {
  title: ReactNode;
  /** Shown at the right of the header, and still visible when collapsed (e.g. a count). */
  aside?: ReactNode;
  /** "section" is a rail section with a tinted header bar; "group" is a lighter sub-heading inside one. */
  level?: "section" | "group";
  defaultOpen?: boolean;
  children: ReactNode;
}

/** A heading that opens and closes the content under it. */
export function Collapsible({ title, aside, level = "section", defaultOpen = true, children }: CollapsibleProps) {
  const [open, setOpen] = useState(defaultOpen);
  const contentId = useId();
  const Heading = level === "section" ? "h2" : "h3";
  const headerClass =
    level === "section"
      ? "bg-shallows-2 px-4 py-2 text-title font-semibold hover:bg-shallows-3"
      : "px-4 py-1.5 font-semibold hover:bg-shallows-2";

  return (
    <section>
      <Heading>
        <button
          type="button"
          onClick={() => setOpen(!open)}
          aria-expanded={open}
          aria-controls={contentId}
          className={`flex w-full items-center gap-2 text-left ${headerClass}`}
        >
          <CaretDownIcon
            size={level === "section" ? 14 : 12}
            weight="bold"
            aria-hidden
            className={`shrink-0 text-ink-2 transition-transform duration-150 ease-out ${open ? "" : "-rotate-90"}`}
          />
          <span className="flex-1">{title}</span>
          {aside}
        </button>
      </Heading>
      <div id={contentId} hidden={!open}>
        {children}
      </div>
    </section>
  );
}
