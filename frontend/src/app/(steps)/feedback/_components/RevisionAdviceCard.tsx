import { Lightbulb } from "lucide-react";

export function RevisionAdviceCard({ advice }: { advice: string }) {
  if (!advice) return null;

  return (
    <div className="rounded-xl border border-[#cfe3f7] bg-[#eef6ff] p-4">
      <div className="mb-2 flex items-center gap-2">
        <Lightbulb size={16} className="text-[var(--accent)]" />
        <h3 className="text-sm font-semibold text-[var(--accent)]">修改建议</h3>
      </div>
      <p className="text-sm leading-relaxed">{advice}</p>
    </div>
  );
}
