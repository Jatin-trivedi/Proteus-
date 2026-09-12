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
  const { login, register, isAuthenticated, user, logout } = useAuth();

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
        toast.success("Signed In Successfully", {
          description: `Welcome back, Operator ${username}. Your session has been established.`,
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
        toast.success("Account Created Successfully", {
          description: `Clearance granted for ${username} [${role.toUpperCase()}]. Welcome to Proteus.`,
        });
        navigate({ to: "/" });
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Authentication failed. Verify credentials.");
      toast.error("Authentication Failed", {
        description: err.message || "Invalid operator credentials. Please check your username and passphrase.",
      });
    } finally {
      setIsLoading(false);
    }
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

          {/* Error Notification Box (Light Mode, Pure White, High Contrast) */}
          {errorMessage && (
            <div className="mb-4 p-3.5 rounded-xl bg-white text-zinc-900 border border-red-200 border-l-4 border-l-red-500 text-xs flex items-start gap-2.5 shadow-[0_10px_25px_rgba(0,0,0,0.45)]">
              <div className="p-1 rounded-md bg-red-100 text-red-600 shrink-0 mt-0.5">
                <AlertCircle className="h-4 w-4" />
              </div>
              <div className="flex-1">
                <span className="font-bold text-zinc-950 block text-[13px]">Authentication Notice</span>
                <span className="text-zinc-600 leading-relaxed text-[12px]">{errorMessage}</span>
              </div>
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
