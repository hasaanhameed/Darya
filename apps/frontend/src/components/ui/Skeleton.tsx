/** A grey placeholder block shown while data loads. Pulses unless the user prefers reduced motion. */
export function Skeleton({ className = "" }: { className?: string }) {
  return <div aria-hidden className={`rounded-control bg-wash motion-safe:animate-pulse ${className}`} />;
}
