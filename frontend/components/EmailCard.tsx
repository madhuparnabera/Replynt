import Link from "next/link";
import { IntentTag } from "@/components/IntentTag";
import { PriorityBadge } from "@/components/PriorityBadge";
import { formatScore } from "@/lib/format";
import type { Email } from "@/lib/types";

export function EmailCard({ email }: { email: Email }) {
  return (
    <Link
      href={`/email/${encodeURIComponent(email.email_id)}`}
      className="block rounded-xl border border-line bg-panel p-4 transition hover:border-blue-500/40 hover:bg-slate-900"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <PriorityBadge priority={email.priority} />
            <IntentTag intent={email.intent} />
            {email.needs_reply ? (
              <span className="rounded-full border border-blue-400/40 bg-blue-500/12 px-2.5 py-1 text-xs font-medium text-blue-200">
                Reply needed
              </span>
            ) : null}
          </div>
          <h2 className="mt-3 truncate text-base font-semibold text-white">{email.subject}</h2>
          <p className="mt-1 truncate text-sm text-slate-400">{email.sender}</p>
        </div>
        <div className="rounded-xl border border-line bg-canvas px-3 py-2 text-sm text-slate-300">
          Risk <span className="font-semibold text-white">{formatScore(email.risk_score)}</span>
        </div>
      </div>
    </Link>
  );
}
