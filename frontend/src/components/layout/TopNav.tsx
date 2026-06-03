"use client";

import Link from "next/link";
import { useSessionStore } from "@/lib/stores/session-store";
import { LANGUAGE_PAIRS } from "@/lib/utils/constants";
import { Menu, LayoutGrid } from "lucide-react";

export function TopNav({ onMenuClick }: { onMenuClick?: () => void }) {
  const languagePair = useSessionStore((s) => s.languagePair);
  const setLanguagePair = useSessionStore((s) => s.setLanguagePair);
  const userLevel = useSessionStore((s) => s.userLevel);

  return (
    <header className="flex min-h-[64px] items-center justify-between gap-4 border-b border-[var(--line)] bg-[var(--panel)] px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="rounded-lg p-1.5 text-[var(--muted)] hover:bg-[var(--panel-soft)] lg:hidden"
        >
          <Menu size={20} />
        </button>
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-[var(--accent)] to-[var(--green)] text-sm font-bold text-white">
          LG
        </div>
        <div>
          <h1 className="text-lg font-semibold leading-tight">LinguaGraph</h1>
          <p className="text-xs text-[var(--muted)]">
            诊断 · 练习 · 反馈 · 复习
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Link
          href="/portal"
          className="hidden items-center gap-2 rounded-lg border border-[var(--line)] bg-[var(--panel)] px-3 py-1.5 text-sm text-[var(--text)] hover:bg-[var(--panel-soft)] md:inline-flex"
        >
          <LayoutGrid size={14} />
          门户
        </Link>
        <select
          value={languagePair}
          onChange={(e) => setLanguagePair(e.target.value)}
          className="rounded-lg border border-[var(--line)] bg-[var(--panel)] px-3 py-1.5 text-sm text-[var(--text)]"
        >
          {Object.entries(LANGUAGE_PAIRS).map(([key, { label }]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>

        {userLevel && (
          <span className="rounded-full bg-[#eef6ff] px-3 py-1 text-xs font-semibold text-[var(--accent)]">
            {userLevel}
          </span>
        )}
      </div>
    </header>
  );
}
