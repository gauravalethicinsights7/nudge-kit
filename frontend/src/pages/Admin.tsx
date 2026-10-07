import { useMemo, useState } from "react";
import { Settings2, ShieldCheck, Users2 } from "lucide-react";
import { useCreateTeammate, usePack, useRunRecords, useSystemStatus, useTeammates } from "../api/hooks";
import { useAuth, ROLE_LABELS } from "../state/AuthContext";
import { USER_ROLES } from "../api/types";
import { ApiError } from "../api/client";
import { ChartCard } from "../components/charts/ChartCard";
import { BarChart } from "../components/charts/BarChart";
import {
  AccentCallout,
  Badge,
  Card,
  EmptyState,
  MetricStat,
  MicroLabel,
  SectionHeading,
  TableWrap,
} from "../components/shared/ui";

function UsersPanel() {
  const { user } = useAuth();
  const isAdmin = user?.role === "platform_admin";
  const { data: teammates } = useTeammates(isAdmin ? user?.tenant_id : undefined);
  const createTeammate = useCreateTeammate(user?.tenant_id);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "insights_analytics_lead" });

  if (!isAdmin) {
    return (
      <Card title="Users" style={{ margin: 0 }}>
        <EmptyState
          icon={<Users2 size={24} strokeWidth={1.6} />}
          sub={`Only a platform admin can manage users. You are signed in as ${ROLE_LABELS[user?.role ?? "viewer"]}.`}
        />
      </Card>
    );
  }

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    createTeammate.mutate(form, {
      onSuccess: () => {
        setShowForm(false);
        setForm({ name: "", email: "", password: "", role: "insights_analytics_lead" });
      },
    });
  };

  return (
    <Card
      title="Users"
      sub={`${teammates?.length ?? 0} people in this tenant`}
      right={
        <button className="btn-small btn-ghost" onClick={() => setShowForm((s) => !s)}>
          {showForm ? "Cancel" : "Add teammate"}
        </button>
      }
      style={{ margin: 0 }}
    >
      {showForm && (
        <form onSubmit={submit} style={{ marginBottom: 18, paddingBottom: 16, borderBottom: "1px solid var(--border)" }}>
          <div className="grid grid-2">
            <div className="form-row">
              <label>Name</label>
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div className="form-row">
              <label>Email</label>
              <input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>
            <div className="form-row">
              <label>Temporary password</label>
              <input type="password" required minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
            </div>
            <div className="form-row">
              <label>Role</label>
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                {USER_ROLES.filter((r) => r !== "platform_admin").map((r) => (
                  <option key={r} value={r}>{ROLE_LABELS[r]}</option>
                ))}
              </select>
            </div>
          </div>
          {createTeammate.error && (
            <p style={{ color: "var(--red-text)", fontSize: 12 }}>
              {createTeammate.error instanceof ApiError ? createTeammate.error.detail : String(createTeammate.error)}
            </p>
          )}
          <button className="btn-navy" type="submit" disabled={createTeammate.isPending}>
            {createTeammate.isPending ? "Adding…" : "Add teammate"}
          </button>
        </form>
      )}

      {teammates?.length ? (
        <TableWrap minWidth={460}>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
            </tr>
          </thead>
          <tbody>
            {teammates.map((t) => (
              <tr key={t.id}>
                <td style={{ fontWeight: 600 }}>{t.name}</td>
                <td>{t.email}</td>
                <td>
                  <Badge color="navySoft">{ROLE_LABELS[t.role]}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </TableWrap>
      ) : (
        <EmptyState icon={<Users2 size={24} strokeWidth={1.6} />} sub="No teammates yet." />
      )}

      <p style={{ fontSize: 11.5, color: "var(--text-3)", marginTop: 14 }}>
        A new teammate sees no brands until you grant access from a brand's Overview page.
      </p>
    </Card>
  );
}

export function Admin() {
  const { user } = useAuth();
  const { data: status } = useSystemStatus();
  const { data: runRecords } = useRunRecords(user?.role === "platform_admin");
  const [market, setMarket] = useState("india");
  const { data: pack } = usePack(market);

  const costByModule = useMemo(() => {
    if (!runRecords?.length) return [];
    const totals = new Map<string, number>();
    for (const r of runRecords) totals.set(r.module, (totals.get(r.module) ?? 0) + r.cost);
    return Array.from(totals.entries())
      .map(([module, cost]) => ({ module, cost }))
      .sort((a, b) => b.cost - a.cost);
  }, [runRecords]);

  const totalCost = runRecords?.reduce((n, r) => n + r.cost, 0) ?? 0;
  const totalTokens = runRecords?.reduce((n, r) => n + r.tokens_in + r.tokens_out, 0) ?? 0;

  return (
    <div className="page" style={{ margin: "0 auto" }}>
      <SectionHeading
        eyebrow="Administration"
        title="Admin Console"
        sub="System status, users and access, market packs, and run-record cost history."
      />

      <div className="grid grid-4" style={{ marginBottom: 22 }}>
        <Card style={{ margin: 0 }}>
          <MetricStat label="Total LLM spend" value={`$${totalCost.toFixed(2)}`} tone="gold" />
        </Card>
        <Card style={{ margin: 0 }}>
          <MetricStat label="Tokens used" value={totalTokens.toLocaleString()} />
        </Card>
        <Card style={{ margin: 0 }}>
          <MetricStat label="Runs logged" value={runRecords?.length ?? 0} />
        </Card>
        <Card style={{ margin: 0 }}>
          <MetricStat label="Budget per run" value={`$${status?.run_budget_usd ?? "–"}`} sub="Hard cap" />
        </Card>
      </div>

      <div className="grid grid-2" style={{ marginBottom: 22, alignItems: "start" }}>
        <Card title="System status" sub="API keys the engine needs to run research modules" style={{ margin: 0 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 13, color: "var(--text-2)", fontWeight: 600 }}>Anthropic</span>
              <Badge color={status?.anthropic_configured ? "emerald" : "red"}>
                {status?.anthropic_configured ? "Configured" : "Not configured"}
              </Badge>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 13, color: "var(--text-2)", fontWeight: 600 }}>Serper (web search)</span>
              <Badge color={status?.serper_configured ? "emerald" : "red"}>
                {status?.serper_configured ? "Configured" : "Not configured"}
              </Badge>
            </div>
            <AccentCallout tone="navy" label="Run budget" icon={<ShieldCheck size={12} />}>
              Each module run is capped at ${status?.run_budget_usd ?? "–"} of LLM spend.
            </AccentCallout>
          </div>
        </Card>
        <UsersPanel />
      </div>

      <Card
        title="Market pack browser"
        sub="Read-only configuration — channels, caps and compliance rules come from the pack, never from code"
        right={
          <select value={market} onChange={(e) => setMarket(e.target.value)}>
            <option value="india">India</option>
            <option value="us">US</option>
          </select>
        }
      >
        {pack ? (
          <div className="grid grid-2" style={{ alignItems: "start" }}>
            <div>
              <MicroLabel>Channels ({pack.channels.length})</MicroLabel>
              <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 10 }}>
                {pack.channels.map((c) => (
                  <div
                    key={c.id}
                    style={{
                      padding: "10px 14px",
                      background: "var(--bg-raised)",
                      borderRadius: "var(--radius-sm)",
                    }}
                  >
                    <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-1)", marginBottom: 6 }}>
                      {c.name}
                    </div>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      <Badge color="neutral">Cost {c.unit_cost ?? "unset"}</Badge>
                      <Badge color="neutral">Cap {pack.frequency_caps[c.id] ?? "none"}</Badge>
                      {c.requires_consent && <Badge color="amber">Consent: {c.consent_field}</Badge>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <MicroLabel>Compliance rules ({pack.compliance_rules.length})</MicroLabel>
              <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 10 }}>
                {pack.compliance_rules.map((r) => (
                  <div key={r.id} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                    <Badge color={r.severity === "block" ? "red" : "amber"}>{r.severity}</Badge>
                    <span style={{ fontSize: 12.5, lineHeight: 1.6, color: "var(--text-2)" }}>{r.rule}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <EmptyState icon={<Settings2 size={24} strokeWidth={1.6} />} sub="Loading pack…" />
        )}
      </Card>

      {costByModule.length > 0 && (
        <>
          <ChartCard
            title="LLM cost by module"
            subtitle="Total spend per module across all runs"
            height={Math.max(140, costByModule.length * 30)}
          >
            <BarChart
              data={costByModule}
              x="module"
              y="cost"
              horizontal
              valueFormatter={(v) => `$${v.toFixed(2)}`}
              height={Math.max(140, costByModule.length * 30)}
            />
          </ChartCard>
          <div style={{ height: 22 }} />
        </>
      )}

      <Card title="Run record history" sub="Cost, tokens and duration for every logged module run">
        {!user || user.role !== "platform_admin" ? (
          <EmptyState sub="Only a platform admin can view run-record history." />
        ) : runRecords?.length ? (
          <TableWrap minWidth={720}>
            <thead>
              <tr>
                <th>Module</th>
                <th>Model</th>
                <th>Tokens in/out</th>
                <th>Cost</th>
                <th>Duration</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              {runRecords.map((r) => (
                <tr key={r.id}>
                  <td>
                    <Badge color="navySoft">{r.module}</Badge>
                  </td>
                  <td style={{ fontSize: 11.5 }}>{r.model}</td>
                  <td>
                    {r.tokens_in}/{r.tokens_out}
                  </td>
                  <td>${r.cost.toFixed(4)}</td>
                  <td>{r.duration_ms}ms</td>
                  <td>{r.error ? <Badge color="red">{r.error}</Badge> : "—"}</td>
                </tr>
              ))}
            </tbody>
          </TableWrap>
        ) : (
          <EmptyState sub="No runs logged yet — this fills in once the LLM-backed modules run." />
        )}
      </Card>
    </div>
  );
}
