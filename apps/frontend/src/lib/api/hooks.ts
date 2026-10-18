"use client";

import { useQuery } from "@tanstack/react-query";

import { apiGet } from "@/lib/api/client";
import type { Alert, NodeState, ReachRisk, ReachSeries, RiverNetwork } from "@/lib/api/types";

export function useNetwork() {
  return useQuery({
    queryKey: ["network"],
    queryFn: () => apiGet<RiverNetwork>("/network"),
    staleTime: Infinity, // the river graph rarely changes
  });
}

export function useNodeStates() {
  return useQuery({ queryKey: ["state"], queryFn: () => apiGet<NodeState[]>("/state") });
}

export function useReachRisks() {
  return useQuery({ queryKey: ["risk"], queryFn: () => apiGet<ReachRisk[]>("/risk") });
}

export function useActiveAlerts() {
  return useQuery({
    queryKey: ["alerts", "active"],
    queryFn: () => apiGet<Alert[]>("/alerts?status=active"),
  });
}

export function useReachSeries(reachId: string) {
  return useQuery({
    queryKey: ["series", reachId],
    queryFn: () => apiGet<ReachSeries>(`/reaches/${reachId}/series`),
  });
}
