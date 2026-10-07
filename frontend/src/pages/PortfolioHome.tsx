import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Briefcase, Plus } from "lucide-react";
import { useBrands, useCreateBrand } from "../api/hooks";
import { StatusBadge } from "../components/Badge";
import { SkeletonKpiRow } from "../components/Skeleton";
import { useAuth } from "../state/AuthContext";
import {
  AvatarInitials,
  Badge,
  Card,
  EmptyState,
  MetricStat,
  MicroLabel,
  SectionHeading,
} from "../components/shared/ui";

const MARKETS = ["india", "us"];
const STAGES = ["pre_launch", "launch", "growth", "mature", "loe"];

export function PortfolioHome() {
  const { user } = useAuth();
  const { data: brands, isLoading } = useBrands(!!user);
  const createBrand = useCreateBrand();
  const navigate = useNavigate();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: "", molecule: "", indication: "", market: "india", lifecycle_stage: "launch", company: "",
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    createBrand.mutate(form, { onSuccess: (brand) => navigate(`/brands/${brand.id}`) });
  };

  const approved = brands?.filter((b) => b.status === "approved").length ?? 0;
  const draft = brands?.filter((b) => b.status === "draft").length ?? 0;
  const markets = new Set(brands?.map((b) => b.market)).size;

  return (
    <div className="page" style={{ margin: "0 auto" }}>
      <SectionHeading
        eyebrow="Portfolio"
        title="Brand Portfolio"
        sub="A brand and a market in — an approved, evidence-backed brand plan and activation plan out."
        right={
          <button className="btn-navy" onClick={() => setShowForm((s) => !s)}>
            {showForm ? "Cancel" : (
              <>
                <Plus size={14} style={{ marginRight: 6, verticalAlign: "-2px" }} />
                New brand
              </>
            )}
          </button>
        }
      />

      {isLoading ? (
        <SkeletonKpiRow count={3} />
      ) : brands?.length ? (
        <div className="grid grid-3" style={{ marginBottom: 22 }}>
          <Card style={{ margin: 0 }}>
            <MetricStat label="Brands in portfolio" value={brands.length} />
          </Card>
          <Card style={{ margin: 0 }}>
            <MetricStat label="Approved plans" value={approved} sub={`${draft} still in draft`} tone="emerald" />
          </Card>
          <Card style={{ margin: 0 }}>
            <MetricStat
              label="Markets"
              value={markets}
              sub={Array.from(new Set(brands.map((b) => b.market.toUpperCase()))).join(", ")}
              tone="gold"
            />
          </Card>
        </div>
      ) : null}

      {showForm && (
        <Card title="Create a brand" sub="The pack for the selected market supplies channels, costs and compliance rules">
          <form onSubmit={submit}>
            <div className="grid grid-2">
              <div className="form-row">
                <label>Brand name</label>
                <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </div>
              <div className="form-row">
                <label>Molecule</label>
                <input required value={form.molecule} onChange={(e) => setForm({ ...form, molecule: e.target.value })} />
              </div>
              <div className="form-row">
                <label>Indication</label>
                <input required value={form.indication} onChange={(e) => setForm({ ...form, indication: e.target.value })} />
              </div>
              <div className="form-row">
                <label>Company</label>
                <input required value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
              </div>
              <div className="form-row">
                <label>Market</label>
                <select value={form.market} onChange={(e) => setForm({ ...form, market: e.target.value })}>
                  {MARKETS.map((m) => <option key={m} value={m}>{m.toUpperCase()}</option>)}
                </select>
              </div>
              <div className="form-row">
                <label>Lifecycle stage</label>
                <select value={form.lifecycle_stage} onChange={(e) => setForm({ ...form, lifecycle_stage: e.target.value })}>
                  {STAGES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            </div>
            <button className="btn-navy" type="submit" disabled={createBrand.isPending}>
              {createBrand.isPending ? "Creating…" : "Create brand"}
            </button>
          </form>
        </Card>
      )}

      <Card title="Brands" sub="Select a brand to open its command centre">
        {isLoading ? (
          <p style={{ color: "var(--text-3)", fontSize: 13 }}>Loading…</p>
        ) : !brands?.length ? (
          <EmptyState
            icon={<Briefcase size={28} strokeWidth={1.6} />}
            title="No brands yet"
            sub="Create a brand to start building its evidence-backed plan, from market landscape through activation."
            action={
              <button className="btn-navy btn-small" onClick={() => setShowForm(true)}>
                Create your first brand
              </button>
            }
          />
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 16 }}>
            {brands.map((brand) => (
              <Link
                key={brand.id}
                to={`/brands/${brand.id}`}
                className="card"
                style={{ margin: 0, borderLeft: "3px solid var(--navy)" }}
              >
                <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                  <AvatarInitials text={brand.name} size={40} />
                  <div style={{ minWidth: 0, flex: 1 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "flex-start" }}>
                      <span style={{ fontSize: 15, fontWeight: 700, color: "var(--text-1)" }}>{brand.name}</span>
                      <StatusBadge status={brand.status} />
                    </div>
                    <div style={{ fontSize: 12.5, color: "var(--text-3)", marginTop: 4 }}>
                      {brand.molecule} · {brand.indication}
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: 14, paddingTop: 12, borderTop: "1px solid var(--border)" }}>
                  <MicroLabel>Market context</MicroLabel>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    <Badge color="navySoft">{brand.market.toUpperCase()}</Badge>
                    <Badge color="neutral">{brand.lifecycle_stage}</Badge>
                    <Badge color="neutral">{brand.company}</Badge>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
