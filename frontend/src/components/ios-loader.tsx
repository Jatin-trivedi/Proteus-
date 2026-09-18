import React, { useEffect, useState } from "react";
import { useRouterState } from "@tanstack/react-router";
import { ProteusIcon } from "@/components/proteus-logo";
import { cn } from "@/lib/utils";

/**
 * Authentic Apple / iPhone 12-Blade Activity Spinner
 */
export function IOSSpinner({
  size = "md",
  className,
  color = "white",
}: {
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
  color?: "white" | "purple" | "muted";
}) {
  const sizeClass = {
    sm: "w-5 h-5",
    md: "w-8 h-8",
    lg: "w-11 h-11",
    xl: "w-16 h-16",
  }[size];

  const bladeColor = {
    white: "bg-white",
    purple: "bg-[#C084FC]",
    muted: "bg-zinc-400",
  }[color];

  return (
    <div className={cn("relative inline-block", sizeClass, className)} aria-label="Loading">
      {Array.from({ length: 12 }).map((_, i) => {
        const rotation = i * 30;
        const delay = -1 + (i * 1) / 12;
        return (
          <div
            key={i}
            className="absolute left-[45%] top-[10%] w-[10%] h-[28%] rounded-full origin-[50%_145%]"
            style={{
              transform: `rotate(${rotation}deg)`,
              animation: `ios-spinner-fade 1s linear infinite`,
              animationDelay: `${delay}s`,
            }}
          >
            <div className={cn("w-full h-full rounded-full shadow-sm", bladeColor)} />
          </div>
        );
      })}
    </div>
  );
}

/**
 * Full-screen iPhone / Apple Style Loading Screen
 * Triggers on initial app boot and route navigations.
 */
export function IOSLoadingScreen() {
  const [initialLoading, setInitialLoading] = useState(true);
  const [customLoading, setCustomLoading] = useState(false);
  const [progress, setProgress] = useState(15);
  const [visible, setVisible] = useState(true);

  const isNavigating = useRouterState({ select: (s) => s.isLoading });

  // Handle Initial Application Boot
  useEffect(() => {
    // Smooth progress simulation like iOS boot/update screen
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) return prev;
        const step = Math.floor(Math.random() * 18) + 8;
        return Math.min(prev + step, 92);
      });
    }, 120);

    const onWindowLoaded = () => {
      setProgress(100);
      setTimeout(() => {
        setInitialLoading(false);
        setTimeout(() => setVisible(false), 500);
      }, 350);
    };

    if (document.readyState === "complete") {
      onWindowLoaded();
    } else {
      window.addEventListener("load", onWindowLoaded);
    }

    // Custom event listener for triggering loader from anywhere
    const handleCustomLoading = (e: Event) => {
      const customEvent = e as CustomEvent<{ loading: boolean }>;
      if (customEvent.detail?.loading !== undefined) {
        setCustomLoading(customEvent.detail.loading);
        if (customEvent.detail.loading) {
          setVisible(true);
        }
      }
    };

    window.addEventListener("proteus:loading" as any, handleCustomLoading);

    return () => {
      clearInterval(interval);
      window.removeEventListener("load", onWindowLoaded);
      window.removeEventListener("proteus:loading" as any, handleCustomLoading);
    };
  }, []);

  const showOverlay = initialLoading || customLoading || isNavigating;

  if (!visible && !showOverlay) {
    return null;
  }

  return (
    <>
      {/* Top iOS Glowing Linear Progress Line for background navigation */}
      <div
        className={cn(
          "fixed top-0 left-0 right-0 h-[2.5px] z-[999999] pointer-events-none transition-all duration-300",
          isNavigating ? "opacity-100" : "opacity-0"
        )}
      >
        <div className="h-full w-full bg-gradient-to-r from-transparent via-[#A855F7] to-[#E879F9] animate-pulse shadow-[0_0_12px_#A855F7]" />
      </div>

      {/* Full-Screen iPhone Style Loading Screen */}
      <div
        className={cn(
          "fixed inset-0 z-[999990] flex flex-col items-center justify-center bg-[#08090C] select-none transition-opacity duration-500 ease-out",
          showOverlay
            ? "opacity-100 pointer-events-auto"
            : "opacity-0 pointer-events-none"
        )}
        style={{
          backdropFilter: "blur(40px)",
          WebkitBackdropFilter: "blur(40px)",
        }}
      >
        {/* Ambient Apple-style dark gradient glow */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_45%,rgba(168,85,247,0.12)_0%,transparent_70%)] pointer-events-none" />

        {/* Center Container: Minimalist Emblem + iOS Loading Bar */}
        <div className="relative z-10 flex flex-col items-center max-w-xs w-full px-6 text-center space-y-8 animate-in fade-in zoom-in-95 duration-400">
          {/* Logo / Emblem */}
          <div className="relative flex items-center justify-center">
            <div className="absolute -inset-4 rounded-full bg-[#A855F7]/20 blur-xl animate-pulse" />
            <ProteusIcon
              size={72}
              className="relative drop-shadow-[0_0_24px_rgba(168,85,247,0.6)] animate-pulse"
            />
          </div>

          {/* iPhone Apple OS Style Progress Bar */}
          <div className="w-48 sm:w-56 space-y-3">
            <div className="h-[4.5px] w-full rounded-full bg-white/[0.12] overflow-hidden p-[0.5px]">
              <div
                className="h-full rounded-full bg-white transition-all duration-300 ease-out shadow-[0_0_10px_rgba(255,255,255,0.8)]"
                style={{ width: `${initialLoading ? progress : isNavigating ? 75 : 100}%` }}
              />
            </div>

            {/* Subtle iOS Spinner + Status */}
            <div className="flex items-center justify-center gap-2.5 pt-1 text-[11px] font-sans text-zinc-400 font-medium tracking-wide">
              <IOSSpinner size="sm" color="purple" />
              <span>Initializing Proteus...</span>
            </div>
          </div>
        </div>

        {/* Bottom subtle iOS footer */}
        <div className="absolute bottom-10 inset-x-0 text-center text-[10px] font-mono tracking-widest text-zinc-600 uppercase">
          Autonomous Forensic Intelligence · Security Grid
        </div>
      </div>
    </>
  );
}

/**
 * Helper function to trigger the iPhone loader programmatically from anywhere
 */
export function setGlobalLoader(loading: boolean) {
  if (typeof window !== "undefined") {
    window.dispatchEvent(
      new CustomEvent("proteus:loading", { detail: { loading } })
    );
  }
}
