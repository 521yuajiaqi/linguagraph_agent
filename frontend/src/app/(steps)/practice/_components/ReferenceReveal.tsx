"use client";

import { useState } from "react";
import { Eye, EyeOff, AlertTriangle } from "lucide-react";

export function ReferenceReveal({ reference }: { reference: string }) {
  const [show, setShow] = useState(false);

  if (!reference) return null;

  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4">
      {!show ? (
        <button
          onClick={() => setShow(true)}
          className="flex items-center gap-2 text-sm text-[var(--muted)] hover:text-[var(--accent)]"
        >
          <Eye size={16} />
          查看参考译文
        </button>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-[var(--muted)]">
              参考译文
            </span>
            <button
              onClick={() => setShow(false)}
              className="text-[var(--muted)] hover:text-[var(--text)]"
            >
              <EyeOff size={14} />
            </button>
          </div>
          <p className="whitespace-pre-wrap break-words text-base leading-relaxed">
            {reference}
          </p>
          <p className="flex items-center gap-1 text-xs text-[var(--amber)]">
            <AlertTriangle size={12} />
            建议先自己修改后再对照参考译文
          </p>
        </div>
      )}
    </div>
  );
}
