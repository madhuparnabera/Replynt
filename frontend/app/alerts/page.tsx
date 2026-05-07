"use client";

import { useEffect, useState } from "react";
import { AlertCard } from "@/components/AlertCard";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { SectionHeader } from "@/components/SectionHeader";
import { supabase } from "@/lib/supabase";
import type { Alert } from "@/lib/types";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function load() {
      const { data } = await supabase.from("alerts").select("*").order("id", { ascending: false });
      if (active) {
        setAlerts((data ?? []) as Alert[]);
        setLoading(false);
      }
    }
    load();
    const channel = supabase.channel("alerts-realtime").on("postgres_changes", { event: "*", schema: "public", table: "alerts" }, load).subscribe();
    return () => {
      active = false;
      supabase.removeChannel(channel);
    };
  }, []);

  if (loading) return <LoadingState label="Loading alerts..." />;

  return (
    <div className="space-y-6">
      <SectionHeader eyebrow="Alerts" title="Risk and deadline alerts" />
      <div className="space-y-3">
        {alerts.length ? (
          alerts.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onRead={(id) => setAlerts((current) => current.map((item) => (item.id === id ? { ...item, is_read: true } : item)))}
            />
          ))
        ) : (
          <EmptyState title="No alerts" description="New unread alerts will appear here in realtime." />
        )}
      </div>
    </div>
  );
}
