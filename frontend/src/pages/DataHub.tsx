import { useRef } from "react";
import { useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, RefreshCw, Upload } from "lucide-react";
import { useUploadFile, useUploads } from "../api/hooks";
import { ApiError } from "../api/client";
import { Badge, Card, MetricStat, MicroLabel } from "../components/shared/ui";
import { StageHeader } from "../components/shared/StageHeader";
import { DataLevelPanel } from "../components/shared/DataLevelPanel";

const KINDS: { kind: string; label: string; hint: string; accept: string }[] = [
  { kind: "hcp_sample", label: "HCP sample", hint: "CSV: crm_id, specialty, setting, state, city, city_tier, territory_id, access, consent_email, consent_whatsapp", accept: ".csv" },
  { kind: "content_library", label: "Content library", hint: "YAML: modules with name, channel_refs, driver, claim, format and mlr_status", accept: ".yaml,.yml" },
  { kind: "engagement_events", label: "Engagement events", hint: "CSV: hcp_id, channel, depth, occurred_at, period", accept: ".csv" },
  { kind: "sales", label: "Rx / sales", hint: "CSV: hcp_id, period, nrx, trx", accept: ".csv" },
  { kind: "call_notes", label: "Call notes", hint: "CSV: note_id, crm_id, text", accept: ".csv" },
  { kind: "survey_responses", label: "Survey responses", hint: "CSV: respondent_id plus one column per rated item", accept: ".csv" },
  { kind: "social_posts", label: "Social posts", hint: "CSV: post_id, hcp_ref, text", accept: ".csv" },
];

function UploadRow({ brandId, kind, label, hint, accept }: { brandId: string; kind: string; label: string; hint: string; accept: string }) {
  const upload = useUploadFile(brandId);
  const { data: uploads } = useUploads(brandId);
  const existing = uploads?.find((u) => u.kind === kind);
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <Card
      style={{
        margin: 0,
        borderLeft: existing ? "3px solid var(--emerald)" : "3px solid var(--border-strong)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, marginBottom: 10 }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text-1)" }}>{label}</div>
          {existing ? (
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 6 }}>
              <CheckCircle2 size={13} style={{ color: "var(--emerald)" }} />
              <Badge color="emerald">{existing.row_count ?? "?"} rows uploaded</Badge>
            </div>
          ) : (
            <div style={{ marginTop: 6 }}>
              <Badge color="neutral">Not uploaded</Badge>
            </div>
          )}
        </div>
        <Upload size={15} style={{ color: "var(--text-3)", flexShrink: 0 }} />
      </div>

      <MicroLabel>Expected columns</MicroLabel>
      <p style={{ fontSize: 12, color: "var(--text-3)", lineHeight: 1.6, margin: "0 0 12px" }}>{hint}</p>

      <input
        ref={inputRef}
        type="file"
        accept={accept}
        style={{ fontSize: 12, width: "100%" }}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) upload.mutate({ kind, file });
        }}
      />
      {upload.isPending && <div style={{ fontSize: 11.5, color: "var(--text-3)", marginTop: 8 }}>Uploading…</div>}
      {upload.isError && (
        <div style={{ fontSize: 11.5, color: "var(--red-text)", marginTop: 8 }}>
          {upload.error instanceof ApiError ? upload.error.detail : String(upload.error)}
        </div>
      )}
    </Card>
  );
}

export function DataHub() {
  const { brandId } = useParams();
  const qc = useQueryClient();
  const { data: uploads } = useUploads(brandId);

  if (!brandId) return null;

  const uploadedCount = KINDS.filter((k) => uploads?.some((u) => u.kind === k.kind)).length;
  const totalRows = uploads?.reduce((n, u) => n + (u.row_count ?? 0), 0) ?? 0;

  return (
    <div>
      <StageHeader
        stageId="data"
                right={
          <button className="btn-ghost" onClick={() => qc.invalidateQueries({ queryKey: ["uploads", brandId] })}>
            <RefreshCw size={13} style={{ marginRight: 6, verticalAlign: "-2px" }} />
            Refresh
          </button>
        }
      />

      <div className="grid grid-3" style={{ marginBottom: 22 }}>
        <Card style={{ margin: 0 }}>
          <MetricStat
            label="Upload readiness"
            value={`${uploadedCount} / ${KINDS.length}`}
            sub={uploadedCount === KINDS.length ? "All file types uploaded" : `${KINDS.length - uploadedCount} remaining`}
            tone={uploadedCount === KINDS.length ? "emerald" : "navy"}
          />
        </Card>
        <Card style={{ margin: 0 }}>
          <MetricStat label="Rows ingested" value={totalRows.toLocaleString()} tone="gold" />
        </Card>
        <Card style={{ margin: 0 }}>
          <MetricStat label="File types" value={KINDS.length} sub="Supported by the engine" />
        </Card>
      </div>

      <DataLevelPanel uploads={uploads} />

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 16 }}>
        {KINDS.map((k) => (
          <UploadRow key={k.kind} brandId={brandId} {...k} />
        ))}
      </div>
    </div>
  );
}
