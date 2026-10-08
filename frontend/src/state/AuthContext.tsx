import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { getToken, setToken, setUnauthorizedHandler } from "../api/tokenStore";
import type { User, UserRole } from "../api/types";

// Mirrors the blueprint's Users & Roles table ("Can approve" column) — purely
// a client-side UX hint (hide/disable a button a role can't use anyway); the
// API enforces the real check server-side regardless (api/routers/approvals.py's
// APPROVER_ROLES), so this map going stale only means a worse error message,
// never a security gap.
export const APPROVE_PERMISSIONS: Record<UserRole, string[]> = {
  brand_manager: ["market_landscape", "research_gap", "persona", "journey_map", "persona_assignment", "competitor", "message_map", "early_warning_signal"],
  brand_marketing_head: ["brand_plan"],
  insights_analytics_lead: ["segment", "channel", "channel_fit", "channel_plan", "outcome", "scorecard", "lift_estimate", "prior_update", "assumption_review"],
  sales_ops_field_excellence: ["segment", "adoption_state", "target_list", "journey_rule", "action"],
  medical_mlr_reviewer: ["content_module", "message_map"],
  market_country_lead: ["brand_plan", "channel_plan"],
  platform_admin: [], // handled separately — admin can approve anything
  viewer: [],
  external_reviewer: [],
};

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (tenantName: string, name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  canApprove: (entityType: string) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  const logout = () => {
    setToken(null);
    setUser(null);
    navigate("/login");
  };

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setToken(null);
      setUser(null);
    });
  }, []);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setIsLoading(false);
      return;
    }
    api
      .get<User>("/auth/me")
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setIsLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const resp = await api.post<{ access_token: string; user: User }>("/auth/login", { email, password });
    setToken(resp.access_token);
    setUser(resp.user);
  };

  const signup = async (tenantName: string, name: string, email: string, password: string) => {
    const resp = await api.post<{ access_token: string; user: User }>("/auth/signup", {
      tenant_name: tenantName, name, email, password,
    });
    setToken(resp.access_token);
    setUser(resp.user);
  };

  const canApprove = (entityType: string) => {
    if (!user) return false;
    if (user.role === "platform_admin") return true;
    return (APPROVE_PERMISSIONS[user.role] ?? []).includes(entityType);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, signup, logout, canApprove }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export const ROLE_LABELS: Record<UserRole, string> = {
  brand_manager: "Brand manager",
  brand_marketing_head: "Brand / marketing head",
  insights_analytics_lead: "Insights & analytics lead",
  sales_ops_field_excellence: "Sales operations / field excellence",
  medical_mlr_reviewer: "Medical / MLR reviewer",
  market_country_lead: "Market / country lead",
  platform_admin: "Platform admin",
  viewer: "Viewer",
  external_reviewer: "External reviewer",
};
