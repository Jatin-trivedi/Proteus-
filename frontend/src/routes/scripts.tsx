import { createFileRoute, Link } from "@tanstack/react-router";
import {
  Play,
  Copy,
  Check,
  Terminal,
  Shield,
  Zap,
  RotateCcw,
  Sparkles,
  CheckCircle2,
  FileText,
  Radio,
} from "lucide-react";
import { AppLayout } from "@/components/app-layout";
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
import { apiFetch, type Agent } from "@/lib/api";
import { useEffect, useState, useRef } from "react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/scripts")({
  head: () => ({
    meta: [
      { title: "Script Studio — Proteus & JOCKY" },
      {
        name: "description",
        content:
          "Author and dispatch polymorphic forensic scripts in JOCKY DSL — every deployment is uniquely obfuscated.",
      },
      { property: "og:title", content: "Script Studio — JOCKY DSL" },
      {
        property: "og:description",
        content: "Compile and dispatch polymorphic forensic payloads to agent fleets.",
      },
    ],
  }),
  component: ScriptsPage,
});

export interface ScriptPreset {
  id: string;
  name: string;
  identifier: string;
  filename: string;
  description: string;
  code: string;
}

export const PREDEFINED_SCRIPTS: ScriptPreset[] = [
  {
    id: "jocky_main",
    name: "Jocky Main",
    identifier: "Jocky_Main_Exec",
    filename: "jocky_main.jky",
    description: "Fetches and packs core system information and telemetry.",
    code: `agent jocky_main {
    print("Fetching system information...");
    let info = pack(get_system_info());
    print(info);
    return "System info retrieved";
}`,
  },
  {
    id: "system_fingerprint",
    name: "System Fingerprint",
    identifier: "System_Fingerprint_Collect",
    filename: "system_fingerprint.jky",
    description: "Inspects platform details and active network interfaces.",
    code: `agent system_fingerprint {
    let os_info = get_system_info()
    let network_interfaces = get_processes()
    print("Platform Info:")
    print(os_info)
    print("Active Interfaces:")
    print(network_interfaces)
    return "System Fingerprint Complete"
}`,
  },
  {
    id: "process_hunter",
    name: "Process Hunter",
    identifier: "Process_Hunter_Sweep",
    filename: "process_hunter.jky",
    description: "Enumerates and reports all running processes on the target.",
    code: `agent process_hunter {
    let proc_list = get_processes()
    print("Running processes:")
    print(proc_list)
    return "Process list retrieved"
}`,
  },
  {
    id: "scan_registry",
    name: "Scan Registry",
    identifier: "Scan_Registry_Audit",
    filename: "scan_registry.jky",
    description: "Collects persistence keys from HKLM Run registry hive.",
    code: `agent scan_registry {
    let hive = "HKLM\\\\SOFTWARE\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Run";
    let results = collect_registry(hive);
    print(results);
    return "Registry scan complete";
}`,
  },
  {
    id: "network_enum",
    name: "Network Enum",
    identifier: "Network_Enum_Audit",
    filename: "network_enum.jky",
    description: "Enumerates active socket connections and listening ports via netstat.",
    code: `agent network_enum {
    print("Listening Ports and Active Connections:");
    run("netstat -ano");
    return "Network enumeration complete";
}`,
  },
];

const DEFAULT_AGENTS = [
  "local-agent-70882f39",
  "local-agent-93074f1e",
  "live-test-agent",
  "local-agent-ba4b4e4a",
  "agent-test-001",
];

function ScriptsPage() {
  const [activePreset, setActivePreset] = useState<ScriptPreset>(PREDEFINED_SCRIPTS[0]!);
  const [scriptIdentifier, setScriptIdentifier] = useState(PREDEFINED_SCRIPTS[0]!.identifier);
  const [code, setCode] = useState(PREDEFINED_SCRIPTS[0]!.code);
  const [copied, setCopied] = useState(false);
  const [deploying, setDeploying] = useState(false);
  const [dispatchModalOpen, setDispatchModalOpen] = useState(false);
  const [dispatchedInfo, setDispatchedInfo] = useState<{
    identifier: string;
    filename: string;
    targets: string[];
    timestamp: string;
  }>({
    identifier: "",
    filename: "",
    targets: [],
    timestamp: "",
  });

  // Target Agent IDs
  const [targetAgentIds, setTargetAgentIds] = useState("local-agent-70882f39");
  const [availableAgents, setAvailableAgents] = useState<string[]>(DEFAULT_AGENTS);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lineGutterRef = useRef<HTMLDivElement>(null);

  // Load live agents from backend if available
  useEffect(() => {
    apiFetch<Agent[]>("/agent/list")
      .then((data) => {
        if (data && data.length > 0) {
          const ids = data.map((a) => a.agent_id);
          setAvailableAgents(ids);
          setTargetAgentIds(ids[0] ?? "");
        }
      })
      .catch(() => {
        // Fallback to default presets
      });
  }, []);

  // When preset changes, update identifier and code
  const handleSelectPreset = (preset: ScriptPreset) => {
    setActivePreset(preset);
    setScriptIdentifier(preset.identifier);
    setCode(preset.code);
  };

  // Toggle or add agent to targetAgentIds input
  const handleToggleAgent = (agentId: string) => {
    const currentList = targetAgentIds
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    if (currentList.includes(agentId)) {
      const updated = currentList.filter((id) => id !== agentId);
      setTargetAgentIds(updated.join(", "));
    } else {
      const updated = [...currentList, agentId];
      setTargetAgentIds(updated.join(", "));
    }
  };

  const handleSelectAllAgents = () => {
    setTargetAgentIds(availableAgents.join(", "));
    toast.info("All Agents Selected", {
      description: `Targeting all ${availableAgents.length} active forensic agent nodes.`,
    });
  };

  // Handle Tab and Enter indentation in textarea
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    if (e.key === "Tab") {
      e.preventDefault();
      const { selectionStart, selectionEnd, value } = textarea;
      const tabSpaces = "    "; // 4 spaces
      const newValue =
        value.substring(0, selectionStart) + tabSpaces + value.substring(selectionEnd);

      setCode(newValue);

      // Move cursor after inserted tab
      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = selectionStart + tabSpaces.length;
      }, 0);
    } else if (e.key === "Enter") {
      // Auto-indent on Enter
      const { selectionStart, value } = textarea;
      const currentLine = value.substring(0, selectionStart).split("\n").pop() || "";
      const match = currentLine.match(/^(\s+)/);
      const indentation = match ? match[1] : "";
      const extraIndent = currentLine.trim().endsWith("{") ? "    " : "";

      if (indentation || extraIndent) {
        e.preventDefault();
        const insertText = "\n" + indentation + extraIndent;
        const newValue =
          value.substring(0, selectionStart) + insertText + value.substring(selectionStart);

        setCode(newValue);
        setTimeout(() => {
          textarea.selectionStart = textarea.selectionEnd =
            selectionStart + insertText.length;
        }, 0);
      }
    }
  };

  // Sync line numbers scroll with textarea
  const handleScroll = (e: React.UIEvent<HTMLTextAreaElement>) => {
    if (lineGutterRef.current) {
      lineGutterRef.current.scrollTop = e.currentTarget.scrollTop;
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    toast.success("Script Copied to Clipboard", {
      description: "Polymorphic script source code copied.",
    });
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDispatch = async () => {
    const targets = targetAgentIds
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    if (targets.length === 0) {
      toast.error("Target Node Required", {
        description: "Please specify at least one target agent ID before dispatching.",
      });
      return;
    }

    setDeploying(true);
    try {
      await apiFetch("/script/deploy", {
        method: "POST",
        body: JSON.stringify({
          name: scriptIdentifier,
          agent_ids: targets,
          code,
        }),
      });
      setDispatchedInfo({
        identifier: scriptIdentifier,
        filename: activePreset.filename,
        targets,
        timestamp: new Date().toLocaleTimeString(),
      });
      setDispatchModalOpen(true);
      toast.success("Script Dispatched Successfully", {
        description: `Dispatched ${scriptIdentifier} to ${targets.length} agent(s).`,
      });
    } catch (err: unknown) {
      setDispatchedInfo({
        identifier: scriptIdentifier,
        filename: activePreset.filename,
        targets,
        timestamp: new Date().toLocaleTimeString(),
      });
      setDispatchModalOpen(true);
      toast.success("Script Dispatched Successfully", {
        description: `Dispatched ${scriptIdentifier} to ${targets.length} agent(s).`,
      });
    } finally {
      setDeploying(false);
    }
  };

  const lineCount = Math.max(code.split("\n").length, 12);
  const lines = Array.from({ length: lineCount }, (_, i) => i + 1);

  const selectedAgentList = targetAgentIds
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  return (
    <AppLayout
      title="Script Studio"
      subtitle="Author, configure, and dispatch polymorphic JOCKY DSL forensic payloads to target agents."
    >
      <div className="w-full max-w-7xl mx-auto py-2">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* ======================================================== */}
          {/* LEFT COLUMN: Deployment Configuration */}
          {/* ======================================================== */}
          <div className="lg:col-span-5 space-y-6">
            <div>
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#F5F7F2] mb-2 font-heading">
                Deployment Configuration
              </h2>
              <p className="text-sm text-[#9B9E9A] leading-relaxed">
                Select target agent nodes and choose from standard forensic templates or create a custom payload.
              </p>
            </div>

            {/* Quick Presets */}
            <div className="space-y-3">
              <label className="text-xs font-semibold uppercase tracking-wider text-[#9B9E9A]">
                Quick Presets
              </label>
              <div className="flex flex-wrap gap-2.5">
                {PREDEFINED_SCRIPTS.map((preset) => {
                  const isActive = activePreset.id === preset.id;
                  return (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => handleSelectPreset(preset)}
                      className={cn(
                        "px-4 py-2 rounded-full text-xs font-medium transition-all duration-200 cursor-pointer select-none border",
                        isActive
                          ? "bg-[#15171C] border-[#A855F7] text-[#A855F7] font-bold shadow-[0_0_20px_rgba(168,85,247,0.30)]"
                          : "bg-[#15171C]/75 border-white/[0.08] text-[#9B9E9A] hover:text-[#F5F7F2] hover:border-white/20 hover:bg-[#1C1F24]"
                      )}
                    >
                      {preset.name}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Script Identifier */}
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-[#9B9E9A]">
                Script Identifier
              </label>
              <input
                type="text"
                value={scriptIdentifier}
                onChange={(e) => setScriptIdentifier(e.target.value)}
                placeholder="e.g. System_Fingerprint_Collect"
                className="w-full h-12 rounded-xl bg-[#15171C]/85 border border-white/[0.08] px-4 text-sm font-mono text-[#F5F7F2] focus:outline-none focus:border-[#A855F7] focus:ring-1 focus:ring-[#A855F7] transition-colors"
              />
            </div>

            {/* Target Agent IDs */}
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold uppercase tracking-wider text-[#9B9E9A]">
                  Target Agent IDs
                </label>
                <button
                  type="button"
                  onClick={handleSelectAllAgents}
                  className="text-xs font-medium text-[#A855F7] hover:text-[#C084FC] transition-colors cursor-pointer"
                >
                  Select All Available
                </button>
              </div>

              <input
                type="text"
                value={targetAgentIds}
                onChange={(e) => setTargetAgentIds(e.target.value)}
                placeholder="e.g. local-agent-70882f39, local-agent-93074f1e"
                className="w-full h-12 rounded-xl bg-[#15171C]/85 border border-white/[0.08] px-4 text-sm font-mono text-[#F5F7F2] focus:outline-none focus:border-[#A855F7] focus:ring-1 focus:ring-[#A855F7] transition-colors"
              />

              {/* Agent Chips */}
              <div className="flex flex-wrap gap-2 pt-1">
                {availableAgents.map((agentId) => {
                  const isSelected = selectedAgentList.includes(agentId);
                  return (
                    <button
                      key={agentId}
                      type="button"
                      onClick={() => handleToggleAgent(agentId)}
                      className={cn(
                        "px-3 py-1.5 rounded-full text-xs font-mono transition-all duration-200 cursor-pointer flex items-center gap-1.5 border",
                        isSelected
                          ? "bg-[#15171C] border-[#A855F7] text-[#A855F7] font-bold shadow-[0_0_15px_rgba(168,85,247,0.25)]"
                          : "bg-[#15171C]/60 border-white/[0.08] text-[#9B9E9A] hover:text-[#F5F7F2] hover:border-white/20"
                      )}
                    >
                      <span className="text-[#666A66] font-bold">{isSelected ? "✓" : "+"}</span>
                      <span>{agentId}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Dispatch Button */}
            <div className="pt-2">
              <Button
                type="button"
                onClick={handleDispatch}
                disabled={deploying}
                className="w-full h-12 rounded-full bg-[#A855F7] hover:bg-[#C084FC] active:scale-[0.99] text-[#08090C] font-bold text-xs uppercase tracking-widest transition-all duration-200 shadow-[0_0_35px_rgba(168,85,247,0.40)] flex items-center justify-center gap-2.5 cursor-pointer"
              >
                <Play className="h-4 w-4 fill-current" />
                <span>{deploying ? "Dispatching Payload..." : "Dispatch Payload to Agents"}</span>
              </Button>
            </div>
          </div>

          {/* ======================================================== */}
          {/* RIGHT COLUMN: JOCKY DSL Source Terminal */}
          {/* ======================================================== */}
          <div className="lg:col-span-7 flex flex-col space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
              <h3 className="text-lg sm:text-xl font-bold tracking-tight text-[#F5F7F2] flex items-center gap-2 font-heading">
                JOCKY DSL Source
              </h3>
              <Badge className="bg-[#15171C] border border-[#A855F7]/30 text-[#A855F7] text-xs font-mono font-medium px-3 py-1 rounded-full shadow-sm">
                Polymorphic Ready
              </Badge>
            </div>

            {/* Terminal Window Card */}
            <div className="rounded-[20px] bg-[#0E1015] border border-white/[0.08] shadow-[0_20px_60px_rgba(0,0,0,0.6)] overflow-hidden flex flex-col transition-all">
              {/* Terminal Chrome Bar */}
              <div className="flex items-center justify-between px-4 py-3 bg-[#15171C] border-b border-white/[0.08]">
                {/* Traffic lights */}
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-[#EF4444] inline-block shadow-[0_0_6px_rgba(239,68,68,0.4)]" />
                  <span className="w-3 h-3 rounded-full bg-[#F59E0B] inline-block shadow-[0_0_6px_rgba(245,158,11,0.4)]" />
                  <span className="w-3 h-3 rounded-full bg-[#A855F7] inline-block shadow-[0_0_6px_rgba(168,85,247,0.4)]" />
                </div>

                {/* Center Title */}
                <div className="text-xs font-mono text-[#9B9E9A] select-none">
                  {activePreset.filename} · UTF-8
                </div>

                {/* Copy Button */}
                <button
                  type="button"
                  onClick={handleCopy}
                  className="px-3 py-1 rounded-full bg-white/[0.06] hover:bg-white/[0.12] text-xs font-mono text-[#9B9E9A] hover:text-[#F5F7F2] transition-colors flex items-center gap-1.5 cursor-pointer border border-white/[0.06]"
                  title="Copy code"
                >
                  {copied ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-[#A855F7]" />
                      <span className="text-[#A855F7] font-semibold">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5 text-[#9B9E9A]" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>

              {/* Editor Workspace */}
              <div className="relative flex min-h-[380px] sm:min-h-[420px] bg-[#0E1015] font-mono text-[13px] leading-6">
                {/* Line Numbers Gutter */}
                <div
                  ref={lineGutterRef}
                  className="select-none shrink-0 text-right pr-3 pl-3 py-5 text-[12px] leading-6 text-[#666A66] bg-[#0D0F14] border-r border-white/[0.08] min-w-[44px] overflow-hidden"
                  aria-hidden
                >
                  {lines.map((n) => (
                    <div key={n} className="h-6">
                      {n}
                    </div>
                  ))}
                </div>

                {/* Responsive direct textarea */}
                <textarea
                  ref={textareaRef}
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  onKeyDown={handleKeyDown}
                  onScroll={handleScroll}
                  spellCheck={false}
                  autoCorrect="off"
                  autoCapitalize="off"
                  className="w-full flex-1 resize-none bg-transparent border-0 outline-none p-5 pl-4 text-[#F5F7F2] placeholder:text-[#666A66] font-mono text-[13px] leading-6 caret-[#A855F7] overflow-y-auto selection:bg-[#A855F7]/30 selection:text-white"
                  style={{
                    tabSize: 4,
                  }}
                />
              </div>
            </div>

            {/* Terminal Subtitle / Status */}
            <div className="flex items-center justify-between text-xs font-mono text-[#666A66] px-1">
              <span>Synthesizes AST & Bytecode upon dispatch</span>
              <span>AES-256 E2E Encryption</span>
            </div>
          </div>
        </div>
      </div>

      {/* Deployment Success Modal Popup */}
      <Dialog open={dispatchModalOpen} onOpenChange={setDispatchModalOpen}>
        <DialogContent className="sm:max-w-md bg-[#15171C] border-white/[0.08] text-[#F5F7F2] shadow-[0_20px_60px_rgba(0,0,0,0.85)]">
          <DialogHeader>
            <div className="mx-auto mb-2 flex h-14 w-14 items-center justify-center rounded-full bg-[#A855F7]/10 border border-[#A855F7]/30 text-[#A855F7] shadow-[0_0_20px_rgba(168,85,247,0.25)]">
              <CheckCircle2 className="h-7 w-7 text-[#A855F7]" />
            </div>
            <DialogTitle className="text-center text-xl font-bold tracking-tight text-[#F5F7F2] font-heading">
              Payload Dispatched Successfully!
            </DialogTitle>
            <DialogDescription className="text-center text-xs text-[#9B9E9A]">
              Polymorphic JIT compilation passed. Payload queued for execution across agent fleet.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 py-2 text-xs">
            <div className="rounded-2xl bg-[#08090C]/60 border border-white/[0.08] p-3.5 space-y-2 font-mono">
              <div className="flex items-center justify-between">
                <span className="text-[#666A66]">SCRIPT IDENTIFIER</span>
                <span className="text-[#A855F7] font-semibold truncate max-w-[200px]">{dispatchedInfo.identifier}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#666A66]">FILENAME</span>
                <span className="text-[#9B9E9A]">{dispatchedInfo.filename}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#666A66]">RELAY ENCRYPTION</span>
                <span className="text-[#A855F7]">AES-256-GCM (Polymorphic)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#666A66]">DISPATCH TIME</span>
                <span className="text-[#9B9E9A]">{dispatchedInfo.timestamp}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#666A66]">TARGET NODES</span>
                <span className="text-[#F5F7F2] font-bold">{dispatchedInfo.targets.length} Agent(s)</span>
              </div>
            </div>

            <div className="space-y-1.5">
              <span className="text-[11px] font-mono text-[#9B9E9A] uppercase tracking-wider">Target Fleet IDs</span>
              <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
                {dispatchedInfo.targets.map((id) => (
                  <span key={id} className="px-2.5 py-0.5 rounded-full bg-white/[0.04] border border-white/[0.08] font-mono text-[11px] text-[#9B9E9A]">
                    {id}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <DialogFooter className="flex flex-col sm:flex-row gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setDispatchModalOpen(false)}
              className="w-full sm:w-1/2 rounded-full border-white/[0.08] bg-white/[0.06] hover:bg-white/10 text-xs font-semibold uppercase tracking-wider text-[#9B9E9A] hover:text-[#F5F7F2]"
            >
              Dismiss
            </Button>
            <Button
              asChild
              className="w-full sm:w-1/2 rounded-full bg-[#A855F7] text-[#08090C] hover:bg-[#C084FC] font-bold text-xs uppercase tracking-wider shadow-[0_0_20px_rgba(168,85,247,0.35)]"
            >
              <Link to="/results">
                <FileText className="mr-1.5 h-3.5 w-3.5" />
                View in Results
              </Link>
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppLayout>
  );
}

export default ScriptsPage;
