import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export function MetricCard({
  title,
  value,
  delta,
  icon: Icon,
  tone = "cyber",
}: {
  title: string;
  value: string | number;
  delta?: string;
  icon: LucideIcon;
  tone?: "cyber" | "success" | "warning" | "destructive";
}) {
  const tones = {
    cyber: "text-primary bg-primary/10 border-primary/25",
    success: "text-success bg-success/10 border-success/25",
    warning: "text-warning bg-warning/10 border-warning/25",
    destructive: "text-destructive bg-destructive/10 border-destructive/25",
  } as const;

  return (
    <div className="panel p-6 flex items-start gap-4 transition-colors hover:border-primary/30">
      <div className={cn("grid h-11 w-11 shrink-0 place-items-center rounded-md border", tones[tone])}>
        <Icon className="h-5 w-5" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-[11px] font-mono uppercase tracking-widest text-muted-foreground">
          {title}
        </div>
        <div className="mt-2 text-3xl font-bold tabular-nums leading-none text-foreground">{value}</div>
        {delta && <div className="mt-2 text-xs text-muted-foreground">{delta}</div>}
      </div>
    </div>
  );
}
