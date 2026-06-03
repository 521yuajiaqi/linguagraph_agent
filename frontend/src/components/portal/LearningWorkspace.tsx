"use client";

import {
  ArrowRight,
  ClipboardList,
  Languages,
  Sparkles,
  GraduationCap,
} from "lucide-react";
import { useRouter } from "next/navigation";

function WorkspaceCard({
  title,
  description,
  accent,
  badge,
  active = false,
  onClick,
}: {
  title: string;
  description: string;
  accent: string;
  badge: string;
  active?: boolean;
  onClick?: () => void;
}) {
  const Component = active ? "button" : "div";

  return (
    <Component
      onClick={onClick}
      className={[
        "group w-full rounded-[1.75rem] border p-5 text-left transition-all",
        active
          ? "border-[var(--line)] bg-white/80 hover:-translate-y-0.5 hover:shadow-[0_16px_50px_rgba(15,23,42,0.08)]"
          : "border-dashed border-[var(--line)] bg-white/60",
      ].join(" ")}
      style={{
        boxShadow: `0 0 0 1px color-mix(in srgb, ${accent} 12%, transparent) inset`,
      }}
    >
      <div className="mb-4 flex items-center justify-between">
        <span
          className="rounded-full px-3 py-1 text-xs font-semibold"
          style={{
            color: accent,
            backgroundColor: `color-mix(in srgb, ${accent} 12%, white)`,
          }}
        >
          {badge}
        </span>
        {active ? (
          <ArrowRight
            size={16}
            className="text-[var(--muted)] transition-transform group-hover:translate-x-1"
          />
        ) : (
          <span className="text-xs text-[var(--muted)]">即将开放</span>
        )}
      </div>
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-[var(--muted)]">
        {description}
      </p>
    </Component>
  );
}

export function LearningWorkspace() {
  const router = useRouter();

  return (
    <section className="space-y-5">
      <div className="rounded-[2rem] border border-white/70 bg-[linear-gradient(135deg,rgba(255,255,255,0.85),rgba(238,245,255,0.88))] p-7 shadow-[0_18px_70px_rgba(15,23,42,0.06)] backdrop-blur-xl">
        <div className="flex items-start justify-between gap-6">
          <div className="max-w-2xl">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-[var(--line)] bg-white/70 px-3 py-1 text-xs font-semibold text-[var(--accent)]">
              <Sparkles size={12} />
              主学习区
            </div>
            <h2 className="text-3xl font-black tracking-tight text-slate-900">
              学习功能区
            </h2>
            <p className="mt-3 text-sm leading-7 text-slate-600">
              当前以翻译训练为主，后续将持续扩展俄语语法与专项练习模块，形成统一的学习门户。
            </p>
          </div>

          <div className="hidden shrink-0 rounded-2xl border border-[var(--line)] bg-white/70 px-4 py-3 text-right lg:block">
            <div className="text-xs text-slate-500">当前核心任务</div>
            <div className="mt-1 text-sm font-semibold text-slate-900">翻译训练闭环</div>
          </div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.35fr_0.65fr]">
        <div className="rounded-[2rem] border border-white/70 bg-[linear-gradient(135deg,rgba(47,109,184,0.11),rgba(255,255,255,0.82))] p-7 shadow-[0_18px_70px_rgba(15,23,42,0.05)]">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-[var(--accent)] shadow-sm">
              <Languages size={22} />
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-900">翻译训练工作台</h3>
              <p className="text-sm text-slate-600">
                进入当前的中俄/俄中翻译练习、批改与反馈闭环。
              </p>
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <button
              onClick={() => router.push("/practice")}
              className="rounded-2xl border border-[var(--line)] bg-white p-4 text-left transition-colors hover:bg-[var(--panel-soft)]"
            >
              <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
                <GraduationCap size={16} />
                继续翻译训练
              </div>
              <p className="text-sm text-[var(--muted)]">
                直接进入当前的练习、批改和反馈流程。
              </p>
            </button>

            <button
              onClick={() => router.push("/review")}
              className="rounded-2xl border border-[var(--line)] bg-white p-4 text-left transition-colors hover:bg-[var(--panel-soft)]"
            >
              <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
                <ClipboardList size={16} />
                查看学习复盘
              </div>
              <p className="text-sm text-[var(--muted)]">
                浏览能力数据、错题记录和后续规划。
              </p>
            </button>
          </div>
        </div>

        <div className="grid gap-4">
          <WorkspaceCard
            title="A1-B2 语法"
            description="未来用于按级别拆分俄语语法知识点，形成分层学习区。"
            accent="var(--teal)"
            badge="规划中"
          />
          <WorkspaceCard
            title="习题练习区"
            description="未来可承载题库练习、专项纠错和复习任务。"
            accent="var(--green)"
            badge="扩展区"
          />
        </div>
      </div>
    </section>
  );
}
