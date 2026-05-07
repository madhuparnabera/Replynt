import { PriorityBadge } from "@/components/PriorityBadge";
import { formatDate, isOverdue } from "@/lib/format";
import type { Commitment } from "@/lib/types";

export function TaskCard({ task }: { task: Commitment }) {
  const overdue = isOverdue(task.deadline) && task.status !== "done";

  return (
    <div className={`rounded-xl border bg-panel p-4 ${overdue ? "border-red-500/50" : "border-line"}`}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <PriorityBadge priority={task.priority} />
        <span className="rounded-full border border-slate-500/30 bg-slate-500/10 px-2.5 py-1 text-xs text-slate-300">
          {task.status || "open"}
        </span>
      </div>
      <h3 className="mt-3 text-sm font-semibold leading-6 text-white">{task.task}</h3>
      <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-400">
        <span>{task.who || "Unassigned"}</span>
        <span className={overdue ? "text-red-300" : "text-slate-400"}>{overdue ? "Overdue" : formatDate(task.deadline)}</span>
      </div>
    </div>
  );
}
