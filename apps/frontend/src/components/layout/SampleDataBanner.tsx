import { USE_SAMPLE_DATA } from "@/lib/api/client";

export function SampleDataBanner() {
  if (!USE_SAMPLE_DATA) return null;
  return (
    <p role="status" className="shrink-0 bg-ink px-4 py-1 text-meta font-medium text-sheet">
      Sample data, not live. Every flow, level, forecast and alert on this page is made up for development.
    </p>
  );
}
