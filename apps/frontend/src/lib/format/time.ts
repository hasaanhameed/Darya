// Values arrive in UTC (or as plain dates for daily reports) and are shown in Pakistan time.

const PKT = "Asia/Karachi";

const dayFormat = new Intl.DateTimeFormat("en-GB", {
  timeZone: PKT,
  day: "numeric",
  month: "short",
});

const dateTimeFormat = new Intl.DateTimeFormat("en-GB", {
  timeZone: PKT,
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

function isDateOnly(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(value);
}

/** "17 Oct" for a date, "17 Oct, 06:00 PKT" for a UTC timestamp. */
export function formatObservedAt(value: string): string {
  if (isDateOnly(value)) return formatDay(value);
  return `${dateTimeFormat.format(new Date(value))} PKT`;
}

/** "17 Oct". A plain date is a reporting day, so it is not shifted by time zone. */
export function formatDay(date: string): string {
  if (isDateOnly(date)) return dayFormat.format(new Date(`${date}T12:00:00+05:00`));
  return dayFormat.format(new Date(date));
}
