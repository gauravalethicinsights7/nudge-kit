import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { CheckCheck, Inbox } from "lucide-react";
import { useApprovals, useApproveAll, useDecideOne, useDraftRows, useReviewDecisions } from "../api/hooks";
import { useAuth } from "../state/AuthContext";
import { ApiError } from "../api/client";
import { ChartCard } from "../components/charts/ChartCard";
import { BarChart } from "../components/charts/BarChart";
import { DetailModal } from "../components/shared/DetailModal";
import {
  Badge,
  Card,
  EmptyState,
  MetricStat,
  TableWrap,
} from "../components/shared/ui";
import { StageHeader } from "../components/shared/StageHeader";

function EntityRows({ brandId, entityType }: { brandId: string; entityType: string }) {
  const { data: rows, isLoading } = useDraftRows(brandId, entityType);
  const decide = useDecideOne(brandId);
  const { canApprove, user } = useAuth();
  const allowed = canApprove(entityType);
  const [comments, setComments] = useState<Record<string, string>>({});

  if (isLoading) return <p style={{ fontSize: 12.5, color: "var(--text-3)" }}>Loading…</p>;
  if (!rows?.length) return <EmptyState sub="No draft rows." />;

  return (
    <>
      <TableWrap minWidth={620}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Created</th>
            <th>Comment</th>
            <th>Decision</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td style={{ fontSize: 11.5 }}>{r.id.slice(0, 8)}</td>
              <td style={{ fontSize: 11.5 }}>{new Date(r.created_at).toLocaleString()}</td>
              <td>
                <input
                  type="text"
                  placeholder="optional comment"
                  value={comments[r.id] ?? ""}
                  onChange={(e) => setComments((c) => ({ ...c, [r.id]: e.target.value }))}
                  style={{ fontSize: 11.5, width: 170 }}
                />
              </td>
              <td style={{ whiteSpace: "nowrap" }}>
                <button
                  className="btn-small btn-navy"
                  disabled={!allowed || decide.isPending}
                  title={allowed ? undefined : `${user?.role} cannot approve ${entityType}`}
                  onClick={() => decide.mutate({ entityType, objectId: r.id, decision: "approved", comment: comments[r.id] })}
                >
                  Approve
                </button>{" "}
                <button
                  className="btn-small btn-ghost"
                  disabled={!allowed || decide.isPending}
                  title={allowed ? undefined : `${user?.role} cannot reject ${entityType}`}
                  onClick={() => decide.mutate({ entityType, objectId: r.id, decision: "rejected", comment: comments[r.id] })}
                >
                  Reject
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </TableWrap>
      {decide.error && (
        <p style={{ fontSize: 11.5, color: "var(--red-text)", marginTop: 10 }}>
          {decide.error instanceof ApiError ? decide.error.detail : String(decide.error)}
        </p>
      )}
    </>
  );
}

export function Approvals() {
  const { brandId } = useParams();
  const { data: approvals, isLoading } = useApprovals(brandId);
  const { data: decisions } = useReviewDecisions(brandId);
  const approveAll = useApproveAll(brandId);
  const { canApprove, user } = useAuth();
  const [expanded, setExpanded] = useState<string | null>(null);

  const backlogData = useMemo(
    () => (approvals ?? []).map((a) => ({ entity_type: a.entity_type, count: a.draft_count })).sort((a, b) => b.count - a.count),
    [approvals],
  );
  const totalPending = approvals?.reduce((sum, a) => sum + a.draft_count, 0) ?? 0;

  return (
    <div>
      <StageHeader stageId="appr" />

      <div className="grid grid-3" style={{ marginBottom: 22 }}>
        <Card style={{ margin: 0 }}>
          <MetricStat label="Drafts pending" value={totalPending} tone={totalPending ? "gold" : "emerald"} />
        </Card>
        <Card style={{ margin: 0 }}>
          <MetricStat label="Entity types" value={backlogData.length} />
        </Card>
        <Card style={{ margin: 0 }}>
          <MetricStat label="Decisions logged" value={decisions?.length ?? 0} />
        </Card>
      </div>

      {!!backlogData.length && (
        <>
          <ChartCard
            title="Approval backlog"
            subtitle={`${totalPending} drafts pending across ${backlogData.length} entity types`}
            height={Math.max(140, backlogData.length * 30)}
          >
            <BarChart
              data={backlogData}
              x="entity_type"
              y="count"
              horizontal
              valueFormatter={(v) => v.toFixed(0)}
              height={Math.max(140, backlogData.length * 30)}
            />
          </ChartCard>
          <div style={{ height: 22 }} />
        </>
      )}

      <Card title="Pending approvals" sub="Review the draft rows, or approve a whole entity type at once">
        {isLoading ? (
          <p style={{ fontSize: 12.5, color: "var(--text-3)" }}>Loading…</p>
        ) : !approvals?.length ? (
          <EmptyState
            icon={<CheckCheck size={28} strokeWidth={1.6} />}
            title="Nothing pending"
            sub="Everything is already approved — downstream modules can read it in production."
          />
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 14 }}>
            {approvals.map((a) => {
              const allowed = canApprove(a.entity_type);
              return (
                <div
                  key={a.entity_type}
                  style={{
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-sm)",
                    padding: 16,
                    display: "flex",
                    flexDirection: "column",
                    gap: 14,
                  }}
                >
                  <MetricStat label={a.entity_type} value={a.draft_count} sub="drafts awaiting review" />
                  <div style={{ display: "flex", gap: 8 }}>
                    <button className="btn-small btn-ghost" onClick={() => setExpanded(a.entity_type)}>
                      Review rows
                    </button>
                    <button
                      className="btn-small btn-navy"
                      disabled={!allowed || approveAll.isPending}
                      title={allowed ? undefined : `${user?.role} cannot approve ${a.entity_type}`}
                      onClick={() => approveAll.mutate(a.entity_type)}
                    >
                      Approve all
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      <Card title="Review decision history" sub="The audit trail behind every approval and rejection">
        {decisions?.length ? (
          <TableWrap minWidth={720}>
            <thead>
              <tr>
                <th>Entity type</th>
                <th>Object</th>
                <th>Decision</th>
                <th>Comment</th>
                <th>When</th>
              </tr>
            </thead>
            <tbody>
              {decisions.slice(0, 50).map((d) => (
                <tr key={d.id}>
                  <td>{d.entity_type}</td>
                  <td style={{ fontSize: 11.5 }}>{d.object_id.slice(0, 8)}</td>
                  <td>
                    <Badge color={d.decision === "approved" ? "emerald" : "red"}>{d.decision}</Badge>
                  </td>
                  <td style={{ fontSize: 11.5 }}>{d.comment ?? "—"}</td>
                  <td style={{ fontSize: 11.5 }}>{new Date(d.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </TableWrap>
        ) : (
          <EmptyState icon={<Inbox size={24} strokeWidth={1.6} />} sub="No decisions recorded yet." />
        )}
      </Card>

      <DetailModal
        open={!!expanded}
        onClose={() => setExpanded(null)}
        eyebrow="Draft rows"
        title={expanded ?? ""}
        width={880}
      >
        {expanded && brandId && <EntityRows brandId={brandId} entityType={expanded} />}
      </DetailModal>
    </div>
  );
}
