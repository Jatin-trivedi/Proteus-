import { Link, useRouterState } from "@tanstack/react-router";
import {
  Shield,
  Menu,
  Bell,
  Search,
  ChevronDown,
  MessageSquare,
  LayoutDashboard,
  Bot,
  FileCode2,
  Radio,
  BarChart3,
  FileText,
  Lock,
  Cpu,
  Activity,
  Send,
  CheckCircle2,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { toast } from "sonner";

function Brand() {
  return (
    <Link to="/" className="flex items-center gap-3 group">
      <div className="relative grid h-9 w-9 place-items-center rounded-lg bg-white/5 border border-white/15 glow-cyber group-hover:border-primary/50 transition-colors">
        <Shield className="h-5 w-5 text-white group-hover:text-primary transition-colors" />
        <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-primary pulse-dot" />
      </div>
      <div className="flex flex-col">
        <span className="text-base font-extrabold tracking-wider text-white font-sans flex items-center gap-1">
          PRO<span className="text-primary font-black">TEUS</span>
        </span>
        <span className="text-[9px] uppercase tracking-[0.2em] text-zinc-400 font-medium whitespace-nowrap">
          Forensic & Compliance Intelligence
        </span>
      </div>
    </Link>
  );
}

function ContactModal() {
  const [open, setOpen] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
    toast.success("Inquiry sent successfully!", {
      description: "A forensic intelligence specialist will contact you shortly.",
    });
    setTimeout(() => {
      setSubmitted(false);
      setOpen(false);
    }, 1500);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          size="sm"
          className="rounded-full bg-white text-zinc-950 hover:bg-zinc-100 hover:scale-[1.02] active:scale-[0.98] font-semibold text-xs tracking-wider uppercase px-4.5 py-2 h-9 shadow-[0_0_20px_rgba(255,255,255,0.2)] transition-all flex items-center gap-2 border border-white/20"
        >
          <MessageSquare className="h-3.5 w-3.5 fill-current text-zinc-900" />
          <span>CONTACT US</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md bg-panel border-border text-foreground">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-lg font-bold">
            <Shield className="h-5 w-5 text-primary" />
            Contact Security & Compliance Team
          </DialogTitle>
          <DialogDescription className="text-muted-foreground text-xs">
            Connect with our advisory consultants and technical forensics team.
          </DialogDescription>
        </DialogHeader>

        {submitted ? (
          <div className="py-8 flex flex-col items-center justify-center text-center space-y-3">
            <CheckCircle2 className="h-12 w-12 text-success animate-in zoom-in-50 duration-300" />
            <h3 className="font-semibold text-foreground">Request Received</h3>
            <p className="text-xs text-muted-foreground max-w-xs">
              Our rapid-response forensic team has received your inquiry.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 mt-2">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-300">Name</label>
              <Input
                required
                placeholder="Operator / Officer Name"
                className="bg-background/80 border-border h-9 text-xs"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-300">Work Email</label>
              <Input
                type="email"
                required
                placeholder="investigator@enterprise.com"
                className="bg-background/80 border-border h-9 text-xs"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-300">Inquiry Scope</label>
              <select
                className="w-full h-9 rounded-md border border-border bg-background/80 px-3 py-1 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                defaultValue="compliance"
              >
                <option value="compliance">Cybersecurity & ISO/SOC Compliance</option>
                <option value="forensics">Stealth Forensics & Incident Response</option>
                <option value="agents">Autonomous Agent Fleet Deployment</option>
                <option value="advisory">Advisory & Expert Consultation</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-zinc-300">Message / Mission Details</label>
              <textarea
                required
                rows={3}
                placeholder="Describe your security posture, requirements or incident timeline..."
                className="w-full rounded-md border border-border bg-background/80 p-2.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <div className="pt-2 flex justify-end gap-2">
              <Button type="button" variant="ghost" size="sm" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm" className="bg-primary text-primary-foreground hover:bg-primary/90">
                <Send className="h-3.5 w-3.5 mr-1.5" /> Submit Inquiry
              </Button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}

function NavLinks() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <nav className="flex items-center gap-1 xl:gap-2 text-[11.5px] font-bold tracking-widest uppercase">
      {/* 1. HOME */}
      <Link
        to="/"
        className={cn(
          "px-3 py-1.5 rounded transition-colors text-zinc-300 hover:text-white",
          pathname === "/" && "text-primary font-black"
        )}
      >
        HOME
      </Link>

      <span className="h-3 w-px bg-white/20 select-none" />

      {/* 2. OPERATION REPORTS (Dropdown with Reports & Live Operations) */}
      <DropdownMenu>
        <DropdownMenuTrigger className="flex items-center gap-1 px-3 py-1.5 rounded text-zinc-300 hover:text-white transition-colors outline-none cursor-pointer group">
          <span
            className={cn(
              (pathname.startsWith("/reports") || pathname.startsWith("/operations")) &&
                "text-primary"
            )}
          >
            OPERATION REPORTS
          </span>
          <ChevronDown className="h-3 w-3 text-zinc-400 group-hover:text-white transition-transform group-data-[state=open]:rotate-180" />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-60 bg-panel/95 backdrop-blur-md border-border p-1.5">
          <DropdownMenuLabel className="text-[10px] uppercase font-mono tracking-widest text-muted-foreground px-2 py-1">
            Operation Reports & Audits
          </DropdownMenuLabel>
          <DropdownMenuItem asChild>
            <Link to="/reports" className="flex items-center gap-2 px-2 py-2 cursor-pointer rounded-md text-xs">
              <FileText className="h-4 w-4 text-primary" />
              <div>
                <div className="font-semibold text-foreground">Audit & Forensic Reports</div>
                <div className="text-[10px] text-muted-foreground">Court-ready incident logs</div>
              </div>
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link to="/operations" className="flex items-center gap-2 px-2 py-2 cursor-pointer rounded-md text-xs">
              <Radio className="h-4 w-4 text-primary" />
              <div>
                <div className="font-semibold text-foreground">Live Operations Monitor</div>
                <div className="text-[10px] text-muted-foreground">Active runtime deployment telemetry</div>
              </div>
            </Link>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <span className="h-3 w-px bg-white/20 select-none" />

      {/* 3. AGENTS */}
      <Link
        to="/agents"
        className={cn(
          "px-3 py-1.5 rounded transition-colors text-zinc-300 hover:text-white",
          pathname.startsWith("/agents") && "text-primary font-black"
        )}
      >
        AGENTS
      </Link>

      <span className="h-3 w-px bg-white/20 select-none" />

      {/* 4. RESULTS */}
      <Link
        to="/results"
        className={cn(
          "px-3 py-1.5 rounded transition-colors text-zinc-300 hover:text-white",
          pathname.startsWith("/results") && "text-primary font-black"
        )}
      >
        RESULTS
      </Link>

      <span className="h-3 w-px bg-white/20 select-none" />

      {/* 5. SCRIPT */}
      <Link
        to="/scripts"
        className={cn(
          "px-3 py-1.5 rounded transition-colors text-zinc-300 hover:text-white",
          pathname.startsWith("/scripts") && "text-primary font-black"
        )}
      >
        SCRIPT
      </Link>
    </nav>
  );
}

function MobileNav({ onNavigate }: { onNavigate: () => void }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const links = [
    { to: "/", label: "Home", icon: LayoutDashboard },
    { to: "/reports", label: "Operation Reports", icon: FileText },
    { to: "/agents", label: "Agents", icon: Bot },
    { to: "/results", label: "Results", icon: BarChart3 },
    { to: "/scripts", label: "Script", icon: FileCode2 },
  ] as const;

  return (
    <div className="flex flex-col h-full bg-sidebar p-6 text-sidebar-foreground space-y-6">
      <Brand />
      <div className="h-px bg-sidebar-border" />
      <div className="space-y-1">
        <div className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground px-2 mb-2">
          Navigation
        </div>
        {links.map(({ to, label, icon: Icon }) => {
          const active = to === "/" ? pathname === "/" : pathname.startsWith(to);
          return (
            <Link
              key={to}
              to={to}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                active
                  ? "bg-primary/10 text-primary border border-primary/20"
                  : "text-muted-foreground hover:bg-sidebar-accent hover:text-foreground"
              )}
            >
              <Icon className={cn("h-4 w-4", active && "text-primary")} />
              <span>{label}</span>
              {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary pulse-dot" />}
            </Link>
          );
        })}
      </div>

      <div className="mt-auto pt-6 border-t border-sidebar-border space-y-4">
        <div className="rounded-lg border border-primary/25 bg-primary/5 p-3.5">
          <div className="flex items-center gap-2 text-xs font-semibold text-primary">
            <Shield className="h-3.5 w-3.5" /> Stealth Mode
            <Badge className="ml-auto bg-success/15 text-success border-success/30">
              Active
            </Badge>
          </div>
          <p className="mt-1.5 text-[11px] leading-relaxed text-muted-foreground">
            Polymorphic obfuscation active across all active telemetry.
          </p>
        </div>
      </div>
    </div>
  );
}

const WORKFLOW = [
  { to: "/", label: "Home" },
  { to: "/scripts", label: "Script" },
  { to: "/agents", label: "Agents" },
  { to: "/operations", label: "Operations" },
  { to: "/results", label: "Results" },
  { to: "/reports", label: "Reports" },
] as const;

function WorkflowStrip() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const activeIdx = WORKFLOW.findIndex((w) =>
    w.to === "/" ? pathname === "/" : pathname.startsWith(w.to),
  );
  return (
    <div className="hidden md:flex items-center gap-1 text-[11px] font-mono uppercase tracking-widest">
      {WORKFLOW.map((w, i) => {
        const active = i === activeIdx;
        const done = activeIdx > -1 && i < activeIdx;
        return (
          <div key={w.to} className="flex items-center gap-1">
            <span
              className={cn(
                "rounded px-2.5 py-1 border transition-colors",
                active && "bg-primary/15 text-primary border-primary/40 shadow-[0_0_12px_rgba(0,229,255,0.15)]",
                done && "text-success border-success/30 bg-success/5",
                !active && !done && "text-muted-foreground border-border bg-panel/30",
              )}
            >
              {w.label}
            </span>
            {i < WORKFLOW.length - 1 && <span className="text-zinc-600">→</span>}
          </div>
        );
      })}
    </div>
  );
}

export function AppLayout({
  title,
  subtitle,
  actions,
  children,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  const [stealth, setStealth] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="relative z-10 flex min-h-screen flex-col bg-background selection:bg-primary/20 selection:text-primary">
      {/* Top Navbar */}
      <header className="sticky top-0 z-40 w-full border-b border-white/10 bg-[#0a0f1d]/90 backdrop-blur-xl transition-all">
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Left Brand */}
          <div className="flex items-center gap-6">
            <Brand />
          </div>

          {/* Center / Right Nav items (Desktop) */}
          <div className="hidden lg:flex items-center gap-6">
            <NavLinks />
          </div>

          {/* Right Action buttons */}
          <div className="flex items-center gap-3">
            {/* Stealth Toggle (Desktop) */}
            <div className="hidden xl:flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 backdrop-blur">
              <span className={cn("h-2 w-2 rounded-full", stealth ? "bg-primary pulse-dot" : "bg-muted-foreground")} />
              <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
                Stealth
              </span>
              <Switch checked={stealth} onCheckedChange={setStealth} className="scale-75" />
            </div>

            {/* Talk / Contact Us Pill Button */}
            <ContactModal />

            {/* Mobile Sheet Trigger */}
            <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
              <SheetTrigger asChild>
                <Button size="icon" variant="ghost" className="lg:hidden text-zinc-300 hover:text-white">
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="p-0 w-80 bg-sidebar border-sidebar-border">
                <SheetHeader className="sr-only">
                  <SheetTitle>Navigation Menu</SheetTitle>
                </SheetHeader>
                <MobileNav onNavigate={() => setMobileOpen(false)} />
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </header>

      {/* Main Content Area (Full width clean container) */}
      <div className="flex-1 w-full">
        {/* Page header banner */}
        <div className="border-b border-border/60 bg-background/40 backdrop-blur-sm relative overflow-hidden">
          {/* Subtle glow accent */}
          <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-[600px] h-[150px] bg-primary/10 blur-[100px] pointer-events-none rounded-full" />

          <div className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-10 md:py-12 flex flex-col gap-6 md:flex-row md:items-end md:justify-between relative z-10">
            <div className="min-w-0 max-w-3xl">
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-primary/10 border border-primary/20 text-[11px] font-mono uppercase tracking-widest text-primary mb-3">
                <Shield className="h-3 w-3" /> Expert-Led Forensics & Compliance
              </div>
              <h1 className="text-3xl md:text-[2.5rem] font-extrabold tracking-tight leading-[1.15] text-foreground">
                {title}
              </h1>
              {subtitle && (
                <p className="mt-3 text-base leading-relaxed text-muted-foreground">{subtitle}</p>
              )}
              <div className="mt-6">
                <WorkflowStrip />
              </div>
            </div>
            {actions && <div className="flex flex-wrap gap-3 shrink-0 items-center">{actions}</div>}
          </div>
        </div>

        {/* Page body */}
        <main className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-10 md:py-14 space-y-10 md:space-y-14">
          {children}
        </main>
      </div>

      {/* Footer */}
      <footer className="mt-auto border-t border-white/10 bg-[#070b14] py-8 text-xs text-muted-foreground">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-primary" />
            <span className="font-semibold text-foreground">PROTEUS</span>
            <span>— Forensics & Information Security Platform</span>
          </div>
          <div className="flex items-center gap-4 text-[11px] font-mono">
            <span>ISO 27001</span>
            <span>•</span>
            <span>SOC 2 Type II</span>
            <span>•</span>
            <span>CMMC Ready</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export function StatusDot({ status }: { status: "online" | "offline" | "executing" | "warning" }) {
  const cls = {
    online: "bg-success",
    executing: "bg-warning",
    warning: "bg-warning",
    offline: "bg-destructive",
  }[status];
  return <span className={cn("inline-block h-2 w-2 rounded-full", cls, status !== "offline" && "pulse-dot")} />;
}

export { Shield, ShieldOff } from "lucide-react";

