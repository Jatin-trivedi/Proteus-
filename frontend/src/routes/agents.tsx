import { createFileRoute } from "@tanstack/react-router";
import { Bot, Wifi, Activity, WifiOff, Terminal, RefreshCw, Trash2, AlertTriangle, Loader2 } from "lucide-react";
import { AppLayout, StatusDot } from "@/components/app-layout";
import { MetricCard } from "@/components/metric-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiFetch, type Agent } from "@/lib/api";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

export const Route = createFileRoute("/agents")({
  head: () => ({
    meta: [
      { title: "Agents — Proteus" },
      { name: "description", content: "Manage deployed forensic agents across Windows, Linux, and macOS endpoints with live telemetry." },
      { property: "og:title", content: "Agent Fleet — Proteus" },
      { property: "og:description", content: "Stealth agents reporting in real time." },
    ],
  }),
  component: AgentsPage,
});

function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selected, setSelected] = useState<Agent>();
  const [filter, setFilter] = useState("");
  const [error, setError] = useState<string>();
  const [agentToDecommission, setAgentToDecommission] = useState<Agent | null>(null);
  const [isDecommissioning, setIsDecommissioning] = useState(false);

  const loadAgents = () => {
    setError(undefined);
    apiFetch<Agent[]>("/agent/list")
      .then((data) => {
        setAgents(data);
        setSelected((current) => data.find((agent) => agent.agent_id === current?.agent_id) ?? data[0]);
      })
      .catch((err: Error) => setError(err.message));
  };

  useEffect(() => { loadAgents(); }, []);

  const handleDecommissionAgent = async () => {
    if (!agentToDecommission) return;
    setIsDecommissioning(true);
    try {
      await apiFetch<{ status: string }>(`/agent/${agentToDecommission.agent_id}/decommission`, {
        method: "POST",
      });
      toast.success("Kill Switch Queued", {
        description: `${agentToDecommission.hostname || agentToDecommission.agent_id} will stop on its next heartbeat. The audit record was retained.`,
      });
      setAgents((prev) =>
        prev.map((agent) =>
          agent.agent_id === agentToDecommission.agent_id
            ? { ...agent, status: "decommissioning" }
            : agent,
        ),
      );
      setSelected((current) =>
        current?.agent_id === agentToDecommission.agent_id
          ? { ...current, status: "decommissioning" }
          : current,
      );
      setAgentToDecommission(null);
    } catch (err: unknown) {
      const message = err instanceof Error
        ? err.message
        : "An unexpected error occurred while decommissioning the agent.";
      toast.error("Failed to Queue Kill Switch", {
        description: message,
      });
    } finally {
      setIsDecommissioning(false);
    }
  };

  const filteredAgents = useMemo(() => {
    const query = filter.toLowerCase();
    return agents.filter((agent) =>
      [agent.agent_id, agent.hostname, agent.os, agent.ip].some((value) =>
        value?.toLowerCase().includes(query),
      ),
    );
  }, [agents, filter]);

  const count = (status: string) => agents.filter((agent) => agent.status === status).length;
  return (
    <AppLayout
      title="Agent Fleet"
      subtitle="Stealth endpoints reporting to the Proteus relay grid."
      actions={
        <Button onClick={loadAgents} variant="outline" className="border-border">
          <RefreshCw className="mr-2 h-4 w-4" /> Sync Fleet
        </Button>
      }
    >
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard title="Total" value={agents.length} icon={Bot} tone="cyber" />
        <MetricCard title="Online" value={count("online")} icon={Wifi} tone="success" />
        <MetricCard title="Executing" value={count("executing")} icon={Activity} tone="warning" />
        <MetricCard title="Offline" value={count("offline")} icon={WifiOff} tone="destructive" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <div className="panel p-0 xl:col-span-2 overflow-hidden">
          <div className="flex items-center gap-3 p-5 border-b border-border">
            <Input value={filter} onChange={(event) => setFilter(event.target.value)} placeholder="Filter hostname, IP, OS…" className="bg-background border-border max-w-xs" />
            <span className="ml-auto text-[11px] font-mono text-muted-foreground">
              {filteredAgents.length} agents
            </span>
          </div>
          {error && <div className="px-5 py-3 text-sm text-destructive">{error}</div>}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground bg-background/40">
                <tr>
                  <th className="text-left px-5 py-3">Agent</th>
                  <th className="text-left px-5 py-3">OS</th>
                  <th className="text-left px-5 py-3">IP</th>
                  <th className="text-left px-5 py-3">Status</th>
                  <th className="text-left px-5 py-3">Last Seen</th>
                  <th className="text-left px-5 py-3">Task</th>
                  <th className="text-right px-5 py-3">Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredAgents.map((a) => {
                  const active = selected?.agent_id === a.agent_id;
                  return (
                    <tr
                      key={a.agent_id}
                      onClick={() => setSelected(a)}
                      className={`border-t border-border cursor-pointer transition-colors ${active ? "bg-primary/5" : "hover:bg-panel/60"}`}
                    >
                      <td className="px-5 py-4">
                        <div className="font-medium text-foreground">{a.hostname ?? "Unknown host"}</div>
                        <div className="text-[11px] font-mono text-muted-foreground">{a.agent_id}</div>
                      </td>
                      <td className="px-5 py-4 text-muted-foreground">{a.os}</td>
                      <td className="px-5 py-4 font-mono text-xs text-muted-foreground">{a.ip}</td>
                      <td className="px-5 py-4">
                        <span className="inline-flex items-center gap-2 capitalize text-foreground">
                          <StatusDot status={a.status as "online" | "offline" | "executing" | "warning"} />
                          {a.status}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-muted-foreground">{a.last_seen ? new Date(a.last_seen).toLocaleString() : "Never"}</td>
                      <td className="px-5 py-4 text-muted-foreground truncate max-w-[16ch]">—</td>
                      <td className="px-5 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setAgentToDecommission(a)}
                          className="h-8 w-8 p-0 text-zinc-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                          title={`Decommission ${a.hostname || a.agent_id}`}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <aside className="panel p-6 space-y-6 self-start">
          <div>
            <div className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground">
              Selected Agent
            </div>
            <div className="text-xl font-bold mt-1">{selected?.hostname ?? "No agent selected"}</div>
            <div className="text-xs font-mono text-muted-foreground">{selected?.agent_id ?? "—"} · {selected?.ip ?? "—"}</div>
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="rounded-md border border-border p-3">
              <div className="text-muted-foreground">Operating System</div>
              <div className="mt-1 font-medium text-foreground">{selected?.os ?? "—"}</div>
            </div>
            <div className="rounded-md border border-border p-3">
              <div className="text-muted-foreground">Status</div>
              <div className="mt-1 flex items-center gap-2 capitalize">
                <StatusDot status={selected?.status === "executing" || selected?.status === "warning" || selected?.status === "offline" ? selected.status : "online"} />
                {selected?.status ?? "—"}
              </div>
            </div>
            <div className="rounded-md border border-border p-3">
              <div className="text-muted-foreground">Uptime</div>
              <div className="mt-1 font-mono text-foreground">18d 04h</div>
            </div>
            <div className="rounded-md border border-border p-3">
              <div className="text-muted-foreground">Kernel</div>
              <div className="mt-1 font-mono text-foreground">6.1.104</div>
            </div>
          </div>

          {selected && (
            <div className="pt-1">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAgentToDecommission(selected)}
                className="w-full border-red-500/30 text-red-400 hover:text-white hover:bg-red-500/20 hover:border-red-500/60 text-xs font-semibold uppercase tracking-wider h-9 transition-all flex items-center justify-center gap-2 rounded-lg"
              >
                <Trash2 className="h-3.5 w-3.5" /> Decommission Agent
              </Button>
            </div>
          )}

          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-foreground mb-2">
              <Terminal className="h-3.5 w-3.5 text-primary" /> Live Activity
            </div>
            <div className="rounded-md border border-border bg-background/60 p-3 font-mono text-[11px] leading-relaxed text-muted-foreground max-h-52 overflow-auto">
              <div><span className="text-primary">›</span> beacon.check_in()  <span className="text-success">ok</span></div>
              <div><span className="text-primary">›</span> polymorph.rehash() <span className="text-primary">a7f4c9 → 9e1b3d</span></div>
              <div><span className="text-primary">›</span> memscan.enum_procs() <span className="text-success">142 pids</span></div>
              <div><span className="text-primary">›</span> registry.diff(HKCU\\Run) <span className="text-warning">1 delta</span></div>
              <div><span className="text-primary">›</span> netstat.snapshot() <span className="text-success">ok</span></div>
              <div><span className="text-primary">›</span> exfil.stage(chunk=32k) <span className="text-success">queued</span></div>
              <div><span className="text-primary">›</span> heartbeat 1000ms <span className="text-success">stable</span></div>
            </div>
          </div>
        </aside>
      </div>

      {/* Decommission Confirmation Dialog */}
      <Dialog open={!!agentToDecommission} onOpenChange={(open) => !open && setAgentToDecommission(null)}>
        <DialogContent className="sm:max-w-md bg-panel border-border text-foreground">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg font-bold text-red-400">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              Decommission Forensic Agent
            </DialogTitle>
            <DialogDescription className="text-muted-foreground text-xs leading-relaxed">
              Are you sure you want to stop this agent on its target and mark it as decommissioning?
            </DialogDescription>
          </DialogHeader>

          {agentToDecommission && (
            <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-3.5 my-2 space-y-1.5 font-mono text-xs">
              <div className="flex justify-between text-zinc-300">
                <span className="text-muted-foreground">Hostname:</span>
                <span className="font-semibold text-white">{agentToDecommission.hostname || "Unknown"}</span>
              </div>
              <div className="flex justify-between text-zinc-300">
                <span className="text-muted-foreground">Agent ID:</span>
                <span className="text-zinc-200">{agentToDecommission.agent_id}</span>
              </div>
              <div className="flex justify-between text-zinc-300">
                <span className="text-muted-foreground">IP Address:</span>
                <span className="text-zinc-200">{agentToDecommission.ip}</span>
              </div>
            </div>
          )}

          <p className="text-[11px] text-zinc-400">
            The kill switch will be delivered on the target's next heartbeat. The local agent record and deployment audit entry will be retained.
          </p>

          <DialogFooter className="gap-2 sm:gap-0 mt-3">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={isDecommissioning}
              onClick={() => setAgentToDecommission(null)}
              className="border-border text-xs"
            >
              Cancel
            </Button>
            <Button
              type="button"
              size="sm"
              disabled={isDecommissioning}
              onClick={handleDecommissionAgent}
              className="bg-red-600 hover:bg-red-700 text-white font-semibold text-xs tracking-wider uppercase ml-2 flex items-center gap-1.5 shadow-[0_0_15px_rgba(239,68,68,0.3)]"
            >
              {isDecommissioning ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Queueing Kill Switch...
                </>
              ) : (
                <>
                  <Trash2 className="h-3.5 w-3.5" />
                  Queue Kill Switch
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppLayout>
  );
}
