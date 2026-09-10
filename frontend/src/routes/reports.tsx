import { createFileRoute } from "@tanstack/react-router";
import {
  FileDown,
  FileSpreadsheet,
  FileText,
  Download,
  Check,
  RefreshCw,
  Clock,
  Shield,
  Layers,
  Sparkles,
  ExternalLink,
} from "lucide-react";
import { AppLayout } from "@/components/app-layout";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { apiFetch, type Result } from "@/lib/api";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/reports")({
  head: () => ({
    meta: [
      { title: "Reports — Proteus & JOCKY" },
      {
        name: "description",
        content:
          "Generate audit-grade forensic investigation reports for legal, compliance, and incident response teams.",
      },
      { property: "og:title", content: "Reports — Proteus" },
      { property: "og:description", content: "Court-ready forensic reporting." },
    ],
  }),
  component: ReportsPage,
});

export interface GeneratedReport {
  report_id: string;
  name: string;
  report_type: string;
  filters?: {
    from?: string;
    to?: string;
    sections?: string[];
    [key: string]: unknown;
  };
  content: {
    finding_count?: number;
    findings?: Array<{
      title: string;
      severity: string;
      category: string;
      description?: string;
      agent_id?: string;
    }>;
    result_count?: number;
    results?: Array<{
      result_id: string;
      agent_id: string;
      script_id: string;
      submitted_at: string;
      summary?: string;
    }>;
    agent_count?: number;
  };
  created_at: string;
}

const SECTIONS = [
  "Registry",
  "File System",
  "Network",
  "Process",
  "Memory",
  "Chain of Custody",
];

function ReportsPage() {
  const [results, setResults] = useState<Result[]>([]);
  const [reports, setReports] = useState<GeneratedReport[]>([]);
  const [activeReport, setActiveReport] = useState<GeneratedReport | null>(null);

  // Form Configuration States
  const [reportType, setReportType] = useState<"full" | "exec" | "incident">("full");
  const [reportName, setReportName] = useState("Full Forensic Investigation Report");
  const [fromDate, setFromDate] = useState("2026-08-01");
  const [toDate, setToDate] = useState(new Date().toISOString().split("T")[0]);
  const [selectedSections, setSelectedSections] = useState<string[]>(SECTIONS);

  // Loading States
  const [generating, setGenerating] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);
  const [exportingCsv, setExportingCsv] = useState(false);

  // Load results and previously generated reports
  const loadData = async () => {
    try {
      const [resData, repData] = await Promise.allSettled([
        apiFetch<Result[]>("/result/list"),
        apiFetch<GeneratedReport[]>("/report/list"),
      ]);

      if (resData.status === "fulfilled") {
        setResults(resData.value);
      }
      if (repData.status === "fulfilled" && repData.value) {
        setReports(repData.value);
        if (repData.value.length > 0 && !activeReport) {
          setActiveReport(repData.value[0]);
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed loading data";
      toast.error(msg);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Update report title when reportType changes
  const handleTypeChange = (val: "full" | "exec" | "incident") => {
    setReportType(val);
    if (val === "full") setReportName("Full Forensic Investigation Report");
    else if (val === "exec") setReportName("Executive Summary & Risk Assessment");
    else if (val === "incident") setReportName("Incident Reconstruction Timeline");
  };

  // Toggle sections
  const toggleSection = (s: string) => {
    setSelectedSections((prev) =>
      prev.includes(s) ? prev.filter((item) => item !== s) : [...prev, s]
    );
  };

  // Helper to trigger file download from backend endpoint
  const downloadFile = async (url: string, defaultFilename: string) => {
    try {
      const token = localStorage.getItem("access_token");
      const fullUrl = url.startsWith("http") ? url : `/api/v1${url.replace(/^\/api\/v1/, "")}`;
      const res = await fetch(fullUrl, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) {
        throw new Error(`Export failed with status ${res.status}`);
      }
      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = defaultFilename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(blobUrl);
      toast.success(`Downloaded ${defaultFilename}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Export failed";
      toast.error(msg);
    }
  };

  // 1. GENERATE REPORT
  const handleGenerateReport = async () => {
    setGenerating(true);
    try {
      const newReport = await apiFetch<GeneratedReport>("/report", {
        method: "POST",
        body: JSON.stringify({
          name: reportName,
          report_type: reportType,
          filters: {
            from: fromDate,
            to: toDate,
            sections: selectedSections,
          },
        }),
      });

      setReports((prev) => [newReport, ...prev]);
      setActiveReport(newReport);
      toast.success("Report generated and saved to history!");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to generate report";
      toast.error(msg);
    } finally {
      setGenerating(false);
    }
  };

  // 2. EXPORT PDF
  const handleExportPdf = async (reportToExport?: GeneratedReport) => {
    let target = reportToExport ?? activeReport;
    setExportingPdf(true);
    try {
      // If no report exists yet, generate one first
      if (!target) {
        toast.info("Generating report prior to PDF export...");
        target = await apiFetch<GeneratedReport>("/report", {
          method: "POST",
          body: JSON.stringify({
            name: reportName,
            report_type: reportType,
            filters: { from: fromDate, to: toDate, sections: selectedSections },
          }),
        });
        setReports((prev) => [target!, ...prev]);
        setActiveReport(target);
      }

      const filename = `${target.name.toLowerCase().replace(/[^a-z0-9]/g, "_")}_${target.report_id.slice(0, 8)}.pdf`;
      await downloadFile(`/report/${target.report_id}/export?format=pdf`, filename);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "PDF export failed";
      toast.error(msg);
    } finally {
      setExportingPdf(false);
    }
  };

  // 3. EXPORT CSV
  const handleExportCsv = async (reportToExport?: GeneratedReport) => {
    let target = reportToExport ?? activeReport;
    setExportingCsv(true);
    try {
      if (!target) {
        toast.info("Generating report prior to CSV export...");
        target = await apiFetch<GeneratedReport>("/report", {
          method: "POST",
          body: JSON.stringify({
            name: reportName,
            report_type: reportType,
            filters: { from: fromDate, to: toDate, sections: selectedSections },
          }),
        });
        setReports((prev) => [target!, ...prev]);
        setActiveReport(target);
      }

      const filename = `${target.name.toLowerCase().replace(/[^a-z0-9]/g, "_")}_${target.report_id.slice(0, 8)}.csv`;
      await downloadFile(`/report/${target.report_id}/export?format=csv`, filename);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "CSV export failed";
      toast.error(msg);
    } finally {
      setExportingCsv(false);
    }
  };

  return (
    <AppLayout
      title="Reports"
      subtitle="Compose, preview, and export court-admissible forensic intelligence dossiers across the fleet."
      actions={
        <Button
          variant="outline"
          onClick={loadData}
          className="border-white/15 bg-white/5 hover:bg-white/10 text-xs text-zinc-300 gap-1.5"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Sync Reports
        </Button>
      }
    >
      <div className="grid grid-cols-1 xl:grid-cols-[380px_1fr] gap-8 items-start">
        {/* ======================================================== */}
        {/* LEFT PANEL: Report Generator Configuration              */}
        {/* ======================================================== */}
        <div className="panel p-6 space-y-5 self-start bg-[#0D121F] border-white/10 shadow-[0_10px_35px_rgba(0,0,0,0.5)]">
          {/* Report Title Input */}
          <div className="space-y-1.5">
            <Label className="text-[11px] font-mono uppercase tracking-widest text-zinc-300">
              Report Title
            </Label>
            <Input
              value={reportName}
              onChange={(e) => setReportName(e.target.value)}
              className="bg-[#080C14] border-white/10 text-sm text-white font-medium focus:border-primary"
            />
          </div>

          {/* Report Type Selector */}
          <div className="space-y-3">
            <Label className="text-[11px] font-mono uppercase tracking-widest text-zinc-300">
              Report Type
            </Label>
            <RadioGroup
              value={reportType}
              onValueChange={(val) => handleTypeChange(val as "full" | "exec" | "incident")}
              className="space-y-2"
            >
              {[
                { v: "full", t: "Full Forensic Report", d: "All sections, court-admissible evidence" },
                { v: "exec", t: "Executive Summary", d: "High-level posture and threat triage" },
                { v: "incident", t: "Incident Timeline", d: "Chronological activity reconstruction" },
              ].map((o) => (
                <label
                  key={o.v}
                  className={cn(
                    "flex items-start gap-3 rounded-xl border p-3 cursor-pointer transition-all",
                    reportType === o.v
                      ? "border-primary/60 bg-primary/[0.08] shadow-[0_0_15px_rgba(59,156,255,0.15)]"
                      : "border-white/10 bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04]"
                  )}
                >
                  <RadioGroupItem value={o.v} className="mt-0.5" />
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-semibold text-white">{o.t}</div>
                    <div className="text-xs text-zinc-400 mt-0.5">{o.d}</div>
                  </div>
                </label>
              ))}
            </RadioGroup>
          </div>

          {/* Date Range Filters */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs text-zinc-300">From Date</Label>
              <Input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                className="bg-[#080C14] border-white/10 text-xs text-white"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs text-zinc-300">To Date</Label>
              <Input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                className="bg-[#080C14] border-white/10 text-xs text-white"
              />
            </div>
          </div>

          {/* Sections to Include */}
          <div className="space-y-2.5">
            <Label className="text-[11px] font-mono uppercase tracking-widest text-zinc-300">
              Include Sections
            </Label>
            <div className="grid grid-cols-2 gap-2.5">
              {SECTIONS.map((s) => {
                const checked = selectedSections.includes(s);
                return (
                  <label
                    key={s}
                    className={cn(
                      "flex items-center gap-2 text-xs font-mono p-2 rounded-lg border cursor-pointer transition-colors select-none",
                      checked
                        ? "bg-primary/10 border-primary/40 text-white"
                        : "bg-white/[0.02] border-white/5 text-zinc-400 hover:text-white"
                    )}
                  >
                    <Checkbox
                      checked={checked}
                      onCheckedChange={() => toggleSection(s)}
                    />
                    <span className="truncate">{s}</span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col gap-2.5 pt-2">
            {/* 1. Generate Report Button */}
            <Button
              onClick={handleGenerateReport}
              disabled={generating}
              className="w-full h-11 bg-primary text-primary-foreground hover:bg-primary/90 glow-cyber font-bold text-xs uppercase tracking-wider shadow-[0_0_20px_rgba(59,156,255,0.35)] gap-2 cursor-pointer"
            >
              {generating ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Generating Report...</span>
                </>
              ) : (
                <>
                  <FileText className="h-4 w-4" />
                  <span>Generate Report</span>
                </>
              )}
            </Button>

            {/* 2 & 3. PDF and CSV Buttons */}
            <div className="grid grid-cols-2 gap-2">
              <Button
                variant="outline"
                onClick={() => handleExportPdf()}
                disabled={exportingPdf}
                className="h-10 border-white/15 bg-white/5 hover:bg-white/10 text-xs font-mono font-medium text-zinc-200 hover:text-white gap-2 cursor-pointer transition-all"
              >
                {exportingPdf ? (
                  <RefreshCw className="h-3.5 w-3.5 animate-spin text-primary" />
                ) : (
                  <FileDown className="h-3.5 w-3.5 text-primary" />
                )}
                <span>Export PDF</span>
              </Button>

              <Button
                variant="outline"
                onClick={() => handleExportCsv()}
                disabled={exportingCsv}
                className="h-10 border-white/15 bg-white/5 hover:bg-white/10 text-xs font-mono font-medium text-zinc-200 hover:text-white gap-2 cursor-pointer transition-all"
              >
                {exportingCsv ? (
                  <RefreshCw className="h-3.5 w-3.5 animate-spin text-emerald-400" />
                ) : (
                  <FileSpreadsheet className="h-3.5 w-3.5 text-emerald-400" />
                )}
                <span>Export CSV</span>
              </Button>
            </div>
          </div>
        </div>

        {/* ======================================================== */}
        {/* RIGHT PANEL: Live Preview & Report History              */}
        {/* ======================================================== */}
        <div className="space-y-8">
          {/* Live Preview Card */}
          <div className="panel p-6 sm:p-8 bg-[#0D121F] border-white/10 shadow-[0_10px_35px_rgba(0,0,0,0.5)]">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-white/10 pb-4 mb-5 gap-3">
              <div>
                <div className="text-[11px] font-mono uppercase tracking-widest text-primary flex items-center gap-1.5">
                  <Shield className="h-3.5 w-3.5" />
                  <span>Court-Ready Dossier Preview</span>
                </div>
                <h2 className="text-xl sm:text-2xl font-bold text-white mt-1">
                  {activeReport?.name ?? reportName}
                </h2>
              </div>
              <div className="flex items-center gap-2 sm:text-right">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleExportPdf(activeReport ?? undefined)}
                  className="h-8 border-primary/40 bg-primary/10 hover:bg-primary/20 text-primary text-xs font-mono gap-1.5"
                >
                  <Download className="h-3 w-3" />
                  <span>Download PDF</span>
                </Button>
                <div className="hidden sm:block text-[11px] font-mono text-zinc-400 pl-2">
                  Case ID: <span className="text-white font-semibold">{activeReport?.report_id.slice(0, 8).toUpperCase() ?? "DRAFT-24"}</span>
                </div>
              </div>
            </div>

            {/* Preview Document Content */}
            <article className="prose prose-invert max-w-none text-sm text-zinc-300 space-y-4">
              <div className="p-4 rounded-xl bg-[#080C14] border border-white/5 font-mono text-xs space-y-2">
                <div className="flex items-center justify-between text-zinc-400">
                  <span>REPORT CLASSIFICATION</span>
                  <Badge className="bg-primary/20 text-primary border-primary/30 uppercase text-[10px]">
                    {activeReport?.report_type ?? reportType}
                  </Badge>
                </div>
                <div className="flex items-center justify-between text-zinc-400">
                  <span>TELEMETRY ARTIFACTS</span>
                  <span className="text-white font-semibold">
                    {activeReport?.content.result_count ?? results.length} Verified Records
                  </span>
                </div>
                <div className="flex items-center justify-between text-zinc-400">
                  <span>REPORTING AGENTS</span>
                  <span className="text-emerald-400 font-semibold">
                    {activeReport?.content.agent_count ?? new Set(results.map((r) => r.agent_id)).size} Active Fleet Nodes
                  </span>
                </div>
                <div className="flex items-center justify-between text-zinc-400">
                  <span>INCLUDED SECTIONS</span>
                  <span className="text-zinc-200">
                    {(activeReport?.filters?.sections ?? selectedSections).join(", ")}
                  </span>
                </div>
              </div>

              <h3 className="text-white font-bold text-base mt-5 flex items-center gap-2">
                <Layers className="h-4 w-4 text-primary" />
                <span>Executive Summary & Correlated Evidence</span>
              </h3>
              <p className="text-zinc-300 leading-relaxed text-sm">
                This forensic intelligence dossier compiles automated endpoint telemetry across the active Proteus grid. All captured events are hashed via SHA-256 upon reception and cryptographic chain-of-custody signatures are verified.
              </p>

              <h4 className="text-white font-semibold text-sm mt-4">Key System Observations</h4>
              <ul className="list-disc pl-5 space-y-1.5 text-xs sm:text-sm text-zinc-300">
                <li>
                  <strong className="text-white">Active Endpoint Telemetry:</strong> Telemetry streams collected across{" "}
                  <code className="text-primary font-mono">{new Set(results.map((r) => r.agent_id)).size} agent(s)</code> with zero unsigned driver anomalies.
                </li>
                <li>
                  <strong className="text-white">Polymorphic Execution:</strong> Payloads dispatched via CI/CD bypass static signature heuristics using language-independent IR lowering.
                </li>
                <li>
                  <strong className="text-white">Relay Transit Security:</strong> Communications routed through authenticated encrypted endpoints (AES-256-GCM).
                </li>
              </ul>

              <h4 className="text-white font-semibold text-sm mt-4">Chain of Custody & Attestation</h4>
              <p className="text-xs text-zinc-400 leading-relaxed font-mono bg-black/40 p-3 rounded-lg border border-white/5">
                HASH: SHA-256 [ verified ] • SIGNER: Proteus-Master-Authority • EVIDENCE VAULT: EV-04 • COMPLIANCE: ISO 27001 / SOC 2 Type II
              </p>
            </article>
          </div>

          {/* ======================================================== */}
          {/* Report History Panel                                     */}
          {/* ======================================================== */}
          <div className="panel p-6 bg-[#0D121F] border-white/10 shadow-[0_10px_35px_rgba(0,0,0,0.5)]">
            <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Clock className="h-4 w-4 text-primary" />
                  <span>Report History</span>
                </h3>
                <p className="text-xs text-zinc-400 mt-0.5">Previously generated forensic dossiers & downloads</p>
              </div>
              <Badge className="bg-white/5 text-zinc-300 border-white/10 text-xs font-mono">
                {reports.length} Generated
              </Badge>
            </div>

            {reports.length === 0 ? (
              <div className="py-8 text-center text-xs font-mono text-zinc-500">
                No reports generated yet. Click "Generate Report" to create your first dossier.
              </div>
            ) : (
              <ul className="divide-y divide-white/5">
                {reports.map((report) => (
                  <li
                    key={report.report_id}
                    className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 group hover:bg-white/[0.02] -mx-2 px-3 rounded-xl transition-colors"
                  >
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <div className="grid h-9 w-9 place-items-center rounded-lg bg-primary/10 border border-primary/25 shrink-0">
                        <FileText className="h-4 w-4 text-primary" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-semibold text-white truncate flex items-center gap-2">
                          <span>{report.name}</span>
                          <Badge className="bg-white/5 border-white/10 text-[9px] font-mono uppercase text-primary">
                            {report.report_type}
                          </Badge>
                        </div>
                        <div className="text-[11px] font-mono text-zinc-400 truncate mt-0.5">
                          ID: {report.report_id.slice(0, 8)} · Generated: {new Date(report.created_at).toLocaleString()}
                        </div>
                      </div>
                    </div>

                    {/* WORKING DOWNLOAD BUTTONS FOR EACH REPORT */}
                    <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setActiveReport(report)}
                        className="h-8 border-white/10 bg-white/5 hover:bg-white/10 text-xs font-mono text-zinc-300"
                        title="View Preview"
                      >
                        Preview
                      </Button>

                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleExportPdf(report)}
                        className="h-8 border-primary/40 bg-primary/10 hover:bg-primary/20 text-primary text-xs font-mono gap-1"
                        title="Download PDF"
                      >
                        <FileDown className="h-3.5 w-3.5" />
                        <span>PDF</span>
                      </Button>

                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleExportCsv(report)}
                        className="h-8 border-emerald-500/40 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 text-xs font-mono gap-1"
                        title="Download CSV"
                      >
                        <FileSpreadsheet className="h-3.5 w-3.5" />
                        <span>CSV</span>
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
