import React, { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { ApiError, apiFetch } from "@/lib/api";

export type UserRole = "admin" | "lead_investigator" | "analyst" | "auditor";

export interface User {
  user_id: string;
  username: string;
  role: UserRole | string;
  created_at?: string;
}

interface AuthResponse {
  user: User;
  access_token: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<User>;
  register: (username: string, password: string, role?: string) => Promise<User>;
  loginDemo: (role?: UserRole) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const DEMO_USER_KEY = "proteus_demo_user";
const SESSION_USER_KEY = "proteus_session_user";
const TOKEN_KEY = "access_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check localStorage for existing session
    const storedToken = localStorage.getItem(TOKEN_KEY);
    const storedDemo = localStorage.getItem(DEMO_USER_KEY);
    const storedSessionUser = localStorage.getItem(SESSION_USER_KEY);

    if (storedToken === "demo-session-token" && storedDemo) {
      try {
        setToken(storedToken);
        setUser(JSON.parse(storedDemo) as User);
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(DEMO_USER_KEY);
      }
      setIsLoading(false);
    } else if (storedToken) {
      setToken(storedToken);
      if (storedSessionUser) {
        try {
          setUser(JSON.parse(storedSessionUser) as User);
        } catch {
          localStorage.removeItem(SESSION_USER_KEY);
        }
      }
      // Attempt to load current user profile from backend
      apiFetch<User>("/auth/me")
        .then((userData) => {
          localStorage.setItem(SESSION_USER_KEY, JSON.stringify(userData));
          setUser(userData);
        })
        .catch((error: unknown) => {
          // Only an explicit auth rejection invalidates the saved session.
          if (error instanceof ApiError && [401, 404].includes(error.status)) {
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(SESSION_USER_KEY);
            localStorage.removeItem(DEMO_USER_KEY);
            setToken(null);
            setUser(null);
          }
        })
        .finally(() => {
          setIsLoading(false);
        });
    } else {
      localStorage.removeItem(DEMO_USER_KEY);
      setIsLoading(false);
    }
  }, []);

  const login = async (username: string, password: string): Promise<User> => {
    const data = await apiFetch<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(SESSION_USER_KEY, JSON.stringify(data.user));
    localStorage.removeItem(DEMO_USER_KEY);
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  };

  const register = async (username: string, password: string, role = "analyst"): Promise<User> => {
    const data = await apiFetch<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, password, role }),
    });
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(SESSION_USER_KEY, JSON.stringify(data.user));
    localStorage.removeItem(DEMO_USER_KEY);
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  };

  const loginDemo = (role: UserRole = "lead_investigator") => {
    const demoProfiles: Record<UserRole, User> = {
      admin: {
        user_id: "sec-admin-01",
        username: "operator_admin",
        role: "admin",
      },
      lead_investigator: {
        user_id: "inv-lead-09",
        username: "lead_investigator",
        role: "lead_investigator",
      },
      analyst: {
        user_id: "forensic-an-42",
        username: "forensic_analyst",
        role: "analyst",
      },
      auditor: {
        user_id: "compliance-aud-03",
        username: "soc2_auditor",
        role: "auditor",
      },
    };

    const selectedUser = demoProfiles[role] || demoProfiles.lead_investigator;
    localStorage.setItem(TOKEN_KEY, "demo-session-token");
    localStorage.setItem(DEMO_USER_KEY, JSON.stringify(selectedUser));
    localStorage.removeItem(SESSION_USER_KEY);
    setToken("demo-session-token");
    setUser(selectedUser);
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(SESSION_USER_KEY);
    localStorage.removeItem(DEMO_USER_KEY);
    setUser(null);
    setToken(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        loginDemo,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
