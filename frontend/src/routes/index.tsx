import { createFileRoute, Link } from "@tanstack/react-router";
import {
  Bot, Wifi, Radio, AlertTriangle, Play, FilePlus2, BarChart3, Shield, ChevronRight,
} from "lucide-react";
import { AppLayout, StatusDot } from "@/components/app-layout";
import { MetricCard } from "@/components/metric-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiFetch, type Agent, type Deployment, type Result } from "@/lib/api";
import { useEffect, useState } from "react";
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Dashboard — JOCKY Labs" },
      { name: "description", content: "Live forensic operations dashboard: agent fleet, active operations, findings, and stealth-mode status." },
      { property: "og:title", content: "JOCKY Labs Dashboard" },
      { property: "og:description", content: "Live forensic operations at a glance." },
    ],
  }),
  component: Dashboard,
});

const sevColor = {
  high: "text-destructive border-destructive/30 bg-destructive/10",
  medium: "text-warning border-warning/30 bg-warning/10",
  low: "text-success border-success/30 bg-success/10",
} as const;

function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [results, setResults] = useState<Result[]>([]);
  const [error, setError] = useState<string>();

  useEffect(() => {
    Promise.all([
      apiFetch<Agent[]>("/agent/list"),
      apiFetch<Deployment[]>("/script/deployments"),
      apiFetch<Result[]>("/result/list"),
    ]).then(([agentData, deploymentData, resultData]) => {
      setAgents(agentData);
      setDeployments(deploymentData);
      setResults(resultData);
    }).catch((err: Error) => setError(err.message));
  }, []);

  const activity = results.slice(0, 12).reverse().map((result, index) => ({
    h: new Date(result.submitted_at).toLocaleTimeString([], { hour: "2-digit", hour12: false }),
    ops: deployments.filter((deployment) => deployment.deployed_at <= result.submitted_at).length,
    alerts: index + 1,
  }));
  const online = agents.filter((agent) => agent.status === "online").length;
  const active = deployments.filter((deployment) => ["pending", "in_progress", "obfuscated"].includes(deployment.status)).length;

  return (
    <AppLayout
      title="Next-Gen Forensic Analysis. Zero Detection."
      subtitle="Centralized investigation intelligence — all systems operational."
      actions={
        <>
          <Button asChild variant="outline" className="border-border">
            <Link to="/results"><BarChart3 className="mr-2 h-4 w-4" />View Results</Link>
          </Button>
          <Button asChild variant="outline" className="border-border">
            <Link to="/operations"><Play className="mr-2 h-4 w-4" />Deploy Script</Link>
          </Button>
          <Button asChild className="bg-primary text-primary-foreground hover:bg-primary/90 glow-cyber">
            <Link to="/scripts"><FilePlus2 className="mr-2 h-4 w-4" />Create Script</Link>
          </Button>
        </>
      }
    >
      {/* Status strip */}
      <div className="panel p-5 flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <StatusDot status="online" />
          <span className="text-sm font-medium text-foreground">All Systems Operational</span>
        </div>
        {error && <div className="text-sm text-destructive">{error}</div>}
        <div className="h-4 w-px bg-border" />
        <div className="flex items-center gap-2 text-sm">
          <Shield className="h-4 w-4 text-primary" />
          <span className="text-foreground">Stealth Mode</span>
          <Badge className="bg-success/15 text-success border-success/30">Active</Badge>
        </div>
        <div className="h-4 w-px bg-border hidden md:block" />
        <div className="hidden md:flex items-center gap-2 text-xs font-mono text-muted-foreground">
          <span>Polymorphic Engine</span>
          <span className="text-primary">a7f4c9…</span>
          <ChevronRight className="h-3 w-3" />
          <span className="text-primary">9e1b3d…</span>
        </div>
        <div className="ml-auto text-xs font-mono text-muted-foreground">
          Session · <span className="text-foreground">42h 11m</span>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard title="Total Agents" value={agents.length} delta="From backend" icon={Bot} tone="cyber" />
        <MetricCard title="Agents Online" value={online} delta="Current status" icon={Wifi} tone="success" />
        <MetricCard title="Active Operations" value={active} delta="Pending or running" icon={Radio} tone="warning" />
        <MetricCard title="Open Findings" value={results.length} delta="Submitted results" icon={AlertTriangle} tone="destructive" />
      </div>

      {/* Activity + Findings */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <div className="panel p-6 xl:col-span-2">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-sm font-semibold text-foreground">Activity — 24h</h3>
              <p className="text-xs text-muted-foreground">Operations and alerts per interval</p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-primary" />Ops</span>
              <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-destructive" />Alerts</span>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={activity}>
                <defs>
                  <linearGradient id="gOps" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="oklch(0.85 0.16 220)" stopOpacity={0.5} />
                    <stop offset="100%" stopColor="oklch(0.85 0.16 220)" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gAlerts" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="oklch(0.65 0.22 25)" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="oklch(0.65 0.22 25)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="oklch(0.32 0.03 260 / 0.4)" strokeDasharray="3 3" />
                <XAxis dataKey="h" stroke="oklch(0.72 0.03 255)" fontSize={11} />
                <YAxis stroke="oklch(0.72 0.03 255)" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    background: "oklch(0.2 0.03 260)",
                    border: "1px solid oklch(0.32 0.03 260)",
                    borderRadius: 8, fontSize: 12,
                  }}
                />
                <Area type="monotone" dataKey="ops" stroke="oklch(0.85 0.16 220)" fill="url(#gOps)" strokeWidth={2} />
                <Area type="monotone" dataKey="alerts" stroke="oklch(0.65 0.22 25)" fill="url(#gAlerts)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-sm font-semibold text-foreground">Latest Findings</h3>
              <p className="text-xs text-muted-foreground">Newest alerts across the fleet</p>
            </div>
            <Link to="/results" className="text-xs text-primary hover:underline">View all</Link>
          </div>
          <ul className="divide-y divide-border">
            {results.slice(0, 6).map((result) => (
              <li key={result.result_id} className="py-4 flex items-start gap-3">
                <span className="shrink-0 rounded-md border px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider text-primary border-primary/30 bg-primary/10">
                  result
                </span>
                <div className="min-w-0 flex-1">
                  <div className="text-sm text-foreground truncate">Result {result.result_id}</div>
                  <div className="text-xs text-muted-foreground truncate">Agent {result.agent_id} · Script {result.script_id}</div>
                </div>
                <div className="text-[11px] font-mono text-muted-foreground whitespace-nowrap">{new Date(result.submitted_at).toLocaleString()}</div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </AppLayout>
  );
}
