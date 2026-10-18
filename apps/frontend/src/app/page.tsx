import { Suspense } from "react";

import { Dashboard, DashboardSkeleton } from "@/components/dashboard/Dashboard";

export default function MapPage() {
  // The dashboard reads the selected reach from the URL, which needs a Suspense boundary (useSearchParams).
  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <Dashboard />
    </Suspense>
  );
}
