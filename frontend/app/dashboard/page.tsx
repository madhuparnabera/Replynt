"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { PriorityBadge } from "@/components/PriorityBadge";
import { SectionHeader } from "@/components/SectionHeader";
import { TaskCard } from "@/components/TaskCard";
import { supabase } from "@/lib/supabase";
import type { Alert, Commitment, Email } from "@/lib/types";

export default function DashboardPage() {
  const [emails, setEmails] = useState<Email[]>([]);
  const [commitments, setCommitments] = useState<Commitment[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function load() {
      const [emailResult, commitmentResult, alertResult] = await Promise.all([
        supabase.from("emails").select("*").order("created_at", { ascending: false }),
        supabase.from("commitments").select("*").order("deadline", { ascending: true, nullsFirst: false }),
        supabase.from("alerts").select("*").eq("is_read", false)
      ]);
      if (!active) return;
      setEmails((emailResult.data ?? []) as Email[]);
      setCommitments((commitmentResult.data ?? []) as Commitment[]);
      setAlerts((alertResult.data ?? []) as Alert[]);
      setLoading(false);
    }

    load();
    const channel = supabase
      .channel("dashboard-realtime")
      .on("postgres_changes", { event: "*", schema: "public", table: "emails" }, load)
      .on("postgres_changes", { event: "*", schema: "public", table: "commitments" }, load)
      .on("postgres_changes", { event: "*", schema: "public", table: "alerts" }, load)
      .subscribe();

    return () => {
      active = false;
      supabase.removeChannel(channel);
    };
  }, []);

  const stats = useMemo(
    () => [
      { label: "Total emails", value: emails.length },
      { label: "Urgent emails", value: emails.filter((email) => email.priority === "P1").length },
      { label: "Pending commitments", value: commitments.filter((task) => task.status !== "done").length },
      { label: "Alerts count", value: alerts.length }
    ],
    [alerts.length, commitments, emails]
  );

  const urgentEmails = emails.filter((email) => email.priority === "P1").slice(0, 5);
  const upcoming = commitments.filter((task) => task.status !== "done").slice(0, 4);

  if (loading) return <LoadingState />;

  return (
    <div className="space-y-8">
      <SectionHeader eyebrow="Overview" title="Today in REPLYNT" />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-xl border border-line bg-panel p-5">
            <div className="text-sm text-slate-400">{stat.label}</div>
            <div className="mt-3 text-3xl font-semibold text-white">{stat.value}</div>
          </div>
        ))}
      </div>
      <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        <section className="rounded-xl border border-line bg-panel/60 p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-semibold text-white">Latest urgent emails</h2>
            <Link href="/inbox" className="text-sm text-blue-300 hover:text-blue-200">View inbox</Link>
          </div>
          <div className="space-y-3">
            {urgentEmails.length ? (
              urgentEmails.map((email) => (
                <Link key={email.id} href={`/email/${email.email_id}`} className="block rounded-xl border border-line bg-canvas p-4 hover:border-red-500/40">
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium text-white">{email.subject}</div>
                      <div className="mt-1 truncate text-xs text-slate-400">{email.sender}</div>
                    </div>
                    <PriorityBadge priority={email.priority} />
                  </div>
                </Link>
              ))
            ) : (
              <EmptyState title="No urgent emails" description="P1 messages will appear here as soon as REPLYNT detects them." />
            )}
          </div>
        </section>
        <section className="rounded-xl border border-line bg-panel/60 p-5">
          <h2 className="mb-4 font-semibold text-white">Upcoming deadlines</h2>
          <div className="space-y-3">
            {upcoming.length ? upcoming.map((task) => <TaskCard key={task.id} task={task} />) : <EmptyState title="Nothing due" description="Commitments with deadlines will land here." />}
          </div>
        </section>
      </div>
    </div>
  );
}
