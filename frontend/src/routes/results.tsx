import { createFileRoute, Link } from "@tanstack/react-router";
import { AlertTriangle, ShieldAlert, Network, Zap, FileText } from "lucide-react";
import { AppLayout } from "@/components/app-layout";
import { MetricCard } from "@/components/metric-card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiFetch, type Result } from "@/lib/api";
import { useEffect, useMemo, useState } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";

export const Route = createFileRoute("/results")({
  head: () => ({
    meta: [
      { title: "Results — Proteus" },
      { name: "description", content: "Review and analyze forensic artifacts, memory dumps, and execution logs from deployed agents." },
      { property: "og:title", content: "Results — Proteus" },
      { property: "og:description", content: "Every finding, correlated." },
    ],
  }),
  component: ResultsPage,
});

const sevColor = {
  high: "text-destructive border-destructive/30 bg-destructive/10",
  medium: "text-warning border-warning/30 bg-warning/10",
  low: "text-success border-success/30 bg-success/10",
} as const;

function ResultsPage() {
  const [results, setResults] = useState<Result[]>([]);
  const [error, setError] = useState<string>();

  useEffect(() => {
    apiFetch<Result[]>("/result/list")
      .then(setResults)
      .catch((err: Error) => setError(err.message));
  }, []);

  const severityMix = useMemo(() => [
    { name: "Results", value: results.length, color: "oklch(0.85 0.16 220)" },
  ], [results.length]);

  return (
    <AppLayout
      title="Results"
      subtitle="Correlated findings across the fleet — ready for triage or report."
      actions={
        <Button asChild className="bg-primary text-primary-foreground hover:bg-primary/90 glow-cyber">
          <Link to="/reports"><FileText className="mr-2 h-4 w-4" />Generate Report</Link>
        </Button>
      }
    >
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard title="Total Results" value={results.length} icon={AlertTriangle} tone="cyber" />
        <MetricCard title="Submitted Results" value={results.length} icon={ShieldAlert} tone="warning" />
        <MetricCard title="Agents Reporting" value={new Set(results.map((result) => result.agent_id)).size} icon={Network} tone="success" />
        <MetricCard title="Scripts Reporting" value={new Set(results.map((result) => result.script_id)).size} icon={Zap} tone="destructive" />
      </div>
      {error && <div className="text-sm text-destructive">{error}</div>}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <div className="panel p-6 xl:col-span-2">
          <Tabs defaultValue="overview">
            <TabsList className="bg-background/60 border border-border">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="registry">Registry</TabsTrigger>
              <TabsTrigger value="files">File System</TabsTrigger>
              <TabsTrigger value="network">Network</TabsTrigger>
              <TabsTrigger value="process">Process</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="mt-4">
              <ul className="divide-y divide-border">
                {results.map((result) => (
                  <li key={result.result_id} className="py-4 flex items-start gap-3">
                    <span className="shrink-0 rounded-md border px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider text-primary border-primary/30 bg-primary/10">
                      result
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium">Result {result.result_id}</div>
                      <div className="text-xs text-muted-foreground">Encrypted payload: {result.data_encrypted}</div>
                    </div>
                    <div className="text-[11px] font-mono text-muted-foreground whitespace-nowrap">{result.agent_id}</div>
                  </li>
                ))}
              </ul>
            </TabsContent>

            <TabsContent value="registry" className="mt-4">
              <pre className="font-mono text-xs bg-background/60 border border-border rounded-md p-4 overflow-x-auto text-muted-foreground">
{`HKCU\\Software
├── Microsoft
│   └── Windows
│       └── CurrentVersion
│           └── Run
│               ├── OneDriveSetup    (unchanged)
│               ├── SecurityHealth   (unchanged)
│               └── svchost_helper   ★ ADDED  9m ago
└── Classes
    └── .jql                          ★ NEW    12m ago`}
              </pre>
            </TabsContent>

            <TabsContent value="files" className="mt-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                {["C:\\Users\\Public\\svchost_.exe", "C:\\Windows\\Temp\\dumpx.dat", "/etc/hosts", "/var/log/auth.log", "/tmp/.hidden-cache", "%APPDATA%\\Roaming\\jql_stub"].map((p) => (
                  <div key={p} className="rounded-md border border-border bg-background/40 p-3">
                    <div className="font-mono text-xs text-foreground truncate">{p}</div>
                    <div className="text-[11px] text-muted-foreground mt-1">Modified · integrity mismatch</div>
                  </div>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="network" className="mt-4">
              <table className="w-full text-sm">
                <thead className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground">
                  <tr><th className="text-left py-2">Local</th><th className="text-left py-2">Remote</th><th className="text-left py-2">State</th><th className="text-left py-2">Process</th></tr>
                </thead>
                <tbody className="font-mono text-xs">
                  {[
                    ["10.14.2.41:52341", "185.220.101.47:443", "ESTABLISHED", "chrome.exe"],
                    ["10.14.0.11:4444", "0.0.0.0:*", "LISTEN", "svchost_.exe"],
                    ["10.14.1.19:22", "10.14.0.11:51234", "ESTABLISHED", "sshd"],
                    ["10.14.3.88:53", "8.8.8.8:53", "ESTABLISHED", "mDNSResponder"],
                  ].map((r) => (
                    <tr key={r.join()} className="border-t border-border">
                      <td className="py-2">{r[0]}</td><td>{r[1]}</td>
                      <td><Badge className="bg-panel border-border text-[10px]">{r[2]}</Badge></td>
                      <td>{r[3]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TabsContent>

            <TabsContent value="process" className="mt-4">
              <ul className="space-y-2 text-sm">
                {[
                  { pid: 4128, name: "svchost_.exe", user: "SYSTEM", cpu: "12%", flag: "unsigned" },
                  { pid: 2211, name: "chrome.exe", user: "jdoe", cpu: "3%", flag: "ok" },
                  { pid: 780, name: "explorer.exe", user: "jdoe", cpu: "1%", flag: "ok" },
                  { pid: 5501, name: "powershell.exe", user: "SYSTEM", cpu: "8%", flag: "hidden window" },
                ].map((p) => (
                  <li key={p.pid} className="rounded-md border border-border bg-background/40 p-3 flex items-center gap-3">
                    <span className="font-mono text-xs text-muted-foreground w-16">PID {p.pid}</span>
                    <span className="font-medium">{p.name}</span>
                    <span className="text-xs text-muted-foreground">{p.user}</span>
                    <span className="ml-auto text-xs font-mono">{p.cpu}</span>
                    <Badge className={p.flag === "ok" ? "bg-success/10 text-success border-success/30" : "bg-destructive/10 text-destructive border-destructive/30"}>
                      {p.flag}
                    </Badge>
                  </li>
                ))}
              </ul>
            </TabsContent>
          </Tabs>
        </div>

        <div className="panel p-6">
          <div className="mb-2">
            <h3 className="text-sm font-semibold">Findings by Severity</h3>
            <p className="text-xs text-muted-foreground">Last 24 hours</p>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={severityMix} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} strokeWidth={0}>
                  {severityMix.map((s) => <Cell key={s.name} fill={s.color} />)}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "oklch(0.2 0.03 260)",
                    border: "1px solid oklch(0.32 0.03 260)",
                    borderRadius: 8, fontSize: 12,
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
