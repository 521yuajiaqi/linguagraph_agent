"use client";

import { useState } from "react";
import { Tag } from "@/components/shared/Tag";
import { ChevronDown } from "lucide-react";
import type { MistakeRecord } from "@/lib/utils/types";

interface MistakeWithId extends MistakeRecord {
  id: string;
  created_at?: string;
}

export function MistakeNotebook({ mistakes }: { mistakes: MistakeWithId[] }) {
  const [filter, setFilter] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const allTags = [...new Set(mistakes.flatMap((m) => m.error_types))];

  const filtered = filter
    ? mistakes.filter((m) =>
        m.error_types.some((t) => t.toLowerCase().includes(filter.toLowerCase()))
      )
    : mistakes;

  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4">
      <h3 className="mb-3 text-sm font-semibold">
        错题本 · {mistakes.length} 条记录
      </h3>

      {allTags.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-1.5">
          <button
            onClick={() => setFilter("")}
            className={`rounded-full px-2.5 py-0.5 text-xs ${
              !filter
                ? "bg-[var(--accent)] text-white"
                : "bg-[var(--panel-soft)] text-[var(--muted)]"
            }`}
          >
            全部
          </button>
          {allTags.map((tag) => (
            <button
              key={tag}
              onClick={() => setFilter(tag === filter ? "" : tag)}
              className={`rounded-full px-2.5 py-0.5 text-xs ${
                filter === tag
                  ? "bg-[var(--amber)] text-white"
                  : "bg-[var(--panel-soft)] text-[var(--muted)] hover:bg-[var(--line)]"
              }`}
            >
              {tag}
            </button>
          ))}
        </div>
      )}

      <div className="space-y-2">
        {filtered.map((m) => (
          <div
            key={m.id}
            className="rounded-lg border border-[var(--line)] bg-[var(--panel-soft)]"
          >
            <button
              onClick={() => setExpandedId(expandedId === m.id ? null : m.id)}
              className="flex w-full items-center justify-between px-3 py-2.5 text-left"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{m.source_text}</p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {m.error_types.map((tag) => (
                    <Tag key={tag} label={tag} variant="warn" />
                  ))}
                </div>
              </div>
              <ChevronDown
                size={14}
                className={`ml-2 shrink-0 text-[var(--muted)] transition-transform ${
                  expandedId === m.id ? "rotate-180" : ""
                }`}
              />
            </button>
            {expandedId === m.id && (
              <div className="border-t border-[var(--line)] px-3 py-2.5 space-y-2 text-sm">
                <div>
                  <span className="text-[var(--muted)]">你的译文：</span>
                  <span className="text-[var(--danger)]">{m.student_answer}</span>
                </div>
                <div>
                  <span className="text-[var(--muted)]">推荐译文：</span>
                  <span className="text-[var(--green)]">{m.recommended_answer}</span>
                </div>
                <div>
                  <span className="text-[var(--muted)]">原因：</span>
                  {m.reason}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <p className="py-4 text-center text-sm text-[var(--muted)]">
          没有匹配的错题记录
        </p>
      )}
    </div>
  );
}
