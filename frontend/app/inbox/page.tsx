"use client";

import { useEffect, useState } from "react";
import { EmailCard } from "@/components/EmailCard";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { SectionHeader } from "@/components/SectionHeader";
import { supabase } from "@/lib/supabase";
import type { Email } from "@/lib/types";

export default function InboxPage() {
  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function load() {
      const { data } = await supabase.from("emails").select("*").order("created_at", { ascending: false });
      if (active) {
        setEmails((data ?? []) as Email[]);
        setLoading(false);
      }
    }
    load();
    const channel = supabase
      .channel("emails-realtime")
      .on("postgres_changes", { event: "*", schema: "public", table: "emails" }, load)
      .subscribe();
    return () => {
      active = false;
      supabase.removeChannel(channel);
    };
  }, []);

  if (loading) return <LoadingState label="Loading inbox..." />;

  return (
    <div className="space-y-6">
      <SectionHeader eyebrow="Inbox" title="Analyzed emails" />
      <div className="space-y-3">
        {emails.length ? emails.map((email) => <EmailCard key={email.id} email={email} />) : <EmptyState title="Inbox is empty" description="Analyzed emails from Supabase will appear here." />}
      </div>
    </div>
  );
}
