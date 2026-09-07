import { createFileRoute } from "@tanstack/react-router";
import { FilePlus2, Play, Save, Layers } from "lucide-react";
import { AppLayout } from "@/components/app-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { apiFetch, type Agent, type Script } from "@/lib/api";
import { useEffect, useState } from "react";
import { toast } from "sonner";

export const Route = createFileRoute("/scripts")({
  head: () => ({
    meta: [
      { title: "Scripts — JOCKY Labs" },
      { name: "description", content: "Author polymorphic forensic scripts and target agent fleets with the JOCKY editor." },
      { property: "og:title", content: "Script Library — JOCKY Labs" },
      { property: "og:description", content: "Build. Polymorph. Deploy." },
    ],
  }),
  component: ScriptsPage,
});

const DEFAULT_CODE = `# JQL — JOCKY Query Language
target: hosts where os == "windows"
stealth: on
polymorph: aes-256, xor-rot, dead-code-inject

scan memory {
  enum processes
  dump lsass if suspicious
  hash executables
}

scan registry {
  path HKCU\\\\Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Run
  diff since last_run
}

report -> relay.encrypted()
`;

function highlight(code: string) {
  return code
    .replace(/(#.*)$/gm, '<span style="color:oklch(0.72 0.03 255)">$1</span>')
    .replace(/\b(target|stealth|polymorph|scan|report|enum|dump|hash|path|diff|since|if)\b/g, '<span style="color:oklch(0.85 0.16 220)">$1</span>')
    .replace(/\b(on|off|windows|linux|macos)\b/g, '<span style="color:oklch(0.78 0.16 75)">$1</span>')
    .replace(/(".*?")/g, '<span style="color:oklch(0.72 0.17 155)">$1</span>');
}

function ScriptsPage() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [progress, setProgress] = useState(0);
  const [deploying, setDeploying] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [scripts, setScripts] = useState<Script[]>([]);
  const [scriptName, setScriptName] = useState("Memory Sweep v3.2");

  const toggle = (id: string) =>
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  useEffect(() => {
    apiFetch<Agent[]>("/agent/list").then((data) => {
      setAgents(data);
      setSelected(data.slice(0, 2).map((agent) => agent.agent_id));
    }).catch((error: Error) => toast.error(error.message));
  }, []);

  useEffect(() => {
    apiFetch<Script[]>("/script/list")
      .then(setScripts)
      .catch((error: Error) => toast.error(error.message));
  }, []);

  const deploy = async () => {
    if (deploying) return;
    setDeploying(true);
    setProgress(0);
    try {
      await apiFetch("/script/deploy", {
        method: "POST",
        body: JSON.stringify({ name: scriptName, agent_ids: selected, code }),
      });
      setProgress(100);
      toast.success(`Deployed to ${selected.length} agents.`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Deployment failed");
    } finally {
      setDeploying(false);
    }
  };

  return (
    <AppLayout
      title="Script Library"
      subtitle="Compose forensic queries in JQL — every deploy is uniquely polymorphed."
      actions={
        <>
          <Button variant="outline" className="border-border"><Save className="mr-2 h-4 w-4" />Save Draft</Button>
          <Button className="bg-primary text-primary-foreground hover:bg-primary/90 glow-cyber">
            <FilePlus2 className="mr-2 h-4 w-4" /> Create New Script
          </Button>
        </>
      }
    >
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-8">
        <div className="space-y-8">
          <div className="panel overflow-hidden">
            <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-primary" />
                <span className="text-sm font-semibold">memory_sweep.jql</span>
                <Badge className="bg-primary/10 text-primary border-primary/30 ml-2">JQL</Badge>
              </div>
              <span className="text-[11px] font-mono text-muted-foreground">
                Hash · <span className="text-primary">a7f4c9d1</span>
              </span>
            </div>
            <div className="relative font-mono text-[13px] leading-6">
              <pre
                aria-hidden
                className="pointer-events-none absolute inset-0 whitespace-pre-wrap break-words p-5 text-foreground"
                dangerouslySetInnerHTML={{ __html: highlight(code) + "\n" }}
              />
              <Textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                spellCheck={false}
                className="relative min-h-[340px] w-full resize-y bg-transparent border-0 rounded-none p-5 font-mono text-[13px] leading-6 text-transparent caret-primary focus-visible:ring-0"
              />
            </div>
          </div>

          <div className="panel p-6">
            <div className="grid md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Script Name</Label>
                <Input value={scriptName} onChange={(event) => setScriptName(event.target.value)} className="bg-background border-border" />
              </div>
              <div className="space-y-2">
                <Label>Category</Label>
                <Input defaultValue="Memory · Persistence" className="bg-background border-border" />
              </div>
              <div className="md:col-span-2 space-y-2">
                <Label>Description</Label>
                <Textarea
                  defaultValue="Enumerates running processes, hashes executables, and dumps LSASS if suspicious tokens are detected."
                  className="bg-background border-border"
                />
              </div>
            </div>

            <div className="mt-6">
              <div className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground mb-2">
                Target Agents ({selected.length} selected)
              </div>
              <div className="grid sm:grid-cols-2 gap-2">
                {agents.map((a) => (
                  <label
                    key={a.id}
                    className="flex items-center gap-3 rounded-md border border-border bg-background/40 p-3 cursor-pointer hover:border-primary/40"
                  >
                    <Checkbox
                      checked={selected.includes(a.id)}
                      onCheckedChange={() => toggle(a.id)}
                    />
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium truncate">{a.hostname ?? "Unknown host"}</div>
                      <div className="text-[11px] font-mono text-muted-foreground truncate">{a.agent_id} · {a.os}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Deployment panel */}
          <div className="panel p-6 flex flex-col md:flex-row md:items-center gap-4">
            <div className="min-w-0 flex-1">
              <div className="text-sm font-semibold text-foreground">Ready to deploy</div>
              <div className="text-xs text-muted-foreground">
                {selected.length} targets · polymorphic hash rotates per host
              </div>
              {(deploying || progress === 100) && (
                <div className="mt-3">
                  <Progress value={progress} className="h-1.5" />
                  <div className="mt-1 text-[11px] font-mono text-muted-foreground">
                    {deploying ? `Injecting… ${progress}%` : `Delivered · ${selected.length}/${selected.length}`}
                  </div>
                </div>
              )}
            </div>
            <Button
              onClick={deploy}
              disabled={deploying || selected.length === 0}
              className="bg-primary text-primary-foreground hover:bg-primary/90 glow-cyber min-w-[160px]"
            >
              <Play className="mr-2 h-4 w-4" />
              {deploying ? "Deploying…" : "Deploy Script"}
            </Button>
          </div>
        </div>

        <aside className="panel p-6 self-start">
          <div className="mb-3">
            <div className="text-sm font-semibold">Template Library</div>
            <div className="text-xs text-muted-foreground">Battle-tested starting points</div>
          </div>
          <ul className="space-y-2">
            {scripts.map((script) => (
              <li key={script.script_id}>
                <button className="w-full text-left rounded-md border border-border bg-background/40 p-3 hover:border-primary/40 hover:bg-primary/5 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium">{script.name}</div>
                    <Badge className="bg-panel border-border text-[10px] font-mono uppercase">JQL</Badge>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">Created {new Date(script.created_at).toLocaleString()}</div>
                </button>
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </AppLayout>
  );
}
