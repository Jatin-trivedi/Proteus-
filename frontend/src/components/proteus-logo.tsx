import React from "react";
import { cn } from "@/lib/utils";
import logoWhite from "@/assets/proteus-logo.png";
import logoDark from "@/assets/proteus-logo-transparent.png";

interface ProteusLogoProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  size?: "xs" | "sm" | "md" | "lg" | "xl" | "2xl" | number;
  variant?: "icon" | "full" | "horizontal";
  subtitle?: string;
  glow?: boolean;
  theme?: "white" | "dark";
}

const sizeMap = {
  xs: 20,
  sm: 28,
  md: 36,
  lg: 48,
  xl: 64,
  "2xl": 96,
};

/**
 * Proteus Logo / Icon Image Component
 * Uses white logo for dark UI and dark logo for light UI.
 */
export function ProteusIcon({
  size = "md",
  className,
  glow = false,
  theme = "white",
  alt = "Proteus Logo",
  src,
  ...props
}: Omit<ProteusLogoProps, "variant" | "subtitle">) {
  const dimension = typeof size === "number" ? size : sizeMap[size] || 36;
  const logoSrc = src ?? (theme === "dark" ? logoDark : logoWhite);

  return (
    <img
      src={logoSrc}
      alt={alt}
      width={dimension}
      height={dimension}
      className={cn(
        "shrink-0 object-contain block transition-transform duration-300",
        glow && "drop-shadow-[0_0_12px_rgba(56,189,248,0.55)]",
        className
      )}
      style={{ width: dimension, height: dimension, minWidth: dimension, minHeight: dimension }}
      {...props}
    />
  );
}

/**
 * Full Proteus Brand Component
 */
export function ProteusLogo({
  variant = "horizontal",
  size = "md",
  className,
  subtitle = "Forensic & Compliance Intelligence",
  glow = true,
  theme = "white",
  ...props
}: ProteusLogoProps) {
  if (variant === "icon") {
    return <ProteusIcon size={size} className={className} glow={glow} theme={theme} {...props} />;
  }

  if (variant === "full") {
    return (
      <div className={cn("flex flex-col items-center text-center group", className)}>
        <ProteusIcon
          size={size === "md" ? "xl" : size}
          theme={theme}
          className="mb-3 transition-transform group-hover:scale-105"
          glow={glow}
          {...props}
        />
        <span className="text-2xl font-black tracking-[0.25em] text-foreground font-sans uppercase">
          PROTEUS
        </span>
        {subtitle && (
          <span className="mt-1 text-[10px] uppercase tracking-[0.22em] text-muted-foreground font-medium">
            {subtitle}
          </span>
        )}
      </div>
    );
  }

  // Horizontal variant (for Navbar & Headers)
  return (
    <div className={cn("flex items-center gap-3 group", className)}>
      <div className="relative grid place-items-center rounded-xl bg-white/[0.04] p-1.5 border border-white/10 glow-cyber group-hover:border-primary/50 group-hover:bg-primary/[0.06] transition-all duration-300">
        <ProteusIcon
          size={size}
          theme={theme}
          className="transition-transform group-hover:scale-105"
          glow={glow}
          {...props}
        />
        <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-primary pulse-dot" />
      </div>
      <div className="flex flex-col">
        <span className="text-lg font-black tracking-[0.16em] text-white font-sans leading-none select-none">
          PRO<span className="text-primary font-black">TEUS</span>
        </span>
        {subtitle && (
          <span className="text-[9px] uppercase tracking-[0.2em] text-zinc-400 font-medium whitespace-nowrap mt-1">
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );
}

export default ProteusLogo;
