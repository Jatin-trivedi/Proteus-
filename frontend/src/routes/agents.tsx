import { createFileRoute } from "@tanstack/react-router";
import { Bot, Wifi, Activity, WifiOff, Terminal, RefreshCw } from "lucide-react";
import { AppLayout, StatusDot } from "@/components/app-layout";
import { MetricCard } from "@/components/metric-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiFetch, type Agent } from "@/lib/api";
import { useEffect, useMemo, useState } from "react";

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
    </AppLayout>
  );
}
