export function LoadingState({ label = "Loading intelligence..." }: { label?: string }) {
  return (
    <div className="grid gap-3">
      <div className="h-24 animate-pulse rounded-xl border border-line bg-panel/70" />
      <div className="h-24 animate-pulse rounded-xl border border-line bg-panel/50" />
      <div className="h-24 animate-pulse rounded-xl border border-line bg-panel/30" />
      <div className="text-sm text-slate-500">{label}</div>
    </div>
  );
}
