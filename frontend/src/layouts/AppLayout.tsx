import { Link, Outlet } from "react-router-dom";
import { LogOut, Settings } from "lucide-react";
import { useSystemStatus } from "../api/hooks";
import { useAuth, ROLE_LABELS } from "../state/AuthContext";
import { AskNudgePanel } from "../components/AskNudgePanel";
import { AvatarInitials } from "../components/shared/ui";

export function AppLayout() {
  const { data: status } = useSystemStatus();
  const { user, logout } = useAuth();

  return (
    <div>
      <div className="topbar">
        <div className="topbar-left">
          <Link to="/" className="topbar-brand">
            <span className="topbar-brand-mark">N</span>
            <span className="wordmark">NUDGE Omnichannel</span>
          </Link>
        </div>
        <div className="topbar-right">
          {status && (
            <span
              className="status-pill-group"
              title="Controls whether the LLM-dependent modules can run"
            >
              <span className={`status-dot ${status.anthropic_configured ? "on" : ""}`} />
              Anthropic
              <span className={`status-dot ${status.serper_configured ? "on" : ""}`} />
              Serper
            </span>
          )}
          <Link to="/admin" className="btn btn-small btn-ghost">
            <Settings size={13} style={{ marginRight: 5, verticalAlign: "-2px" }} />
            Admin
          </Link>
          {user && (
            <span style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <AvatarInitials text={user.name} size={28} />
              <span style={{ display: "flex", flexDirection: "column", lineHeight: 1.25 }}>
                <span style={{ fontSize: 12.5, fontWeight: 600, color: "var(--text-1)" }}>{user.name}</span>
                <span style={{ fontSize: 10.5, color: "var(--text-3)" }}>{ROLE_LABELS[user.role]}</span>
              </span>
              <button className="btn-small btn-ghost" onClick={logout} title="Log out">
                <LogOut size={13} />
              </button>
            </span>
          )}
        </div>
      </div>
      <Outlet />
      <AskNudgePanel />
    </div>
  );
}
