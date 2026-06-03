"use client";

import { useSessionStore } from "@/lib/stores/session-store";
import { LANGUAGE_PAIRS } from "@/lib/utils/constants";

interface Props {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function TranslationEditor({ value, onChange, disabled }: Props) {
  const languagePair = useSessionStore((s) => s.languagePair);
  const pairInfo = LANGUAGE_PAIRS[languagePair as keyof typeof LANGUAGE_PAIRS];
  const targetLang = pairInfo?.target === "ru" ? "俄语" : "中文";

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-[var(--muted)]">我的译文</label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder={`输入您的${targetLang}译文... (Ctrl+Enter 提交)`}
        rows={4}
        className="w-full resize-none rounded-xl border border-[var(--line)] bg-[var(--panel)] px-4 py-3 text-sm leading-relaxed placeholder:text-[var(--muted)] focus:border-[var(--accent)] focus:outline-none disabled:opacity-50"
      />
      <p className="text-xs text-[var(--muted)]">
        {value.length} 字符 · 先自己尝试，卡住时使用上方提示
      </p>
    </div>
  );
}
