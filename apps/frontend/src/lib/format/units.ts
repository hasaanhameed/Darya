const wholeNumber = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const oneDecimal = new Intl.NumberFormat("en-US", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

/** Discharge in cusecs, e.g. "312,400". The unit is shown separately. */
export function formatCfs(flow_cfs: number): string {
  return wholeNumber.format(flow_cfs);
}

/** Reservoir level in feet, e.g. "1,546.3". */
export function formatFt(level_ft: number): string {
  return oneDecimal.format(level_ft);
}
