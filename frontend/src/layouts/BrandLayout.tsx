import { Link, NavLink, Outlet, useLocation, useParams } from "react-router-dom";
import {
  BarChart3, BookOpen, Database, GitBranch, Inbox, LayoutDashboard,
  Layers, Radio, ScrollText, Swords, Target, Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useBrand } from "../api/hooks";
import { Breadcrumbs } from "../components/Breadcrumbs";
import { AvatarInitials } from "../components/shared/ui";

const NAV: { section: string; items: { to: string; label: string; icon: LucideIcon }[] }[] = [
  { section: "Understand the market", items: [
    { to: "", label: "Overview", icon: LayoutDashboard },
    { to: "data-hub", label: "Data Hub", icon: Database },
    { to: "market-landscape", label: "Market Landscape", icon: BarChart3 },
    { to: "evidence", label: "Evidence Library", icon: BookOpen },
  ]},
  { section: "Know the doctors", items: [
    { to: "segments", label: "Segments & Targeting", icon: Layers },
    { to: "personas", label: "Personas & Journeys", icon: Users },
    { to: "competitive", label: "Competitive Map", icon: Swords },
  ]},
  { section: "Decide the plan", items: [
    { to: "brand-plan", label: "Brand Plan", icon: ScrollText },
    { to: "channel-planner", label: "Channel Planner", icon: Radio },
  ]},
  { section: "Act and learn", items: [
    { to: "orchestration", label: "Orchestration & NBA", icon: GitBranch },
    { to: "measurement", label: "Measurement", icon: Target },
  ]},
  { section: "Governance", items: [
    { to: "approvals", label: "Approvals Inbox", icon: Inbox },
  ]},
];

const ALL_ITEMS = NAV.flatMap((g) => g.items);

export function BrandLayout() {
  const { brandId } = useParams();
  const { data: brand } = useBrand(brandId);
  const location = useLocation();

  const currentSegment = location.pathname.split(`/brands/${brandId}/`)[1] ?? "";
  const currentItem = ALL_ITEMS.find((i) => i.to === currentSegment) ?? ALL_ITEMS[0];

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

        {NAV.map((group) => (
          <div key={group.section}>
            <div className="sidebar-section">{group.section}</div>
            {group.items.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={`/brands/${brandId}/${item.to}`}
                  end={item.to === ""}
                  className={({ isActive }) => (isActive ? "active" : "")}
                >
                  <Icon size={14} strokeWidth={2} style={{ flexShrink: 0 }} />
                  <span className="nav-label">{item.label}</span>
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
              { label: currentItem?.label ?? "Overview" },
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
