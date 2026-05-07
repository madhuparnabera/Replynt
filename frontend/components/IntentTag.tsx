export function IntentTag({ intent }: { intent?: string | null }) {
  return (
    <span className="inline-flex items-center rounded-full border border-slate-500/30 bg-slate-500/10 px-2.5 py-1 text-xs font-medium text-slate-300">
      {intent || "Unknown"}
    </span>
  );
}
