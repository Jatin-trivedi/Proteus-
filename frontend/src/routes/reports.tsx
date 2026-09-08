import { createFileRoute } from "@tanstack/react-router";
import { FileDown, FileSpreadsheet, FileText, Download } from "lucide-react";
import { AppLayout } from "@/components/app-layout";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { apiFetch, type Result } from "@/lib/api";
import { useEffect, useState } from "react";
import { toast } from "sonner";

export const Route = createFileRoute("/reports")({
  head: () => ({
    meta: [
      { title: "Reports — Proteus" },
      { name: "description", content: "Generate audit-grade forensic investigation reports for legal, compliance, and incident response teams." },
      { property: "og:title", content: "Reports — Proteus" },
      { property: "og:description", content: "Court-ready forensic reporting." },
    ],
  }),
  component: ReportsPage,
});

const SECTIONS = ["Registry", "File System", "Network", "Process", "Memory", "Chain of Custody"];

function ReportsPage() {
  const [results, setResults] = useState<Result[]>([]);

  useEffect(() => {
    apiFetch<Result[]>("/result/list")
      .then(setResults)
      .catch((error: Error) => toast.error(error.message));
  }, []);

  return (
    <AppLayout
      title="Reports"
      subtitle="Compose, preview, and export forensic reports for stakeholders and courts."
    >
      <div className="grid grid-cols-1 xl:grid-cols-[380px_1fr] gap-8">
        <div className="panel p-6 space-y-5 self-start">
          <div className="space-y-3">
            <Label className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground">Report Type</Label>
            <RadioGroup defaultValue="full" className="space-y-2">
              {[
                { v: "full", t: "Full Forensic Report", d: "All sections, evidence-grade" },
                { v: "exec", t: "Executive Summary", d: "Findings and recommendations" },
                { v: "incident", t: "Incident Timeline", d: "Chronological reconstruction" },
              ].map((o) => (
                <label key={o.v} className="flex items-start gap-3 rounded-md border border-border p-3 cursor-pointer hover:border-primary/40">
                  <RadioGroupItem value={o.v} />
                  <div>
                    <div className="text-sm font-medium">{o.t}</div>
                    <div className="text-xs text-muted-foreground">{o.d}</div>
                  </div>
                </label>
              ))}
            </RadioGroup>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>From</Label>
              <Input type="date" defaultValue="2026-08-01" className="bg-background border-border" />
            </div>
            <div className="space-y-2">
              <Label>To</Label>
              <Input type="date" defaultValue="2026-09-07" className="bg-background border-border" />
            </div>
          </div>

          <div className="space-y-2">
            <Label className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground">Include Sections</Label>
            <div className="grid grid-cols-2 gap-2">
              {SECTIONS.map((s) => (
                <label key={s} className="flex items-center gap-2 text-sm">
                  <Checkbox defaultChecked />{s}
                </label>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-2 pt-2">
            <Button
              onClick={() => toast.success("Report queued · RPT-0143")}
              className="bg-primary text-primary-foreground hover:bg-primary/90 glow-cyber"
            >
              <FileText className="mr-2 h-4 w-4" /> Generate Report
            </Button>
            <div className="grid grid-cols-2 gap-2">
              <Button variant="outline" className="border-border"><FileDown className="mr-2 h-4 w-4" />PDF</Button>
              <Button variant="outline" className="border-border"><FileSpreadsheet className="mr-2 h-4 w-4" />CSV</Button>
            </div>
          </div>
        </div>

        <div className="space-y-8">
          <div className="panel p-6">
            <div className="flex items-center justify-between border-b border-border pb-4 mb-4">
              <div>
                <div className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground">Preview</div>
                <h2 className="text-xl font-bold">Q3 Forensic Digest — Draft</h2>
              </div>
              <div className="text-right text-[11px] font-mono text-muted-foreground">
                Case · <span className="text-foreground">JOCKY-24-118</span><br />
                Prepared · 2026-09-07
              </div>
            </div>
            <article className="prose prose-invert max-w-none text-sm text-muted-foreground space-y-3">
              <p>
                The backend currently contains <span className="text-foreground font-medium">{results.length} submitted results</span> across
                <span className="text-foreground font-medium"> {new Set(results.map((result) => result.agent_id)).size} agents</span> and
                <span className="text-foreground font-medium"> {new Set(results.map((result) => result.script_id)).size} scripts</span>.
              </p>
              <h3 className="text-foreground font-semibold mt-4">Key Findings</h3>
              <ul className="list-disc pl-5 space-y-1">
                <li>Unsigned <code className="text-primary">svchost_.exe</code> on AGT-002 spawned from <code>%TEMP%</code> with SYSTEM handle to LSASS.</li>
                <li>Persistent HTTPS beacon (7s jitter) to <code>185.220.101.47</code> across three subnets.</li>
                <li>Registry autorun modified outside change-management window on AGT-007.</li>
              </ul>
              <h3 className="text-foreground font-semibold mt-4">Chain of Custody</h3>
              <p>All artifacts hashed on capture (SHA-256), relay-signed, and mirrored to immutable evidence vault EV-04.</p>
            </article>
          </div>

          <div className="panel p-6">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold">Report History</h3>
                <p className="text-xs text-muted-foreground">Previously generated reports</p>
              </div>
            </div>
            <ul className="divide-y divide-border">
              {results.map((result) => (
                <li key={result.result_id} className="py-4 flex items-center gap-3">
                  <div className="grid h-9 w-9 place-items-center rounded-md bg-primary/10 border border-primary/25">
                    <FileText className="h-4 w-4 text-primary" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium truncate">Result {result.result_id}</div>
                    <div className="text-[11px] font-mono text-muted-foreground truncate">
                      Agent {result.agent_id} · Script {result.script_id} · {new Date(result.submitted_at).toLocaleString()}
                    </div>
                  </div>
                  <Button size="sm" variant="outline" className="border-border">
                    <Download className="mr-2 h-3.5 w-3.5" />Download
                  </Button>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
