import { createFileRoute } from "@tanstack/react-router";
import { Radio, CheckCircle2, AlertTriangle, PlayCircle } from "lucide-react";
import { AppLayout, StatusDot } from "@/components/app-layout";
import { MetricCard } from "@/components/metric-card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { apiFetch, type Deployment } from "@/lib/api";
import { useEffect, useState } from "react";

export const Route = createFileRoute("/operations")({
  head: () => ({
    meta: [
      { title: "Operations — JOCKY Labs" },
      { name: "description", content: "Track live and completed forensic operations across the JOCKY agent fleet in real time." },
      { property: "og:title", content: "Operations — JOCKY Labs" },
      { property: "og:description", content: "Real-time deployment orchestration." },
    ],
  }),
  component: OpsPage,
});

const statusMeta = {
  executing: { dot: "executing" as const, label: "Executing", cls: "bg-warning/15 text-warning border-warning/30" },
  complete: { dot: "online" as const, label: "Complete", cls: "bg-success/15 text-success border-success/30" },
  warning: { dot: "warning" as const, label: "Attention", cls: "bg-destructive/15 text-destructive border-destructive/30" },
};

function OpsPage() {
  const [operations, setOperations] = useState<Deployment[]>([]);
  const [error, setError] = useState<string>();

  useEffect(() => {
    apiFetch<Deployment[]>("/script/deployments")
      .then(setOperations)
      .catch((err: Error) => setError(err.message));
  }, []);

  const active = operations.filter((operation) => ["pending", "in_progress", "obfuscated"].includes(operation.status));
  const completed = operations.filter((operation) => operation.status === "completed");
  const failed = operations.filter((operation) => operation.status === "failed");

  return (
    <AppLayout
      title="Operations"
      subtitle="Live orchestration of deployed scripts across the fleet."
    >
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard title="Active" value={active.length} icon={PlayCircle} tone="warning" />
        <MetricCard title="Queued" value={operations.filter((operation) => operation.status === "pending").length} icon={Radio} tone="cyber" />
        <MetricCard title="Completed" value={completed.length} icon={CheckCircle2} tone="success" />
        <MetricCard title="Failed" value={failed.length} icon={AlertTriangle} tone="destructive" />
      </div>
      {error && <div className="text-sm text-destructive">{error}</div>}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {operations.map((op) => {
          const status = op.status === "completed" ? "complete" : op.status === "failed" ? "warning" : "executing";
          const m = statusMeta[status];
          const progress = op.status === "completed" ? 100 : op.status === "pending" ? 0 : 50;
          return (
            <div key={op.id} className="panel p-6">
              <div className="flex items-start gap-3">
                <StatusDot status={m.dot} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-semibold text-foreground truncate">{op.name}</h3>
                    <Badge className={m.cls}>{m.label}</Badge>
                  </div>
                  <div className="text-[11px] font-mono text-muted-foreground mt-0.5">
                    {op.deploy_id} · {op.script_name ?? op.script_id} · Agent {op.agent_id} · started {new Date(op.deployed_at).toLocaleString()}
                  </div>
                </div>
              </div>
              <div className="mt-4">
                <Progress value={progress} className="h-1.5" />
                <div className="mt-1.5 flex justify-between text-[11px] font-mono text-muted-foreground">
                  <span>Progress</span><span>{progress}%</span>
                </div>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                <div className="rounded border border-border p-2">
                  <div className="text-[10px] uppercase tracking-widest text-muted-foreground">Findings</div>
                  <div className="text-sm font-bold mt-0.5">{op.result_id ? 1 : 0}</div>
                </div>
                <div className="rounded border border-border p-2">
                  <div className="text-[10px] uppercase tracking-widest text-muted-foreground">Runtime</div>
                  <div className="text-sm font-bold mt-0.5 font-mono">{op.executed_at ? `${Math.max(1, Math.round((new Date(op.executed_at).getTime() - new Date(op.deployed_at).getTime()) / 60000))}m` : "—"}</div>
                </div>
                <div className="rounded border border-border p-2">
                  <div className="text-[10px] uppercase tracking-widest text-muted-foreground">Hash</div>
                  <div className="text-sm font-bold mt-0.5 font-mono text-primary">9e1b…</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </AppLayout>
  );
}
