import { useParams } from "react-router-dom";
import type { ReactNode } from "react";
import { AlertTriangle, Target } from "lucide-react";
import { useApprovals } from "../../api/hooks";
import { useAuth, APPROVE_PERMISSIONS, ROLE_LABELS } from "../../state/AuthContext";
import { approverRolesFor, stageById, type Stage } from "../../domain/stages";
import { Badge, SectionHeading } from "./ui";

/* Every stage page opens the same way: the decision it drives, who signs it
 * off, and whether anything it stands on is still a draft.
 *
 * The decision line is the "why NUDGE" — a brand lead landing here should see
 * what question this page answers before they see a single number.
 */

export function StageHeader({
  stageId,
  right,
  children,
}: {
  stageId: string;
  right?: ReactNode;
  children?: ReactNode;
}) {
  const { brandId } = useParams();
  const { user } = useAuth();
  const { data: approvals } = useApprovals(brandId);
  const stage = stageById(stageId);
  if (!stage) return null;

  const approvers = approverRolesFor(stage, APPROVE_PERMISSIONS);
  const youCanApprove =
    user?.role === "platform_admin" || (user ? approvers.includes(user.role) : false);

  // An entity type still showing drafts in the approvals inbox hasn't been
  // signed off yet. No draft rows == nothing outstanding for that type.
  const draftTypes = new Set(
    (approvals ?? []).filter((a) => a.draft_count > 0).map((a) => a.entity_type),
  );
  const pendingUpstream = stage.upstream
    .map(stageById)
    .filter((s): s is Stage => !!s)
    .filter((s) => s.entityTypes.some((t) => draftTypes.has(t)));

  return (
    <>
      <SectionHeading
        eyebrow={`${stage.ix} · ${stage.group}`}
        title={stage.label}
        sub={stage.shows}
        right={right}
      />

      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          gap: 10,
          borderLeft: "3px solid var(--gold)",
          background: "var(--gold-light)",
          borderRadius: "var(--radius-sm)",
          padding: "12px 16px",
          marginBottom: 18,
        }}
      >
        <Target size={14} strokeWidth={2.4} style={{ color: "var(--gold-muted)", flexShrink: 0, marginTop: 2 }} />
        <div style={{ minWidth: 0, flex: 1 }}>
          <div
            style={{
              fontSize: 10,
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.07em",
              color: "var(--gold-muted)",
              marginBottom: 3,
            }}
          >
            The decision this drives
          </div>
          <div style={{ fontSize: 13.5, lineHeight: 1.55, color: "var(--text-1)", fontWeight: 600 }}>
            {stage.decision}
          </div>
        </div>
        {approvers.length > 0 && (
          <div style={{ flexShrink: 0, textAlign: "right" }}>
            <div
              style={{
                fontSize: 10,
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.07em",
                color: "var(--gold-muted)",
                marginBottom: 4,
              }}
            >
              Signed off by
            </div>
            <div style={{ display: "flex", gap: 5, flexWrap: "wrap", justifyContent: "flex-end" }}>
              {approvers.map((r) => (
                <Badge key={r} color={user?.role === r ? "navy" : "neutral"}>
                  {ROLE_LABELS[r]}
                </Badge>
              ))}
            </div>
            {!youCanApprove && (
              <div style={{ fontSize: 10.5, color: "var(--text-3)", marginTop: 4 }}>
                You are {ROLE_LABELS[user?.role ?? "viewer"]} — view only here
              </div>
            )}
          </div>
        )}
      </div>

      {pendingUpstream.length > 0 && (
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: 10,
            borderLeft: "3px solid var(--amber)",
            background: "var(--amber-bg)",
            borderRadius: "var(--radius-sm)",
            padding: "12px 16px",
            marginBottom: 18,
          }}
        >
          <AlertTriangle size={14} strokeWidth={2.4} style={{ color: "var(--amber-text)", flexShrink: 0, marginTop: 2 }} />
          <div style={{ fontSize: 13, lineHeight: 1.6, color: "var(--text-2)" }}>
            <strong style={{ color: "var(--amber-text)" }}>Built on drafts.</strong>{" "}
            {pendingUpstream.map((s) => s.label).join(", ")}{" "}
            {pendingUpstream.length === 1 ? "has" : "have"} unapproved output. These results will
            change if it is revised before sign-off.
          </div>
        </div>
      )}

      {children}
    </>
  );
}
