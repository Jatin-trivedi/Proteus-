import { useEffect, useState } from "react";

import { ProteusIcon } from "@/components/proteus-logo";
import { useAuth } from "@/lib/auth-context";

const MINIMUM_DISPLAY_TIME = 700;

export function AppLoader() {
  const { isLoading: isAuthLoading } = useAuth();
  const [minimumTimeElapsed, setMinimumTimeElapsed] = useState(false);
  const [isVisible, setIsVisible] = useState(true);
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => setMinimumTimeElapsed(true), MINIMUM_DISPLAY_TIME);

    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (isAuthLoading || !minimumTimeElapsed) return;

    setIsExiting(true);
    const timer = window.setTimeout(() => setIsVisible(false), 450);

    return () => window.clearTimeout(timer);
  }, [isAuthLoading, minimumTimeElapsed]);

  if (!isVisible) return null;

  return (
    <div
      aria-label="Loading Proteus"
      aria-live="polite"
      className={`app-loader${isExiting ? " app-loader--exit" : ""}`}
      role="status"
    >
      <div className="app-loader__aura" />
      <div className="app-loader__mark">
        <span className="app-loader__ring app-loader__ring--outer" />
        <span className="app-loader__ring app-loader__ring--inner" />
        <ProteusIcon size={72} theme="white" glow alt="Proteus" />
      </div>
      <div className="app-loader__wordmark">PROTEUS</div>
      <div className="app-loader__status">Initializing secure console</div>
      <div className="app-loader__progress" aria-hidden="true">
        <span />
      </div>
    </div>
  );
}