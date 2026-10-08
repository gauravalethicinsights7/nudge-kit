import { Link, NavLink, Outlet, useLocation, useParams } from "react-router-dom";
import {
  BarChart3, BookOpen, Database, GitBranch, Inbox, LayoutDashboard,
  Layers, Radio, ScrollText, Swords, Target, Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useApprovals, useBrand } from "../api/hooks";
import { Breadcrumbs } from "../components/Breadcrumbs";
import { AvatarInitials } from "../components/shared/ui";
import { STAGES, STAGE_GROUPS, stageById } from "../domain/stages";

const ICONS: Record<string, LucideIcon> = {
  overview: LayoutDashboard,
  data: Database,
  m1: BarChart3,
  evidence: BookOpen,
  m2: Layers,
  m3: Users,
  m4: Swords,
  m5: ScrollText,
  m6: Radio,
  m7: GitBranch,
  m8: Target,
  appr: Inbox,
};

export function BrandLayout() {
  const { brandId } = useParams();
  const { data: brand } = useBrand(brandId);
  const { data: approvals } = useApprovals(brandId);
  const location = useLocation();

  const currentSegment = location.pathname.split(`/brands/${brandId}/`)[1] ?? "";
  const currentStage = STAGES.find((s) => s.route === currentSegment) ?? STAGES[0];

  // Draft counts come from the approvals inbox, so the rail shows the same
  // truth the governance page does rather than a second opinion.
  const draftCounts = new Map((approvals ?? []).map((a) => [a.entity_type, a.draft_count]));
  const pendingTotal = (approvals ?? []).reduce((n, a) => n + a.draft_count, 0);

  /** The approvals endpoint only reports entity types that still have drafts,
   *  so absence means "nothing outstanding" — which is NOT the same as
   *  "approved": a module that never ran also has nothing outstanding. The
   *  rail says only what it can actually tell, and the Command centre (which
   *  does query each module) is where "has data" is established. */
  const statusOf = (stageId: string): "clear" | "draft" => {
    const stage = stageById(stageId);
    if (!stage?.entityTypes.length) return "clear";
    return stage.entityTypes.some((t) => (draftCounts.get(t) ?? 0) > 0) ? "draft" : "clear";
  };

  const DOT: Record<string, string> = {
    draft: "var(--amber)",
    clear: "var(--emerald)",
  };
  const DOT_TITLE: Record<string, string> = {
    draft: "Has output waiting for sign-off",
    clear: "Nothing waiting for sign-off",
  };

  return (
    <div className="app-shell">
      <nav className="sidebar">
        <Link to={`/brands/${brandId}`} className="sidebar-brand">
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <AvatarInitials text={brand?.name ?? "—"} size={32} gold />
            <div style={{ minWidth: 0 }}>
              <div className="sidebar-brand-name">{brand ? brand.name : "Loading…"}</div>
              {brand && (
                <div className="sidebar-brand-meta">
                  {brand.market.toUpperCase()} &middot; {brand.molecule}
                </div>
              )}
            </div>
          </div>
        </Link>

        {STAGE_GROUPS.map((group) => (
          <div key={group}>
            <div className="sidebar-section">{group}</div>
            {STAGES.filter((s) => s.group === group).map((stage) => {
              const Icon = ICONS[stage.id] ?? LayoutDashboard;
              const st = statusOf(stage.id);
              return (
                <NavLink
                  key={stage.id}
                  to={`/brands/${brandId}/${stage.route}`}
                  end={stage.route === ""}
                  className={({ isActive }) => (isActive ? "active" : "")}
                  title={stage.decision}
                >
                  <Icon size={14} strokeWidth={2} style={{ flexShrink: 0 }} />
                  <span className="nav-label" style={{ flex: 1, minWidth: 0 }}>
                    {stage.label}
                  </span>
                  {stage.id === "appr" && pendingTotal > 0 ? (
                    <span
                      title={`${pendingTotal} drafts awaiting review`}
                      style={{
                        background: "var(--gold)",
                        color: "var(--navy)",
                        borderRadius: 9,
                        fontSize: 10,
                        fontWeight: 700,
                        padding: "1px 6px",
                        flexShrink: 0,
                      }}
                    >
                      {pendingTotal > 999 ? "999+" : pendingTotal}
                    </span>
                  ) : stage.entityTypes.length ? (
                    <span
                      title={DOT_TITLE[st]}
                      style={{
                        width: 7,
                        height: 7,
                        borderRadius: "50%",
                        background: DOT[st],
                        flexShrink: 0,
                      }}
                    />
                  ) : null}
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="main-area">
        <div className="topbar" style={{ height: 46, padding: "0 var(--page-pad-x)" }}>
          <Breadcrumbs
            items={[
              { label: "Portfolio", to: "/" },
              { label: brand?.name ?? "Brand", to: `/brands/${brandId}` },
              { label: currentStage?.label ?? "Overview" },
            ]}
          />
        </div>
        <div className="page">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
