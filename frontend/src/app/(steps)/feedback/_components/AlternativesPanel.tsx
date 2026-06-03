import { CheckCircle } from "lucide-react";

export function AlternativesPanel({
  reference,
  alternatives,
}: {
  reference?: string;
  alternatives?: string[];
}) {
  const allAlternatives = [
    ...(reference ? [reference] : []),
    ...(alternatives || []),
  ];

  if (allAlternatives.length === 0) return null;

  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4">
      <h3 className="mb-2 text-sm font-semibold">可接受译法</h3>
      <div className="space-y-2">
        {allAlternatives.map((alt, i) => (
          <div
            key={i}
            className="flex items-start gap-2 rounded-lg bg-[var(--panel-soft)] p-3 text-sm"
          >
            <CheckCircle size={14} className="mt-0.5 shrink-0 text-[var(--green)]" />
            <span>{alt}</span>
            {i === 0 && (
              <span className="shrink-0 rounded bg-[var(--accent)] px-1.5 py-0.5 text-xs text-white">
                推荐
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
