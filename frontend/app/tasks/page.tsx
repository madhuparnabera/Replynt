"use client";

import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { SectionHeader } from "@/components/SectionHeader";
import { TaskCard } from "@/components/TaskCard";
import { supabase } from "@/lib/supabase";
import type { Commitment, Priority } from "@/lib/types";

export default function TasksPage() {
  const [tasks, setTasks] = useState<Commitment[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState("all");
  const [priority, setPriority] = useState<Priority | "all">("all");

  useEffect(() => {
    let active = true;
    async function load() {
      const { data } = await supabase.from("commitments").select("*").order("deadline", { ascending: true, nullsFirst: false });
      if (active) {
        setTasks((data ?? []) as Commitment[]);
        setLoading(false);
      }
    }
    load();
    const channel = supabase.channel("tasks-realtime").on("postgres_changes", { event: "*", schema: "public", table: "commitments" }, load).subscribe();
    return () => {
      active = false;
      supabase.removeChannel(channel);
    };
  }, []);

  const statuses = useMemo(() => ["all", ...Array.from(new Set(tasks.map((task) => task.status || "open")))], [tasks]);
  const filtered = tasks.filter((task) => (status === "all" || task.status === status) && (priority === "all" || task.priority === priority));

  if (loading) return <LoadingState label="Loading commitments..." />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <SectionHeader eyebrow="Tasks" title="Commitment tracker" />
        <div className="flex flex-wrap gap-3">
          <select value={status} onChange={(event) => setStatus(event.target.value)} className="rounded-xl border border-line bg-panel px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500/70">
            {statuses.map((item) => <option key={item}>{item}</option>)}
          </select>
          <select value={priority} onChange={(event) => setPriority(event.target.value as Priority | "all")} className="rounded-xl border border-line bg-panel px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500/70">
            {["all", "P1", "P2", "P3"].map((item) => <option key={item}>{item}</option>)}
          </select>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {filtered.length ? filtered.map((task) => <TaskCard key={task.id} task={task} />) : <EmptyState title="No commitments match" description="Try a different status or priority filter." />}
      </div>
    </div>
  );
}
