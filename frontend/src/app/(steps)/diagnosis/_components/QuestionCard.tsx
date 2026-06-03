"use client";

import { useState } from "react";
import { useDiagnosisStore } from "@/lib/stores/diagnosis-store";
import type { DiagnosisQuestion } from "@/lib/utils/types";
import { ArrowLeft, ArrowRight } from "lucide-react";

const TYPE_LABELS: Record<string, string> = {
  choice: "选择题",
  fill_blank: "填空题",
  short_translate: "短句翻译",
  error_correction: "改错题",
};

export function QuestionCard({
  question,
  onSubmit,
  isLast,
}: {
  question: DiagnosisQuestion;
  onSubmit: () => void;
  isLast: boolean;
}) {
  const answers = useDiagnosisStore((s) => s.answers);
  const setAnswer = useDiagnosisStore((s) => s.setAnswer);
  const currentIndex = useDiagnosisStore((s) => s.currentIndex);
  const next = useDiagnosisStore((s) => s.next);
  const prev = useDiagnosisStore((s) => s.prev);
  const allAnswered = useDiagnosisStore((s) => s.allAnswered);
  const questions = useDiagnosisStore((s) => s.questions);

  const currentAnswer = answers[question.id] || "";
  const canAdvance = currentAnswer.trim().length > 0;

  const handleSubmit = () => {
    if (isLast) {
      onSubmit();
    } else {
      next();
    }
  };

  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <span className="rounded-full bg-[#f3f0ff] px-2.5 py-0.5 text-xs font-medium text-[var(--purple)]">
          {TYPE_LABELS[question.type] || question.type}
        </span>
        <span className="text-xs text-[var(--muted)]">
          难度：{question.difficulty} · 第 {currentIndex + 1}/{questions.length} 题
        </span>
      </div>

      <p className="mb-6 text-lg leading-relaxed">{question.source_text}</p>

      {question.type === "choice" && question.options && (
        <div className="space-y-2">
          {question.options.map((opt, i) => (
            <label
              key={i}
              className={`flex cursor-pointer items-center gap-3 rounded-lg border p-3 transition-colors ${
                currentAnswer === opt
                  ? "border-[var(--purple)] bg-[#f3f0ff]"
                  : "border-[var(--line)] hover:bg-[var(--panel-soft)]"
              }`}
            >
              <input
                type="radio"
                name={`q-${question.id}`}
                value={opt}
                checked={currentAnswer === opt}
                onChange={() => setAnswer(question.id, opt)}
                className="sr-only"
              />
              <span
                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 text-xs ${
                  currentAnswer === opt
                    ? "border-[var(--purple)] bg-[var(--purple)] text-white"
                    : "border-[var(--line)]"
                }`}
              >
                {String.fromCharCode(65 + i)}
              </span>
              <span className="text-sm">{opt}</span>
            </label>
          ))}
        </div>
      )}

      {question.type === "fill_blank" && (
        <div className="space-y-3">
          <input
            type="text"
            value={currentAnswer}
            onChange={(e) => setAnswer(question.id, e.target.value)}
            placeholder="输入填空词..."
            className="w-full rounded-lg border border-[var(--line)] px-4 py-2.5 text-sm focus:border-[var(--purple)] focus:outline-none"
            onKeyDown={(e) => {
              if (e.key === "Enter" && canAdvance) handleSubmit();
            }}
          />
          {question.hint && (
            <p className="text-xs text-[var(--muted)]">提示：{question.hint}</p>
          )}
        </div>
      )}

      {(question.type === "short_translate" || question.type === "error_correction") && (
        <div className="space-y-3">
          <textarea
            value={currentAnswer}
            onChange={(e) => setAnswer(question.id, e.target.value)}
            placeholder={
              question.type === "short_translate"
                ? "输入您的译文..."
                : "请写出修正后的句子..."
            }
            rows={3}
            className="w-full resize-none rounded-lg border border-[var(--line)] px-4 py-2.5 text-sm leading-relaxed focus:border-[var(--purple)] focus:outline-none"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey && canAdvance) {
                e.preventDefault();
                handleSubmit();
              }
            }}
          />
          {question.type === "error_correction" && question.error_sentence && (
            <div className="rounded-lg border border-[#f2c36b] bg-[#fff7e6] p-3 text-sm">
              <span className="font-medium text-[#754200]">原句：</span>
              <span className="text-[#754200]">{question.error_sentence}</span>
            </div>
          )}
        </div>
      )}

      <div className="mt-6 flex items-center justify-between">
        <button
          onClick={prev}
          disabled={currentIndex === 0}
          className="inline-flex items-center gap-1 rounded-lg px-3 py-2 text-sm text-[var(--muted)] hover:text-[var(--text)] disabled:opacity-30"
        >
          <ArrowLeft size={16} />
          上一题
        </button>

        <button
          onClick={handleSubmit}
          disabled={!canAdvance}
          className="inline-flex items-center gap-2 rounded-xl bg-[var(--purple)] px-6 py-2.5 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-40 transition-opacity"
        >
          {isLast ? "提交诊断" : "下一题"}
          {!isLast && <ArrowRight size={16} />}
        </button>
      </div>
    </div>
  );
}
