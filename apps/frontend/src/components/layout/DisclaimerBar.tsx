export function DisclaimerBar() {
  return (
    <p className="shrink-0 border-t border-deep-rule bg-deep px-4 py-1 text-meta text-deep-ink-2">
      Not an official flood warning. For official warnings, see{" "}
      <a href="https://ffd.pmd.gov.pk" className="text-deep-ink underline" target="_blank" rel="noreferrer">
        PMD-FFD
      </a>
      .
    </p>
  );
}
