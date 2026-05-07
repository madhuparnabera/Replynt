"use client";

import { useState } from "react";
import { supabase } from "@/lib/supabase";
import type { Alert } from "@/lib/types";
import { useToast } from "@/components/ToastProvider";

export function AlertCard({ alert, onRead }: { alert: Alert; onRead?: (id: number) => void }) {
  const [loading, setLoading] = useState(false);
  const { notify } = useToast();

  async function markRead() {
    if (alert.is_read) return;
    setLoading(true);
    onRead?.(alert.id);
    const { error } = await supabase.from("alerts").update({ is_read: true }).eq("id", alert.id);
    setLoading(false);
    if (error) {
      notify("Unable to mark alert as read", "error");
      return;
    }
    notify("Alert marked as read", "success");
  }

  return (
    <div className={`rounded-xl border bg-panel p-4 ${alert.is_read ? "border-line opacity-70" : "border-red-500/40"}`}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-red-300">{alert.alert_type}</div>
          <h3 className="mt-2 text-sm font-semibold text-white">{alert.message}</h3>
          {alert.task ? <p className="mt-2 text-sm text-slate-400">{alert.task}</p> : null}
        </div>
        <button
          onClick={markRead}
          disabled={alert.is_read || loading}
          className="rounded-xl border border-line px-3 py-2 text-sm text-slate-200 transition hover:border-blue-500/40 hover:bg-blue-500/10 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {alert.is_read ? "Read" : "Mark read"}
        </button>
      </div>
    </div>
  );
}
