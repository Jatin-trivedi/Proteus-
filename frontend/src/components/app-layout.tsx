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
import { useState, useEffect, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth-context";
import { PlanetBackground } from "@/components/planet-background";
import { ProteusLogo, ProteusIcon } from "@/components/proteus-logo";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { KeyRound, LogOut, UserCheck } from "lucide-react";

function OperatorAuthButton() {
  const { user, isAuthenticated, logout } = useAuth();

  if (isAuthenticated && user) {
    return (
      <div className="flex items-center gap-2">
        <div className="hidden sm:flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs">
          <span className="h-1.5 w-1.5 rounded-full bg-success pulse-dot" />
          <span className="font-mono text-white font-semibold text-[11px] truncate max-w-[120px]">
            {user.username}
          </span>
          <Badge className="bg-primary/20 text-primary border-primary/30 text-[9px] px-1.5 py-0 uppercase">
            {user.role}
          </Badge>
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => {
            logout();
            toast.info("Operator Session Terminated", {
              description: "You have been signed out of the Proteus console.",
            });
          }}
          className="h-8 px-2 text-zinc-400 hover:text-white hover:bg-white/10 rounded-full"
          title="Sign Out"
        >
          <LogOut className="h-3.5 w-3.5" />
        </Button>
      </div>
    );
  }

  return (
    <Button
      asChild
      size="sm"
      variant="outline"
      className="h-8 rounded-full border-white/15 bg-white/5 hover:bg-white/10 text-xs font-semibold text-zinc-200 hover:text-white px-3 transition-colors"
    >
      <Link to="/login" className="flex items-center gap-1.5">
        <KeyRound className="h-3 w-3 text-primary" />
        <span>SIGN IN</span>
      </Link>
    </Button>
  );
}

function Brand() {
  return (
    <Link to="/" className="flex items-center">
      <ProteusLogo variant="horizontal" size="md" />
    </Link>
  );
}

function ContactModal({
  triggerText = "CONTACT US",
  triggerClassName,
  triggerVariant = "default",
}: {
  triggerText?: string;
  triggerClassName?: string;
  triggerVariant?: "default" | "outline" | "ghost";
}) {
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
        {triggerVariant === "outline" ? (
          <Button
            size="sm"
            variant="outline"
            className={cn(
              "w-full rounded-lg border-white/20 bg-white/5 hover:bg-white/10 text-xs font-semibold text-white uppercase tracking-wider h-9 gap-2 transition-all hover:border-primary/40",
              triggerClassName
            )}
          >
            <MessageSquare className="h-3.5 w-3.5 text-primary" />
            <span>{triggerText}</span>
          </Button>
        ) : (
          <Button
            size="sm"
            className={cn(
              "rounded-full bg-white text-zinc-950 hover:bg-zinc-100 hover:scale-[1.02] active:scale-[0.98] font-semibold text-xs tracking-wider uppercase px-4.5 py-2 h-9 shadow-[0_0_20px_rgba(255,255,255,0.2)] transition-all flex items-center gap-2 border border-white/20",
              triggerClassName
            )}
          >
            <MessageSquare className="h-3.5 w-3.5 fill-current text-zinc-900" />
            <span>{triggerText}</span>
          </Button>
        )}
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
    <nav className="flex items-center gap-1 xl:gap-1.5 text-[11.5px] font-bold tracking-widest uppercase">
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

      {/* 2. SCRIPTS */}
      <Link
        to="/scripts"
        className={cn(
          "px-3 py-1.5 rounded transition-colors text-zinc-300 hover:text-white",
          pathname.startsWith("/scripts") && "text-primary font-black"
        )}
      >
        SCRIPTS
      </Link>

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

      {/* 4. OPERATIONS */}
      <Link
        to="/operations"
        className={cn(
          "px-3 py-1.5 rounded transition-colors text-zinc-300 hover:text-white",
          pathname.startsWith("/operations") && "text-primary font-black"
        )}
      >
        OPERATIONS
      </Link>

      <span className="h-3 w-px bg-white/20 select-none" />

      {/* 5. RESULTS */}
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

      {/* 6. REPORTS */}
      <Link
        to="/reports"
        className={cn(
          "px-3 py-1.5 rounded transition-colors text-zinc-300 hover:text-white",
          pathname.startsWith("/reports") && "text-primary font-black"
        )}
      >
        REPORTS
      </Link>
    </nav>
  );
}

function MobileNav({ onNavigate }: { onNavigate: () => void }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const links = [
    { to: "/", label: "Home", icon: LayoutDashboard },
    { to: "/scripts", label: "Scripts", icon: FileCode2 },
    { to: "/agents", label: "Agents", icon: Bot },
    { to: "/operations", label: "Operations", icon: Radio },
    { to: "/results", label: "Results", icon: BarChart3 },
    { to: "/reports", label: "Reports", icon: FileText },
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
        <div className="flex items-center justify-between">
          <div className="text-xs font-semibold text-zinc-300">Operator Clearance</div>
          <OperatorAuthButton />
        </div>
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
  { to: "/scripts", label: "Scripts" },
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
  fullscreenBackground,
}: {
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
  fullscreenBackground?: ReactNode;
}) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const isHome = pathname === "/";
  const [stealth, setStealth] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 25);
    };
    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className={cn("relative z-10 flex min-h-screen flex-col selection:bg-primary/20 selection:text-primary", (fullscreenBackground || !isHome) ? "bg-transparent" : "bg-background")}>
      {fullscreenBackground}
      {!isHome && !fullscreenBackground && <PlanetBackground />}
      {/* Top Navbar */}
      <header
        className={cn(
          "sticky top-0 z-40 w-full transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)]",
          scrolled
            ? "border-b border-white/10 bg-black shadow-[0_12px_35px_rgba(0,0,0,0.95)] backdrop-blur-md"
            : "border-b border-white/5 bg-[linear-gradient(180deg,rgba(0,0,0,0)_0%,rgba(0,0,0,0.25)_45%,rgba(0,0,0,0.7)_100%)]"
        )}
      >
        <div
          className={cn(
            "w-full flex items-center justify-between px-6 sm:px-10 lg:px-14 xl:px-16 transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)]",
            scrolled
              ? "h-16 lg:h-[68px]"
              : "h-20 sm:h-24 lg:h-[104px]"
          )}
        >
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
            {/* Operator Auth / Clearance Status */}
            <OperatorAuthButton />

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
      <div className="flex-1 w-full bg-transparent">
        {/* Page header banner (only for subpages that pass title) */}
        {title && (
          <div className="border-b border-white/10 bg-transparent relative overflow-hidden">
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
        )}

        {/* Page body */}
        <main className={cn("mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 space-y-10 md:space-y-14", isHome ? "py-4 md:py-8" : "py-10 md:py-14")}>
          {children}
        </main>
      </div>

      {/* Professional Enterprise Footer */}
      <footer className={cn("mt-auto border-t border-white/10 relative overflow-hidden text-xs text-muted-foreground", (fullscreenBackground || !isHome) ? "bg-[#06080D]/85 backdrop-blur-md" : "bg-background")}>
        {/* Subtle background glow accents */}
        <div className="absolute top-0 left-1/4 w-96 h-32 bg-primary/5 blur-[120px] pointer-events-none rounded-full" />
        <div className="absolute top-0 right-1/4 w-96 h-32 bg-primary/5 blur-[120px] pointer-events-none rounded-full" />

        {/* Main Multi-Column Content */}
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-16 pb-12">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-10 lg:gap-12">
            {/* Col 1: Brand & Value Prop (5 cols) */}
            <div className="lg:col-span-5 space-y-5">
              <div className="flex items-center gap-3">
                <ProteusLogo size="md" />
                <Badge className="bg-primary/10 text-primary border-primary/30 text-[10px] font-mono tracking-widest uppercase">
                  Enterprise v2.4
                </Badge>
              </div>

              <p className="text-sm text-zinc-400 leading-relaxed max-w-md font-normal">
                A military-grade forensic intelligence and stealth runtime framework. Built with language-independent LLVM intermediate representations, polymorphic mutation engines, and court-admissible chain-of-custody logging.
              </p>

              {/* Grid Fleet Status Pill */}
              <div className="inline-flex items-center gap-2.5 px-3.5 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-xs">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
                </span>
                <span className="font-mono text-zinc-300 text-[11px]">
                  Fleet Grid Status: <strong className="text-primary font-semibold">Operational (14ms)</strong>
                </span>
              </div>

              {/* Security Certifications Row */}
              <div className="pt-2 flex flex-wrap items-center gap-2">
                {["ISO 27001", "SOC 2 Type II", "CMMC Level 3", "NIST 800-171", "HIPAA Ready"].map((badge) => (
                  <span
                    key={badge}
                    className="px-2.5 py-1 rounded-md bg-white/[0.02] border border-white/5 text-[10px] font-mono text-zinc-400 font-medium"
                  >
                    {badge}
                  </span>
                ))}
              </div>
            </div>

            {/* Col 2: Platform Links (2 cols) */}
            <div className="lg:col-span-2 space-y-4">
              <h4 className="text-xs font-mono font-bold tracking-[0.18em] text-white uppercase flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                Platform
              </h4>
              <ul className="space-y-2.5 text-xs font-medium">
                <li>
                  <Link to="/" className="text-zinc-400 hover:text-white transition-colors">
                    Dashboard Overview
                  </Link>
                </li>
                <li>
                  <Link to="/scripts" className="text-zinc-400 hover:text-white transition-colors">
                    Script Studio & JIT
                  </Link>
                </li>
                <li>
                  <Link to="/agents" className="text-zinc-400 hover:text-white transition-colors">
                    Agent Fleet Grid
                  </Link>
                </li>
                <li>
                  <Link to="/operations" className="text-zinc-400 hover:text-white transition-colors">
                    Operations Hub
                  </Link>
                </li>
                <li>
                  <Link to="/results" className="text-zinc-400 hover:text-white transition-colors">
                    Forensic Telemetry
                  </Link>
                </li>
                <li>
                  <Link to="/reports" className="text-zinc-400 hover:text-white transition-colors">
                    Compliance Dossiers
                  </Link>
                </li>
              </ul>
            </div>

            {/* Col 3: Architecture & Technology (2 cols) */}
            <div className="lg:col-span-2 space-y-4">
              <h4 className="text-xs font-mono font-bold tracking-[0.18em] text-white uppercase flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                Architecture
              </h4>
              <ul className="space-y-2.5 text-xs font-medium text-zinc-400">
                <li className="hover:text-zinc-200 transition-colors cursor-pointer">
                  LLVM Frontend IR
                </li>
                <li className="hover:text-zinc-200 transition-colors cursor-pointer">
                  Polymorphic Pipeline
                </li>
                <li className="hover:text-zinc-200 transition-colors cursor-pointer">
                  In-Memory Fileless Exec
                </li>
                <li className="hover:text-zinc-200 transition-colors cursor-pointer">
                  BYOVD Kernel Ring-0
                </li>
                <li className="hover:text-zinc-200 transition-colors cursor-pointer">
                  Domain Fronting & CDN
                </li>
                <li className="hover:text-zinc-200 transition-colors cursor-pointer">
                  Zero-Knowledge Proofs
                </li>
              </ul>
            </div>

            {/* Col 4: Trust & Incident Dispatch (3 cols) */}
            <div className="lg:col-span-3 space-y-4">
              <h4 className="text-xs font-mono font-bold tracking-[0.18em] text-white uppercase flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                Incident Dispatch
              </h4>
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/10 space-y-3.5">
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Emergency threat escalation or authorized forensic task engagement.
                </p>
                <div className="flex items-center gap-2 text-[11px] font-mono text-zinc-300">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                  <span>24/7 Red Team Dispatch</span>
                </div>
                <div className="pt-1">
                  <ContactModal triggerText="Open Mission Dispatch" triggerVariant="outline" />
                </div>
              </div>
              <div className="text-[10px] font-mono text-zinc-500 pt-1">
                PGP: <span className="text-zinc-400 font-mono">0x4F7A 9C21 88EB 341D</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Sub-Footer Bar */}
        <div className="border-t border-white/[0.06] bg-[#030508] py-6">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-4 text-[11px] text-zinc-400 font-mono text-center sm:text-left">
              <span>© 2026 PROTEUS Project. All rights reserved.</span>
              <span className="hidden sm:inline text-zinc-700">•</span>
              <span className="text-zinc-500">
                For authorized security research & defense compliance only.
              </span>
            </div>

            <div className="flex items-center gap-5 text-[11px] font-mono text-zinc-400">
              <span className="hover:text-white transition-colors cursor-pointer">Privacy Protocol</span>
              <span className="text-zinc-700">•</span>
              <span className="hover:text-white transition-colors cursor-pointer">Terms of Engagement</span>
              <span className="text-zinc-700">•</span>
              <span className="hover:text-white transition-colors cursor-pointer">Security Seal</span>
            </div>
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

