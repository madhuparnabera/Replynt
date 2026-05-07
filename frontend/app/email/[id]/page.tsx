"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { AlertCard } from "@/components/AlertCard";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { PriorityBadge } from "@/components/PriorityBadge";
import { IntentTag } from "@/components/IntentTag";
import { TaskCard } from "@/components/TaskCard";
import { useToast } from "@/components/ToastProvider";
import { explainEmail } from "@/lib/api";
import { formatScore } from "@/lib/format";
import { supabase } from "@/lib/supabase";
import type { Alert, Commitment, DraftReply, Email } from "@/lib/types";

function normalizeEmailId(value?: string | null) {
  return (value ?? "")
    .replace(/^email_id\s*→\s*/i, "")
    .replace(/^=/, "")
    .trim();
}

function emailIdCandidates(routeEmailId: string, email?: Email | null) {
  const normalized = normalizeEmailId(email?.email_id || routeEmailId);
  return Array.from(
    new Set(
      [routeEmailId, email?.email_id, normalized, `=${normalized}`, `email_id → ${normalized}`]
        .filter(Boolean)
        .map((value) => String(value).trim())
    )
  );
}

export default function EmailDetailPage() {
  const params = useParams<{ id: string }>();
  const emailId = decodeURIComponent(params.id);
  const { notify } = useToast();
  const emailRef = useRef<Email | null>(null);
  const [email, setEmail] = useState<Email | null>(null);
  const [commitments, setCommitments] = useState<Commitment[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [drafts, setDrafts] = useState<DraftReply[]>([]);
  const [draftBody, setDraftBody] = useState("");
  const [explanation, setExplanation] = useState("");
  const [loading, setLoading] = useState(true);
  const [draftsLoading, setDraftsLoading] = useState(false);
  const [working, setWorking] = useState(false);

  const loadDrafts = useCallback(
    async ({ notifyOnSuccess = false, emailRecord = emailRef.current }: { notifyOnSuccess?: boolean; emailRecord?: Email | null } = {}) => {
      setDraftsLoading(true);
      const candidates = emailIdCandidates(emailId, emailRecord);
      const { data, error } = await supabase
        .from("draft_replies")
        .select("*")
        .in("email_id", candidates)
        .order("created_at", { ascending: false });

      setDraftsLoading(false);

      if (error) {
        notify("Unable to refresh drafts", "error");
        return;
      }

      const nextDrafts = (data ?? []) as DraftReply[];
      setDrafts(nextDrafts);
      setDraftBody(nextDrafts[0]?.draft_body ?? "");

      if (notifyOnSuccess) {
        notify(nextDrafts.length ? "Drafts refreshed" : "No drafts found yet", "success");
      }
    },
    [emailId, notify]
  );

  useEffect(() => {
    let active = true;
    async function load() {
      const candidates = emailIdCandidates(emailId);
      const [emailResult, commitmentResult, alertResult] = await Promise.all([
        supabase.from("emails").select("*").in("email_id", candidates).limit(1).maybeSingle(),
        supabase.from("commitments").select("*").in("email_id", candidates).order("deadline", { ascending: true, nullsFirst: false }),
        supabase.from("alerts").select("*").in("email_id", candidates).order("id", { ascending: false })
      ]);
      if (!active) return;
      const nextEmail = (emailResult.data ?? null) as Email | null;
      emailRef.current = nextEmail;
      setEmail(nextEmail);
      setCommitments((commitmentResult.data ?? []) as Commitment[]);
      setAlerts((alertResult.data ?? []) as Alert[]);
      await loadDrafts({ emailRecord: nextEmail });
      setLoading(false);
    }
    load();
    const channel = supabase
      .channel(`email-${emailId}`)
      .on("postgres_changes", { event: "*", schema: "public", table: "draft_replies" }, () => loadDrafts())
      .on("postgres_changes", { event: "*", schema: "public", table: "commitments", filter: `email_id=eq.${emailId}` }, load)
      .on("postgres_changes", { event: "*", schema: "public", table: "alerts", filter: `email_id=eq.${emailId}` }, load)
      .subscribe();
    return () => {
      active = false;
      supabase.removeChannel(channel);
    };
  }, [emailId, loadDrafts]);

  async function handleCopy() {
    await navigator.clipboard.writeText(draftBody);
    notify("Draft copied", "success");
  }

  async function handleExplain() {
    if (!email) return;
    setWorking(true);
    try {
      const result = await explainEmail({ email_id: email.email_id, body: email.body, summary: email.summary });
      setExplanation(result);
      notify("Explanation loaded", "success");
    } catch {
      notify("Explain request failed", "error");
    } finally {
      setWorking(false);
    }
  }

  if (loading) return <LoadingState label="Loading email intelligence..." />;
  if (!email) return <EmptyState title="Email not found" description="No record matched this email_id in Supabase." />;

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_24rem]">
      <div className="space-y-6">
        <section className="rounded-xl border border-line bg-panel p-5">
          <div className="flex flex-wrap items-center gap-2">
            <PriorityBadge priority={email.priority} />
            <IntentTag intent={email.intent} />
            <span className="rounded-full border border-slate-500/30 bg-canvas px-2.5 py-1 text-xs text-slate-300">Risk {formatScore(email.risk_score)}</span>
          </div>
          <h1 className="mt-4 text-2xl font-semibold text-white">{email.subject}</h1>
          <p className="mt-2 text-sm text-slate-400">{email.sender}</p>
          <div className="mt-5 rounded-xl border border-line bg-canvas p-4 text-sm leading-7 text-slate-300 whitespace-pre-wrap">{email.body}</div>
        </section>
        <section className="rounded-xl border border-line bg-panel p-5">
          <h2 className="font-semibold text-white">Summary</h2>
          <p className="mt-3 text-sm leading-6 text-slate-300">{email.summary || "No AI summary yet."}</p>
          {explanation ? <div className="mt-4 rounded-xl border border-blue-500/30 bg-blue-500/10 p-4 text-sm leading-6 text-blue-100">{explanation}</div> : null}
        </section>
        <section className="rounded-xl border border-line bg-panel p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="font-semibold text-white">AI draft reply</h2>
              <p className="mt-1 text-xs text-slate-500">Synced from Supabase draft_replies</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button onClick={() => loadDrafts({ notifyOnSuccess: true })} disabled={draftsLoading} className="rounded-xl bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-60">
                {draftsLoading ? "Refreshing..." : "Refresh drafts"}
              </button>
              <button onClick={handleExplain} disabled={working} className="rounded-xl border border-line px-3 py-2 text-sm text-slate-200 hover:border-blue-500/50">Explain</button>
              <button onClick={handleCopy} disabled={!draftBody.trim()} className="rounded-xl border border-line px-3 py-2 text-sm text-slate-200 hover:border-blue-500/50 disabled:opacity-50">Copy</button>
            </div>
          </div>
          {draftBody ? (
            <textarea
              value={draftBody}
              readOnly
              className="mt-4 min-h-72 w-full resize-y rounded-xl border border-line bg-canvas p-4 text-sm leading-7 text-slate-100 outline-none focus:border-blue-500/70"
            />
          ) : (
            <div className="mt-4">
              <EmptyState title="No draft replies yet" description="When n8n inserts a generated reply into Supabase, it will appear here automatically." />
            </div>
          )}
          <div className="mt-2 text-xs text-slate-500">
            {drafts.length ? `Showing latest of ${drafts.length} draft${drafts.length === 1 ? "" : "s"}` : "Waiting for generated drafts"}
          </div>
        </section>
      </div>
      <aside className="space-y-6">
        <section className="rounded-xl border border-line bg-panel p-5">
          <h2 className="font-semibold text-white">Commitments</h2>
          <div className="mt-4 space-y-3">
            {commitments.length ? commitments.map((task) => <TaskCard key={task.id} task={task} />) : <EmptyState title="No commitments" description="Extracted tasks for this email appear here." />}
          </div>
        </section>
        <section className="rounded-xl border border-line bg-panel p-5">
          <h2 className="font-semibold text-white">Alerts</h2>
          <div className="mt-4 space-y-3">
            {alerts.length ? alerts.map((alert) => <AlertCard key={alert.id} alert={alert} />) : <EmptyState title="No alerts" description="This email has no open alerts." />}
          </div>
        </section>
        <section className="rounded-xl border border-line bg-panel p-5">
          <h2 className="font-semibold text-white">Previous drafts</h2>
          <div className="mt-4 space-y-3">
            {drafts.length ? (
              drafts.map((draft) => (
                <button key={draft.id} onClick={() => setDraftBody(draft.draft_body)} className="w-full rounded-xl border border-line bg-canvas p-3 text-left text-sm text-slate-300 hover:border-blue-500/40">
                  <div className="truncate font-medium text-white">{draft.subject}</div>
                  <div className="mt-1 text-[11px] text-slate-500">{new Date(draft.created_at).toLocaleString()}</div>
                  <div className="mt-2 line-clamp-3 text-xs leading-5 text-slate-400">{draft.draft_body}</div>
                </button>
              ))
            ) : (
              <EmptyState title="No drafts yet" description="Saved generated replies will be listed here." />
            )}
          </div>
        </section>
      </aside>
    </div>
  );
}
