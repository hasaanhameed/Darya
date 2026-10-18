import Link from "next/link";

// Only pages that exist are listed. Add Alerts, Sources, Evaluation and About as they are built.
const NAV_ITEMS = [{ href: "/", label: "Map" }];

export function SiteHeader() {
  return (
    <header className="flex h-12 shrink-0 items-center gap-8 border-b border-rule bg-sheet px-4">
      <Link href="/" className="text-title font-semibold">
        Darya
      </Link>
      <nav aria-label="Main">
        <ul className="flex gap-6">
          {NAV_ITEMS.map((item) => (
            <li key={item.href}>
              <Link href={item.href} className="font-medium text-ink-2 hover:text-ink">
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
}
