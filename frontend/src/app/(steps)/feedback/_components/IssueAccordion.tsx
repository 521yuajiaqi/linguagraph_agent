"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";

export function IssueAccordion({ issues }: { issues: string[] }) {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  if (!issues.length) return null;

  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4">
      <h3 className="mb-2 text-sm font-semibold">主要问题</h3>
      <div className="space-y-1">
        {issues.map((issue, i) => (
          <div key={i} className="overflow-hidden rounded-lg border border-[var(--line)]">
            <button
              onClick={() => setOpenIndex(openIndex === i ? null : i)}
              className="flex w-full items-center justify-between px-3 py-2.5 text-left text-sm hover:bg-[var(--panel-soft)]"
            >
              <span className="font-medium">
                {i + 1}. {issue.slice(0, 60)}{issue.length > 60 ? "..." : ""}
              </span>
              <ChevronDown
                size={14}
                className={`shrink-0 text-[var(--muted)] transition-transform ${openIndex === i ? "rotate-180" : ""}`}
              />
            </button>
            {openIndex === i && (
              <div className="border-t border-[var(--line)] bg-[var(--panel-soft)] px-3 py-2.5 text-sm leading-relaxed text-[var(--muted)]">
                {issue}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
