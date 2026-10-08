import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type {
  Action,
  AdoptionState,
  ApprovalCount,
  AssumptionReview,
  Brand,
  BrandPlan,
  Channel,
  ChannelFit,
  ChannelPlan,
  Competitor,
  ContentModule,
  DraftRow,
  EarlyWarningSignal,
  Evidence,
  Job,
  JourneyMap,
  JourneyRule,
  LiftEstimate,
  MarketLandscape,
  MessageMap,
  Outcome,
  Pack,
  Persona,
  QuestionBankCoverage,
  PilotPair,
  PriorUpdate,
  ResearchGap,
  ReviewDecision,
  RunRecord,
  Scorecard,
  Segment,
  SystemStatus,
  TargetList,
  Tenant,
  UploadInfo,
  User,
} from "./types";

// ---- auth ------------------------------------------------------------
// Login/signup themselves aren't exposed as hooks — the app authenticates
// silently on load (see AuthContext.tsx's bootstrap), not through a form.

export function useTeammates(tenantId: string | undefined) {
  return useQuery({
    queryKey: ["teammates", tenantId],
    queryFn: () => api.get<User[]>(`/tenants/${tenantId}/users`),
    enabled: !!tenantId,
  });
}
export function useCreateTeammate(tenantId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { name: string; email: string; password: string; role: string }) =>
      api.post<User>(`/tenants/${tenantId}/users`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["teammates", tenantId] }),
  });
}
export function useGrantBrandAccess(brandId: string | undefined) {
  return useMutation({
    mutationFn: (userId: string) => api.post(`/brands/${brandId}/access`, { user_id: userId }),
  });
}

// ---- system / brands -------------------------------------------------

export function useSystemStatus() {
  return useQuery({ queryKey: ["system-status"], queryFn: () => api.get<SystemStatus>("/system/status") });
}

export function useBrands(enabled: boolean) {
  return useQuery({ queryKey: ["brands"], queryFn: () => api.get<Brand[]>("/brands"), enabled });
}

export function useBrand(brandId: string | undefined) {
  return useQuery({
    queryKey: ["brands", brandId],
    queryFn: () => api.get<Brand>(`/brands/${brandId}`),
    enabled: !!brandId,
  });
}

export function useCreateBrand() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => api.post<Brand>("/brands", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["brands"] }),
  });
}

// ---- uploads / data hub ------------------------------------------------

export function useUploads(brandId: string | undefined) {
  return useQuery({
    queryKey: ["uploads", brandId],
    queryFn: () => api.get<UploadInfo[]>(`/brands/${brandId}/uploads`),
    enabled: !!brandId,
  });
}

export function useUploadFile(brandId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ kind, file }: { kind: string; file: File }) => {
      const form = new FormData();
      form.append("file", file);
      return api.postForm<UploadInfo>(`/brands/${brandId}/uploads/${kind}`, form);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["uploads", brandId] }),
  });
}

// ---- fast synchronous run-mutation + invalidate helper ------------------
// For endpoints that return their real result in well under a second (pure
// math, no LLM, no large loop) — see useJobRun below for the job-backed
// pattern genuinely long-running module runs use instead.

function useRunMutation<TBody, TResult>(brandId: string | undefined, path: string, invalidateKeys: string[][]) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: TBody) => api.post<TResult>(`/brands/${brandId}${path}`, body),
    onSuccess: () => {
      for (const key of invalidateKeys) qc.invalidateQueries({ queryKey: [...key, brandId] });
      qc.invalidateQueries({ queryKey: ["approvals", brandId] });
    },
  });
}

// ---- job-backed run pattern ----------------------------------------------
// POST returns {job_id} immediately (202); we poll GET /jobs/{id} until it
// settles, then invalidate the relevant entity queries. This is what
// M1/M2/M3(x4)/M4/M5/M6/M7/M8-outcomes use — the actually long-running
// (LLM-backed, or large-loop) module runs. See api/jobs.py's own docstring
// for why this is "DB-tracked status + polling," not a durable task queue.

function useJobRun<TBody>(brandId: string | undefined, path: string, invalidateKeys: string[][]) {
  const qc = useQueryClient();
  const [jobId, setJobId] = useState<string | null>(null);

  const startMutation = useMutation({
    mutationFn: (body: TBody) => api.post<Job>(`/brands/${brandId}${path}`, body),
    onSuccess: (job) => setJobId(job.id),
  });

  const jobQuery = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => api.get<Job>(`/jobs/${jobId}`),
    enabled: !!jobId,
    refetchInterval: (q) => {
      const status = q.state.data?.status;
      return status === "pending" || status === "running" ? 700 : false;
    },
  });

  const job = jobQuery.data;
  const settled = job?.status === "done" || job?.status === "failed";

  useEffect(() => {
    if (!settled) return;
    for (const key of invalidateKeys) qc.invalidateQueries({ queryKey: [...key, brandId] });
    qc.invalidateQueries({ queryKey: ["approvals", brandId] });
    qc.invalidateQueries({ queryKey: ["jobs", brandId] });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [settled, job?.id]);

  return {
    mutate: (body: TBody) => {
      setJobId(null);
      startMutation.mutate(body);
    },
    isPending: startMutation.isPending || (!!jobId && !settled),
    error: startMutation.error ?? (job?.status === "failed" ? new Error(job.error ?? "job failed") : null),
    job,
  };
}

export function useJobsForBrand(brandId: string | undefined) {
  return useQuery({
    queryKey: ["jobs", brandId],
    queryFn: () => api.get<Job[]>(`/brands/${brandId}/jobs`),
    enabled: !!brandId,
  });
}

// ---- M1 ----------------------------------------------------------------

export function useRunM1(brandId: string | undefined) {
  return useJobRun<Record<string, never>>(brandId, "/m1/run", [["market-landscape"], ["evidence"], ["research-gaps"]]);
}
export function useMarketLandscape(brandId: string | undefined) {
  return useQuery({
    queryKey: ["market-landscape", brandId],
    queryFn: () => api.get<MarketLandscape | null>(`/brands/${brandId}/m1/market-landscape`),
    enabled: !!brandId,
  });
}
export function useEvidence(brandId: string | undefined) {
  return useQuery({
    queryKey: ["evidence", brandId],
    queryFn: () => api.get<Evidence[]>(`/brands/${brandId}/m1/evidence`),
    enabled: !!brandId,
  });
}
export function useQuestionBank(brandId: string | undefined) {
  return useQuery({
    queryKey: ["question-bank", brandId],
    queryFn: () => api.get<QuestionBankCoverage>(`/brands/${brandId}/m1/question-bank`),
    enabled: !!brandId,
  });
}

export function useResearchGaps(brandId: string | undefined) {
  return useQuery({
    queryKey: ["research-gaps", brandId],
    queryFn: () => api.get<ResearchGap[]>(`/brands/${brandId}/m1/research-gaps`),
    enabled: !!brandId,
  });
}

// ---- M2 ------------------------------------------------------------------

export function useRunM2(brandId: string | undefined) {
  return useJobRun<{ target_share: number }>(brandId, "/m2/run", [["segments"], ["adoption-states"], ["target-lists"]]);
}
export function useSegments(brandId: string | undefined) {
  return useQuery({
    queryKey: ["segments", brandId],
    queryFn: () => api.get<Segment[]>(`/brands/${brandId}/m2/segments`),
    enabled: !!brandId,
  });
}
export function useAdoptionStates(brandId: string | undefined) {
  return useQuery({
    queryKey: ["adoption-states", brandId],
    queryFn: () => api.get<AdoptionState[]>(`/brands/${brandId}/m2/adoption-states`),
    enabled: !!brandId,
  });
}
export function useTargetLists(brandId: string | undefined) {
  return useQuery({
    queryKey: ["target-lists", brandId],
    queryFn: () => api.get<TargetList[]>(`/brands/${brandId}/m2/target-lists`),
    enabled: !!brandId,
  });
}

// ---- M3 --------------------------------------------------------------------

export function useRunM3Synthetic(brandId: string | undefined) {
  return useJobRun<{ persona_count: number }>(brandId, "/m3/run-synthetic", [["personas"], ["journey-maps"]]);
}
export function useRunM3CallNotes(brandId: string | undefined) {
  return useJobRun<Record<string, never>>(brandId, "/m3/run-call-notes", [["personas"], ["journey-maps"]]);
}
export function useRunM3Survey(brandId: string | undefined) {
  return useJobRun<Record<string, never>>(brandId, "/m3/run-survey", [["personas"], ["journey-maps"]]);
}
export function useRunM3Social(brandId: string | undefined) {
  return useJobRun<Record<string, never>>(brandId, "/m3/run-social", [["personas"], ["journey-maps"]]);
}
export function usePersonas(brandId: string | undefined) {
  return useQuery({
    queryKey: ["personas", brandId],
    queryFn: () => api.get<Persona[]>(`/brands/${brandId}/m3/personas`),
    enabled: !!brandId,
  });
}
export function useJourneyMaps(brandId: string | undefined) {
  return useQuery({
    queryKey: ["journey-maps", brandId],
    queryFn: () => api.get<JourneyMap[]>(`/brands/${brandId}/m3/journey-maps`),
    enabled: !!brandId,
  });
}

// ---- M4 -----------------------------------------------------------------

export function useRunM4(brandId: string | undefined) {
  return useJobRun<Record<string, never>>(brandId, "/m4/run", [["competitors"], ["message-map"], ["early-warning-signals"]]);
}
export function useCompetitors(brandId: string | undefined) {
  return useQuery({
    queryKey: ["competitors", brandId],
    queryFn: () => api.get<Competitor[]>(`/brands/${brandId}/m4/competitors`),
    enabled: !!brandId,
  });
}
export function useMessageMap(brandId: string | undefined) {
  return useQuery({
    queryKey: ["message-map", brandId],
    queryFn: () => api.get<MessageMap | null>(`/brands/${brandId}/m4/message-map`),
    enabled: !!brandId,
  });
}
export function useEarlyWarningSignals(brandId: string | undefined) {
  return useQuery({
    queryKey: ["early-warning-signals", brandId],
    queryFn: () => api.get<EarlyWarningSignal[]>(`/brands/${brandId}/m4/early-warning-signals`),
    enabled: !!brandId,
  });
}

// ---- M5 --------------------------------------------------------------------

export function useRunM5(brandId: string | undefined) {
  return useJobRun<{ net_price: number; budget_envelope: number | null; plan_horizon_months: number; require_approval: boolean }>(
    brandId, "/m5/run", [["brand-plan"]],
  );
}
export function useBrandPlan(brandId: string | undefined) {
  return useQuery({
    queryKey: ["brand-plan", brandId],
    queryFn: () => api.get<BrandPlan | null>(`/brands/${brandId}/m5/brand-plan`),
    enabled: !!brandId,
  });
}

// ---- M6 -----------------------------------------------------------------

export function useRunM6(brandId: string | undefined) {
  return useJobRun<{ budget_envelope: number; rep_count: number | null }>(
    brandId, "/m6/run", [["channels"], ["channel-fits"], ["channel-plan"]],
  );
}
export function useChannels(brandId: string | undefined) {
  return useQuery({
    queryKey: ["channels", brandId],
    queryFn: () => api.get<Channel[]>(`/brands/${brandId}/m6/channels`),
    enabled: !!brandId,
  });
}
export function useChannelFits(brandId: string | undefined) {
  return useQuery({
    queryKey: ["channel-fits", brandId],
    queryFn: () => api.get<ChannelFit[]>(`/brands/${brandId}/m6/channel-fits`),
    enabled: !!brandId,
  });
}
export function useChannelPlan(brandId: string | undefined) {
  return useQuery({
    queryKey: ["channel-plan", brandId],
    queryFn: () => api.get<ChannelPlan | null>(`/brands/${brandId}/m6/channel-plan`),
    enabled: !!brandId,
  });
}

// ---- M7 -----------------------------------------------------------------

export function useRunM7(brandId: string | undefined) {
  return useJobRun<{ rep_count: number | null }>(brandId, "/m7/run", [["journey-rules"], ["actions"], ["content-modules"]]);
}
export function useJourneyRules(brandId: string | undefined) {
  return useQuery({
    queryKey: ["journey-rules", brandId],
    queryFn: () => api.get<JourneyRule[]>(`/brands/${brandId}/m7/journey-rules`),
    enabled: !!brandId,
  });
}
export function useActions(brandId: string | undefined) {
  return useQuery({
    queryKey: ["actions", brandId],
    queryFn: () => api.get<Action[]>(`/brands/${brandId}/m7/actions`),
    enabled: !!brandId,
  });
}
export function useContentModules(brandId: string | undefined) {
  return useQuery({
    queryKey: ["content-modules", brandId],
    queryFn: () => api.get<ContentModule[]>(`/brands/${brandId}/m7/content-modules`),
    enabled: !!brandId,
  });
}

// ---- M8 -----------------------------------------------------------------

export function useRunM8Outcomes(brandId: string | undefined) {
  return useJobRun<{ period: string }>(brandId, "/m8/run-outcomes", [["outcomes"], ["scorecard"]]);
}
export function useOutcomes(brandId: string | undefined) {
  return useQuery({
    queryKey: ["outcomes", brandId],
    queryFn: () => api.get<Outcome[]>(`/brands/${brandId}/m8/outcomes`),
    enabled: !!brandId,
  });
}
export function useScorecard(brandId: string | undefined) {
  return useQuery({
    queryKey: ["scorecard", brandId],
    queryFn: () => api.get<Scorecard | null>(`/brands/${brandId}/m8/scorecard`),
    enabled: !!brandId,
  });
}
export function useRunLiftTestDid(brandId: string | undefined) {
  return useRunMutation<{ test_name: string; test_deltas: number[]; control_deltas: number[] }, LiftEstimate>(
    brandId, "/m8/lift-tests/did", [["lift-estimates"]],
  );
}
export function useRunLiftTestNational(brandId: string | undefined) {
  return useRunMutation<{ test_name: string; pre_values: number[]; post_values: number[] }, LiftEstimate>(
    brandId, "/m8/lift-tests/national", [["lift-estimates"]],
  );
}
export function useLiftEstimates(brandId: string | undefined) {
  return useQuery({
    queryKey: ["lift-estimates", brandId],
    queryFn: () => api.get<LiftEstimate[]>(`/brands/${brandId}/m8/lift-estimates`),
    enabled: !!brandId,
  });
}
export function useRunPriorUpdate(brandId: string | undefined) {
  return useRunMutation<{ rung: string; successes: number; trials: number; period: string; pseudo_count: number }, PriorUpdate>(
    brandId, "/m8/prior-updates", [["prior-updates"]],
  );
}
export function usePriorUpdates(brandId: string | undefined) {
  return useQuery({
    queryKey: ["prior-updates", brandId],
    queryFn: () => api.get<PriorUpdate[]>(`/brands/${brandId}/m8/prior-updates`),
    enabled: !!brandId,
  });
}
export function useRunAssumptionReview(brandId: string | undefined) {
  return useRunMutation<{ period: string; actual_values: Record<string, number> }, AssumptionReview>(
    brandId, "/m8/assumption-reviews", [["assumption-reviews"]],
  );
}
export function useAssumptionReviews(brandId: string | undefined) {
  return useQuery({
    queryKey: ["assumption-reviews", brandId],
    queryFn: () => api.get<AssumptionReview[]>(`/brands/${brandId}/m8/assumption-reviews`),
    enabled: !!brandId,
  });
}
export function useRunPilotDesign(brandId: string | undefined) {
  return useMutation({
    mutationFn: (body: { effect_size: number; std: number; power: number; alpha: number }) =>
      api.post<{ required_sample_size_per_arm: number }>(`/brands/${brandId}/m8/pilot-design`, body),
  });
}
export function useRunPilotMatching(brandId: string | undefined) {
  return useMutation({
    mutationFn: () => api.post<PilotPair[]>(`/brands/${brandId}/m8/pilot-matching`, {}),
  });
}

// ---- approvals ------------------------------------------------------------

export function useApprovals(brandId: string | undefined) {
  return useQuery({
    queryKey: ["approvals", brandId],
    queryFn: () => api.get<ApprovalCount[]>(`/brands/${brandId}/approvals`),
    enabled: !!brandId,
  });
}
export function useDraftRows(brandId: string | undefined, entityType: string | null) {
  return useQuery({
    queryKey: ["approvals", brandId, entityType],
    queryFn: () => api.get<DraftRow[]>(`/brands/${brandId}/approvals/${entityType}`),
    enabled: !!brandId && !!entityType,
  });
}
export function useApproveAll(brandId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (entityType: string) =>
      api.post<{ approved_count: number }>(`/brands/${brandId}/approvals/${entityType}/approve-all`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["approvals", brandId] }),
  });
}
export function useDecideOne(brandId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ entityType, objectId, decision, comment }: { entityType: string; objectId: string; decision: "approved" | "rejected"; comment?: string }) =>
      api.post<ReviewDecision>(`/brands/${brandId}/approvals/${entityType}/${objectId}/decide`, { decision, comment }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["approvals", brandId] });
      qc.invalidateQueries({ queryKey: ["review-decisions", brandId] });
    },
  });
}
export function useReviewDecisions(brandId: string | undefined) {
  return useQuery({
    queryKey: ["review-decisions", brandId],
    queryFn: () => api.get<ReviewDecision[]>(`/brands/${brandId}/approvals/_review-decisions`),
    enabled: !!brandId,
  });
}

// ---- ask nudge --------------------------------------------------------

export function useAskNudge(brandId: string | undefined) {
  return useMutation({
    mutationFn: (question: string) => api.post<{ answer: string }>(`/brands/${brandId}/ask`, { question }),
  });
}

// ---- admin ----------------------------------------------------------------

export function usePack(market: string | undefined) {
  return useQuery({
    queryKey: ["pack", market],
    queryFn: () => api.get<Pack>(`/packs/${market}`),
    enabled: !!market,
  });
}
export function useRunRecords(enabled: boolean) {
  return useQuery({ queryKey: ["run-records"], queryFn: () => api.get<RunRecord[]>("/run-records"), enabled });
}

export type { Tenant };
