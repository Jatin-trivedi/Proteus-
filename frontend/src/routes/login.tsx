import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import {
  Shield,
  Lock,
  User,
  KeyRound,
  Eye,
  EyeOff,
  ArrowRight,
  Fingerprint,
  CheckCircle2,
  AlertCircle,
  Terminal,
  Cpu,
  Sparkles,
  Zap,
} from "lucide-react";
import { ProteusLogo, ProteusIcon } from "@/components/proteus-logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useAuth, type UserRole } from "@/lib/auth-context";
import { toast } from "sonner";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Operator Authentication — Proteus" },
      { name: "description", content: "Sign in to the Proteus forensic intelligence and compliance console." },
      { property: "og:title", content: "Operator Authentication — Proteus" },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const { login, register, loginDemo, isAuthenticated, user, logout } = useAuth();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setRole] = useState<UserRole>("lead_investigator");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setIsLoading(true);

    try {
      if (mode === "login") {
        await login(username, password);
        toast.success("Security Clearance Verified", {
          description: `Welcome back, Operator ${username}. Session established.`,
        });
        navigate({ to: "/" });
      } else {
        if (password !== confirmPassword) {
          throw new Error("Credentials mismatch: Confirmation password does not match.");
        }
        if (password.length < 8) {
          throw new Error("Security policy requirement: Password must be at least 8 characters.");
        }
        await register(username, password, role);
        toast.success("Operator Credentials Provisioned", {
          description: `Clearance granted for ${username} [${role.toUpperCase()}].`,
        });
        navigate({ to: "/" });
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Authentication failed. Verify credentials.");
      toast.error("Access Denied", {
        description: err.message || "Failed to authenticate operator credentials.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = (selectedRole: UserRole) => {
    loginDemo(selectedRole);
    toast.success("Demo Clearance Granted", {
      description: `Authenticated as ${selectedRole.replace("_", " ").toUpperCase()}.`,
    });
    navigate({ to: "/" });
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-foreground flex flex-col justify-between relative overflow-hidden selection:bg-primary/30 selection:text-white">
      {/* Background ambient grid & neon glows */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff05_1px,transparent_1px),linear-gradient(to_bottom,#ffffff05_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[300px] bg-primary/10 blur-[130px] pointer-events-none rounded-full" />
      <div className="absolute -bottom-32 right-0 w-[500px] h-[300px] bg-cyan-600/10 blur-[140px] pointer-events-none rounded-full" />

      {/* Top Header Bar */}
      <header className="relative z-10 w-full max-w-7xl mx-auto px-6 py-6 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3">
          <ProteusLogo variant="horizontal" size="md" />
        </Link>
        <div className="flex items-center gap-3">
          <Link
            to="/"
            className="text-xs font-mono text-muted-foreground hover:text-white transition-colors flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-white/10 bg-white/5"
          >
            <ArrowRight className="h-3.5 w-3.5 rotate-180" /> Back to Console
          </Link>
        </div>
      </header>

      {/* Main Authentication Card */}
      <main className="relative z-10 w-full max-w-md mx-auto px-4 py-8">
        <div className="relative rounded-2xl border border-white/10 bg-panel/90 backdrop-blur-xl p-6 sm:p-8 shadow-[0_0_50px_rgba(0,0,0,0.8)] glow-cyber">
          {/* Top Logo & Status */}
          <div className="text-center mb-6">
            <div className="inline-flex p-3 rounded-2xl bg-white/5 border border-white/10 mb-3 shadow-[0_0_20px_rgba(56,189,248,0.2)]">
              <ProteusIcon size="lg" glow theme="white" />
            </div>
            <h1 className="text-2xl font-black tracking-tight text-white">
              {mode === "login" ? "Operator Authentication" : "Provision New Identity"}
            </h1>
            <p className="mt-1.5 text-xs text-muted-foreground">
              {mode === "login"
                ? "Enter your cryptographic credentials to access the telemetry console"
                : "Register a forensic operator identity with assigned security role"}
            </p>
          </div>

          {/* Tab Switcher */}
          <div className="grid grid-cols-2 p-1 rounded-lg bg-black/40 border border-white/10 mb-6 text-xs font-semibold">
            <button
              type="button"
              onClick={() => {
                setMode("login");
                setErrorMessage(null);
              }}
              className={`py-2 rounded-md transition-all ${
                mode === "login"
                  ? "bg-primary text-primary-foreground shadow-[0_0_15px_rgba(56,189,248,0.3)] font-bold"
                  : "text-muted-foreground hover:text-white"
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setMode("register");
                setErrorMessage(null);
              }}
              className={`py-2 rounded-md transition-all ${
                mode === "register"
                  ? "bg-primary text-primary-foreground shadow-[0_0_15px_rgba(56,189,248,0.3)] font-bold"
                  : "text-muted-foreground hover:text-white"
              }`}
            >
              Provision Account
            </button>
          </div>

          {/* Error Message Box */}
          {errorMessage && (
            <div className="mb-4 p-3 rounded-lg bg-destructive/10 border border-destructive/30 text-destructive text-xs flex items-start gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username / Operator ID */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-zinc-300 flex items-center gap-1.5">
                <User className="h-3.5 w-3.5 text-primary" /> Operator Call-Sign / ID
              </label>
              <div className="relative">
                <Input
                  required
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. jatin_trivedi or lead_analyst"
                  className="bg-black/50 border-white/15 h-10 text-xs pl-3 font-mono text-white placeholder:text-zinc-500 focus:border-primary"
                />
              </div>
            </div>

            {/* Role selection for registration */}
            {mode === "register" && (
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-zinc-300 flex items-center gap-1.5">
                  <Shield className="h-3.5 w-3.5 text-primary" /> Security Clearance Role
                </label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as UserRole)}
                  className="w-full rounded-md border border-white/15 bg-black/50 p-2.5 text-xs text-foreground font-mono focus:border-primary focus:outline-none"
                >
                  <option value="lead_investigator">Lead Investigator (Full Fleet Access)</option>
                  <option value="analyst">Forensic Analyst (Standard Deployments)</option>
                  <option value="admin">System Administrator (Root Security)</option>
                  <option value="auditor">Compliance Auditor (Read-Only Logs)</option>
                </select>
              </div>
            )}

            {/* Password */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold uppercase tracking-wider text-zinc-300 flex items-center gap-1.5">
                  <Lock className="h-3.5 w-3.5 text-primary" /> Passphrase / Cryptographic Key
                </label>
                {mode === "login" && (
                  <button
                    type="button"
                    onClick={() => toast.info("Passphrase Recovery", { description: "Contact your fleet master key administrator to rotate credentials." })}
                    className="text-[11px] text-primary hover:underline"
                  >
                    Forgot Key?
                  </button>
                )}
              </div>
              <div className="relative">
                <Input
                  required
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="bg-black/50 border-white/15 h-10 text-xs pl-3 pr-10 font-mono text-white placeholder:text-zinc-500 focus:border-primary"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-white"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* Confirm Password for registration */}
            {mode === "register" && (
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-zinc-300 flex items-center gap-1.5">
                  <KeyRound className="h-3.5 w-3.5 text-primary" /> Confirm Passphrase
                </label>
                <Input
                  required
                  type={showPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="bg-black/50 border-white/15 h-10 text-xs pl-3 font-mono text-white placeholder:text-zinc-500 focus:border-primary"
                />
              </div>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full h-10 bg-primary text-primary-foreground hover:bg-primary/90 font-bold text-xs uppercase tracking-widest transition-all glow-cyber mt-2"
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 border-2 border-current border-t-transparent animate-spin rounded-full" />
                  <span>Verifying Clearance...</span>
                </div>
              ) : mode === "login" ? (
                <div className="flex items-center justify-center gap-2">
                  <Fingerprint className="h-4 w-4" />
                  <span>Authorize & Decrypt Session</span>
                </div>
              ) : (
                <div className="flex items-center justify-center gap-2">
                  <KeyRound className="h-4 w-4" />
                  <span>Generate Operator Access</span>
                </div>
              )}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative my-6 text-center">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/10" />
            </div>
            <span className="relative bg-panel px-3 text-[10px] uppercase tracking-widest text-muted-foreground font-mono">
              Quick Operator Clearance (Dev Preview)
            </span>
          </div>

          {/* Fast Demo Access Pills */}
          <div className="grid grid-cols-2 gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => handleDemoLogin("lead_investigator")}
              className="border-white/10 bg-white/5 hover:bg-white/10 text-[11px] h-8 text-zinc-300 hover:text-white justify-start"
            >
              <Zap className="h-3 w-3 text-primary mr-1.5 shrink-0" />
              <span className="truncate">Lead Investigator</span>
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => handleDemoLogin("admin")}
              className="border-white/10 bg-white/5 hover:bg-white/10 text-[11px] h-8 text-zinc-300 hover:text-white justify-start"
            >
              <Shield className="h-3 w-3 text-cyan-400 mr-1.5 shrink-0" />
              <span className="truncate">Security Admin</span>
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => handleDemoLogin("analyst")}
              className="border-white/10 bg-white/5 hover:bg-white/10 text-[11px] h-8 text-zinc-300 hover:text-white justify-start"
            >
              <Terminal className="h-3 w-3 text-emerald-400 mr-1.5 shrink-0" />
              <span className="truncate">Forensic Analyst</span>
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => handleDemoLogin("auditor")}
              className="border-white/10 bg-white/5 hover:bg-white/10 text-[11px] h-8 text-zinc-300 hover:text-white justify-start"
            >
              <CheckCircle2 className="h-3 w-3 text-yellow-400 mr-1.5 shrink-0" />
              <span className="truncate">SOC 2 Auditor</span>
            </Button>
          </div>
        </div>

        {/* Security badges below card */}
        <div className="mt-6 flex flex-wrap items-center justify-center gap-4 text-[10px] font-mono text-zinc-500">
          <div className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-success pulse-dot" />
            <span>TLS 1.3 End-to-End</span>
          </div>
          <span>•</span>
          <div>Zero-Knowledge Keys</div>
          <span>•</span>
          <div>ISO 27001 Compliant</div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 w-full py-6 text-center text-xs text-muted-foreground border-t border-white/5">
        <p>© 2026 Proteus Security Intelligence Platform. Authorized personnel only.</p>
      </footer>
    </div>
  );
}
