import type { Priority } from "@/lib/types";

const styles: Record<Priority, string> = {
  P1: "border-red-400/40 bg-red-500/12 text-red-300",
  P2: "border-yellow-400/40 bg-yellow-500/12 text-yellow-200",
  P3: "border-emerald-400/40 bg-emerald-500/12 text-emerald-300"
};

export function PriorityBadge({ priority }: { priority: Priority }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium ${styles[priority]}`}>
      {priority}
    </span>
  );
}
