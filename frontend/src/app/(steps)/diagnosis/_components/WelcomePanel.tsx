"use client";

import { Sparkles, Clock, Target, BookOpen } from "lucide-react";

export function WelcomePanel({
  onStart,
  error,
}: {
  onStart: () => void;
  error: string | null;
}) {
  return (
    <div className="space-y-8 py-8">
      <div className="text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-[var(--purple)] to-[var(--accent)]">
          <Sparkles size={28} className="text-white" />
        </div>
        <h2 className="text-2xl font-bold">开始能力诊断</h2>
        <p className="mt-2 text-[var(--muted)]">
          完成 5 道题目，帮助我们了解您的翻译水平，制定个性化学习路径
        </p>
      </div>

      <div className="grid gap-3">
        <FeatureCard
          icon={<Target size={18} />}
          title="评估当前水平"
          description="选择题、填空题、短句翻译和改错题 — 覆盖多个能力维度"
        />
        <FeatureCard
          icon={<BookOpen size={18} />}
          title="发现强弱项"
          description="从语义准确、表达流畅、术语一致和语法结构四个维度分析"
        />
        <FeatureCard
          icon={<Clock size={18} />}
          title="约 10 分钟"
          description="5 道诊断题目，足够建立准确的学习画像"
        />
      </div>

      <div className="text-center">
        <button
          onClick={onStart}
          className="inline-flex items-center gap-2 rounded-xl bg-[var(--purple)] px-8 py-3 text-sm font-semibold text-white hover:opacity-90 transition-opacity"
        >
          开始诊断
        </button>
        {error && (
          <p className="mt-3 text-sm text-[var(--danger)]">{error}</p>
        )}
      </div>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="flex gap-3 rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4">
      <div className="shrink-0 mt-0.5 text-[var(--purple)]">{icon}</div>
      <div>
        <p className="text-sm font-semibold">{title}</p>
        <p className="text-sm text-[var(--muted)]">{description}</p>
      </div>
    </div>
  );
}
