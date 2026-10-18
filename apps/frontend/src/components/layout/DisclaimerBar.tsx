export function DisclaimerBar() {
  return (
    <p className="shrink-0 border-b border-rule px-4 py-1 text-meta text-ink-2">
      Research prototype. Not an official flood warning. For official warnings, see{" "}
      <a href="https://ffd.pmd.gov.pk" className="underline hover:text-ink" target="_blank" rel="noreferrer">
        PMD-FFD
      </a>
      .
    </p>
  );
}
