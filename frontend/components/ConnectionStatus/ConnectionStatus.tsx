"use client";

import { useEffect, useState } from "react";
import { fetchHealth } from "@/lib/api";
import type { HealthResponse } from "@/types/api";

type Status = "checking" | "connected" | "disconnected";

export function ConnectionStatus(): React.ReactElement {
  const [status, setStatus] = useState<Status>("checking");
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function check(): Promise<void> {
      try {
        const result = await fetchHealth();
        if (!cancelled) {
          setHealth(result);
          setStatus("connected");
        }
      } catch {
        if (!cancelled) {
          setStatus("disconnected");
        }
      }
    }

    void check();
    const interval = setInterval(() => void check(), 5000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const dotColor =
    status === "connected"
      ? "bg-emerald-500"
      : status === "checking"
        ? "bg-amber-400"
        : "bg-red-500";

  const label =
    status === "connected"
      ? "Connected"
      : status === "checking"
        ? "Checking..."
        : "Disconnected";

  return (
    <div className="flex flex-col gap-1 text-sm">
      <div className="flex items-center gap-2">
        <span className={`h-2.5 w-2.5 rounded-full ${dotColor}`} aria-hidden />
        <span className="font-medium text-slate-700">{label}</span>
      </div>
      {health ? (
        <span className="text-xs text-slate-400">
          model: {health.model_type} · ML pipeline: {health.ml_pipeline_status}
        </span>
      ) : null}
    </div>
  );
}
