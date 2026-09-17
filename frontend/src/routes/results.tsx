import { createFileRoute, Link } from "@tanstack/react-router";
import {
  AlertTriangle,
  ShieldAlert,
  Network,
  Zap,
  FileText,
  FileCode,
  Copy,
  Check,
  Download,
  Trash2,
  Terminal,
  RefreshCw,
} from "lucide-react";
import { AppLayout } from "@/components/app-layout";
import { MetricCard } from "@/components/metric-card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { apiFetch, type Result } from "@/lib/api";
import { useEffect, useMemo, useState } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
import { toast } from "sonner";

export const Route = createFileRoute("/results")({
  head: () => ({
    meta: [
      { title: "Results — Proteus & JOCKY" },
      {
        name: "description",
        content:
          "Review and analyze forensic artifacts, memory dumps, and execution telemetry from deployed agents.",
      },
      { property: "og:title", content: "Results — Proteus" },
      { property: "og:description", content: "Every finding, correlated." },
    ],
  }),
  component: ResultsPage,
});

function ResultsPage() {
  const [results, setResults] = useState<Result[]>([]);
  const [error, setError] = useState<string>();
  const [loading, setLoading] = useState(false);

  // JSON Modal State
  const [jsonModalOpen, setJsonModalOpen] = useState(false);
  const [selectedResult, setSelectedResult] = useState<Result | null>(null);
  const [fullResultJson, setFullResultJson] = useState<string>("");
  const [fetchingDetails, setFetchingDetails] = useState(false);
  const [copied, setCopied] = useState(false);

  const loadResults = () => {
    setLoading(true);
    apiFetch<Result[]>("/result/list")
      .then((data) => {
        setResults(data);
        setError(undefined);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadResults();
  }, []);

  // Fetch full details and open JSON Modal
  const handleViewJson = async (result: Result) => {
    setSelectedResult(result);
    setJsonModalOpen(true);
    setFetchingDetails(true);
    setCopied(false);

    try {
      // Fetch untruncated result from backend
      const full = await apiFetch<Result>(`/result/view?result_id=${result.result_id}`);

      // Try to parse inner data_encrypted if it's serialized JSON
      let parsedPayload: unknown = full.data_encrypted;
      try {
        if (typeof full.data_encrypted === "string") {
          parsedPayload = JSON.parse(full.data_encrypted);
        }
      } catch {
        parsedPayload = full.data_encrypted;
      }

      const formatted = {
        result_id: full.result_id,
        agent_id: full.agent_id,
        script_id: full.script_id,
        submitted_at: full.submitted_at,
        payload: parsedPayload,
      };

      setFullResultJson(JSON.stringify(formatted, null, 2));
    } catch {
      // Fallback to local result object
      let parsedPayload: unknown = result.data_encrypted;
      try {
        if (typeof result.data_encrypted === "string") {
          parsedPayload = JSON.parse(result.data_encrypted);
        }
      } catch {
        parsedPayload = result.data_encrypted;
      }

      const fallback = {
        result_id: result.result_id,
        agent_id: result.agent_id,
        script_id: result.script_id,
        submitted_at: result.submitted_at,
        payload: parsedPayload,
      };
      setFullResultJson(JSON.stringify(fallback, null, 2));
    } finally {
      setFetchingDetails(false);
    }
  };

  const handleCopyJson = () => {
    if (!fullResultJson) return;
    navigator.clipboard.writeText(fullResultJson);
    setCopied(true);
    toast.success("JSON Copied to Clipboard", {
      description: "Forensic telemetry payload copied successfully.",
    });
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadJson = () => {
    if (!fullResultJson || !selectedResult) return;
    const blob = new Blob([fullResultJson], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `result_${selectedResult.result_id.slice(0, 8)}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success("JSON Export Downloaded", {
      description: `Saved result_${selectedResult.result_id.slice(0, 8)}.json to your device.`,
    });
  };

  const handleDeleteResult = async (result: Result) => {
    if (!window.confirm(`Delete result ${result.result_id.slice(0, 8)}? This cannot be undone.`)) {
      return;
    }
    try {
      await apiFetch(`/result/${result.result_id}`, { method: "DELETE" });
      setResults((current) => current.filter((item) => item.result_id !== result.result_id));
      if (selectedResult?.result_id === result.result_id) {
        setJsonModalOpen(false);
        setSelectedResult(null);
      }
      toast.success("Result deleted");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to delete result");
    }
  };

  const severityMix = useMemo(
    () => [
      { name: "Critical Telemetry", value: Math.max(1, Math.ceil(results.length * 0.4)), color: "#E879F9" },
      { name: "High Security", value: Math.max(1, Math.floor(results.length * 0.35)), color: "#A855F7" },
      { name: "Standard Findings", value: Math.max(1, Math.floor(results.length * 0.25)), color: "#7C3AED" },
    ],
    [results.length]
  );

  return (
    <AppLayout
      title="Results"
      subtitle="Correlated forensic artifacts, execution telemetry, and structured findings across the agent grid."
      actions={
        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            onClick={loadResults}
            disabled={loading}
            className="border-border"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin text-primary" : ""}`} />
            Refresh
          </Button>
          <Button asChild className="bg-primary text-primary-foreground hover:bg-primary/90 glow-cyber text-xs">
            <Link to="/reports">
              <FileText className="mr-2 h-4 w-4" />
              Generate Report
            </Link>
          </Button>
        </div>
      }
    >
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard title="Total Results" value={results.length} icon={AlertTriangle} tone="cyber" />
        <MetricCard title="Submitted Results" value={results.length} icon={ShieldAlert} tone="warning" />
        <MetricCard
          title="Agents Reporting"
          value={new Set(results.map((result) => result.agent_id)).size}
          icon={Network}
          tone="success"
        />
        <MetricCard
          title="Scripts Reporting"
          value={new Set(results.map((result) => result.script_id)).size}
          icon={Zap}
          tone="destructive"
        />
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/30 text-destructive text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <div className="panel p-6 xl:col-span-2">
          <Tabs defaultValue="overview">
            <div className="flex items-center justify-between pb-2 border-b border-border/60">
              <TabsList className="bg-background/60 border border-border">
                <TabsTrigger value="overview">Overview ({results.length})</TabsTrigger>
                <TabsTrigger value="registry">Registry</TabsTrigger>
                <TabsTrigger value="files">File System</TabsTrigger>
                <TabsTrigger value="network">Network</TabsTrigger>
                <TabsTrigger value="process">Process</TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="overview" className="mt-4">
              {loading && results.length === 0 ? (
                <div className="py-6 space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className="h-16 rounded-xl bg-white/[0.03] border border-white/[0.06] animate-pulse flex items-center px-4 gap-3"
                    >
                      <div className="h-6 w-16 rounded bg-white/10" />
                      <div className="space-y-1.5 flex-1">
                        <div className="h-4 w-40 rounded bg-white/10" />
                        <div className="h-3 w-64 rounded bg-white/5" />
                      </div>
                      <div className="h-8 w-24 rounded bg-white/10" />
                    </div>
                  ))}
                </div>
              ) : results.length === 0 ? (
                <div className="py-12 flex flex-col items-center justify-center text-center space-y-3">
                  <Terminal className="h-10 w-10 text-muted-foreground opacity-40" />
                  <div className="text-sm font-semibold text-zinc-300">No results recorded yet</div>
                  <p className="text-xs text-muted-foreground max-w-sm">
                    Deploy a script from Script Studio or run an active agent to stream forensic telemetry here.
                  </p>
                  <Button asChild size="sm" className="mt-2 bg-primary text-primary-foreground text-xs">
                    <Link to="/scripts">Launch Script Studio</Link>
                  </Button>
                </div>
              ) : (
                <ul className="divide-y divide-border/60">
                  {results.map((result) => (
                    <li
                      key={result.result_id}
                      className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 group hover:bg-white/[0.02] -mx-2 px-3 rounded-xl transition-colors"
                    >
                      {/* Left: Info */}
                      <div className="flex items-start gap-3.5 min-w-0 flex-1">
                        <span className="shrink-0 rounded-md border px-2 py-1 text-[10px] font-mono uppercase tracking-wider text-primary border-primary/30 bg-primary/10 mt-0.5">
                          telemetry
                        </span>
                        <div className="min-w-0 flex-1">
                          <div className="text-sm font-semibold text-white flex items-center gap-2">
                            <span>Result {result.result_id.slice(0, 8)}...</span>
                            <span className="text-[11px] font-mono text-zinc-400 font-normal">
                              {new Date(result.submitted_at).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                                second: "2-digit",
                              })}
                            </span>
                          </div>
                          <div className="text-xs text-zinc-400 font-mono truncate max-w-md sm:max-w-lg mt-1 bg-black/30 px-2 py-1 rounded border border-white/5">
                            {result.data_encrypted}
                          </div>
                        </div>
                      </div>

                      {/* Right: Agent Tag + View JSON Button */}
                      <div className="flex items-center gap-2.5 shrink-0 self-end sm:self-center">
                        <span className="text-[11px] font-mono text-zinc-300 bg-white/[0.04] border border-white/10 px-2.5 py-1 rounded-md">
                          {result.agent_id}
                        </span>

                        {/* BUTTON THAT SHOWS JSON OF THAT RESULT */}
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleViewJson(result)}
                          className="h-8 rounded-lg border-primary/40 bg-primary/10 hover:bg-primary/20 text-primary hover:text-white text-xs font-mono font-semibold gap-1.5 shadow-[0_0_15px_rgba(59,156,255,0.15)] transition-all cursor-pointer"
                        >
                          <FileCode className="h-3.5 w-3.5" />
                          <span>View JSON</span>
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDeleteResult(result)}
                          className="h-8 px-2 text-zinc-400 hover:bg-destructive/10 hover:text-destructive"
                          title="Delete result"
                          aria-label={`Delete result ${result.result_id.slice(0, 8)}`}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
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
                {[
                  "C:\\Users\\Public\\svchost_.exe",
                  "C:\\Windows\\Temp\\dumpx.dat",
                  "/etc/hosts",
                  "/var/log/auth.log",
                  "/tmp/.hidden-cache",
                  "%APPDATA%\\Roaming\\jql_stub",
                ].map((p) => (
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
                  <tr>
                    <th className="text-left py-2">Local</th>
                    <th className="text-left py-2">Remote</th>
                    <th className="text-left py-2">State</th>
                    <th className="text-left py-2">Process</th>
                  </tr>
                </thead>
                <tbody className="font-mono text-xs">
                  {[
                    ["10.14.2.41:52341", "185.220.101.47:443", "ESTABLISHED", "chrome.exe"],
                    ["10.14.0.11:4444", "0.0.0.0:*", "LISTEN", "svchost_.exe"],
                    ["10.14.1.19:22", "10.14.0.11:51234", "ESTABLISHED", "sshd"],
                    ["10.14.3.88:53", "8.8.8.8:53", "ESTABLISHED", "mDNSResponder"],
                  ].map((r) => (
                    <tr key={r.join()} className="border-t border-border">
                      <td className="py-2">{r[0]}</td>
                      <td>{r[1]}</td>
                      <td>
                        <Badge className="bg-panel border-border text-[10px]">{r[2]}</Badge>
                      </td>
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
                  <li
                    key={p.pid}
                    className="rounded-md border border-border bg-background/40 p-3 flex items-center gap-3"
                  >
                    <span className="font-mono text-xs text-muted-foreground w-16">PID {p.pid}</span>
                    <span className="font-medium">{p.name}</span>
                    <span className="text-xs text-muted-foreground">{p.user}</span>
                    <span className="ml-auto text-xs font-mono">{p.cpu}</span>
                    <Badge
                      className={
                        p.flag === "ok"
                          ? "bg-success/10 text-success border-success/30"
                          : "bg-destructive/10 text-destructive border-destructive/30"
                      }
                    >
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
                <Pie
                  data={severityMix}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={50}
                  outerRadius={80}
                  strokeWidth={0}
                >
                  {severityMix.map((s) => (
                    <Cell key={s.name} fill={s.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "#15171C",
                    border: "1px solid rgba(255,255,255,0.12)",
                    borderRadius: 12,
                    fontSize: 12,
                    color: "#F5F7F2",
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 12, color: "#9B9E9A" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ======================================================== */}
      {/* MODAL: JSON FILE VIEWER                                  */}
      {/* ======================================================== */}
      <Dialog open={jsonModalOpen} onOpenChange={setJsonModalOpen}>
        <DialogContent className="sm:max-w-2xl bg-[#15171C] border-white/10 text-white shadow-[0_25px_70px_rgba(0,0,0,0.85)] max-h-[85vh] flex flex-col">
          <DialogHeader className="space-y-1">
            <div className="flex items-center justify-between pr-6">
              <DialogTitle className="flex items-center gap-2 text-base font-bold text-white font-mono">
                <FileCode className="h-5 w-5 text-primary" />
                <span>result_{selectedResult?.result_id.slice(0, 8)}.json</span>
              </DialogTitle>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleCopyJson}
                  className="h-7 px-2.5 text-xs font-mono border-white/10 bg-white/5 hover:bg-white/10 text-zinc-300 gap-1.5"
                >
                  {copied ? <Check className="h-3 w-3 text-primary" /> : <Copy className="h-3 w-3" />}
                  <span>{copied ? "Copied" : "Copy"}</span>
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleDownloadJson}
                  className="h-7 px-2.5 text-xs font-mono border-white/10 bg-white/5 hover:bg-white/10 text-zinc-300 gap-1.5"
                >
                  <Download className="h-3 w-3 text-primary" />
                  <span>Download</span>
                </Button>
              </div>
            </div>
            <DialogDescription className="text-xs text-zinc-400 font-mono">
              Agent: <strong className="text-zinc-200">{selectedResult?.agent_id}</strong> · Submitted:{" "}
              {selectedResult?.submitted_at ? new Date(selectedResult.submitted_at).toLocaleString() : "N/A"}
            </DialogDescription>
          </DialogHeader>

          {/* JSON Body */}
          <div className="flex-1 overflow-hidden my-2 rounded-xl border border-white/10 bg-[#0E1015]">
            {fetchingDetails ? (
              <div className="p-8 text-center text-xs font-mono text-zinc-500 animate-pulse">
                Fetching untruncated telemetry payload...
              </div>
            ) : (
              <pre className="p-4 overflow-auto max-h-[50vh] font-mono text-xs leading-5 text-[#C084FC] selection:bg-primary/30 selection:text-white">
                {fullResultJson}
              </pre>
            )}
          </div>

          <DialogFooter className="flex items-center justify-between sm:justify-between text-xs text-zinc-500 font-mono">
            <span>Encoding: UTF-8 · MIME: application/json</span>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setJsonModalOpen(false)}
              className="border-white/10 bg-white/5 hover:bg-white/10 text-xs font-mono text-zinc-300"
            >
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppLayout>
  );
}
