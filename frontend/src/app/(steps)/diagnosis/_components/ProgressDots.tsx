"use client";

export function ProgressDots({
  total,
  current,
  onDotClick,
}: {
  total: number;
  current: number;
  onDotClick: (index: number) => void;
}) {
  return (
    <div className="mb-6 flex items-center justify-center gap-2">
      {Array.from({ length: total }, (_, i) => (
        <button
          key={i}
          onClick={() => onDotClick(i)}
          className={`h-2.5 rounded-full transition-all ${
            i === current
              ? "w-8 bg-[var(--purple)]"
              : i < current
                ? "w-3 bg-[var(--purple)] opacity-40"
                : "w-3 bg-[var(--line)]"
          }`}
        />
      ))}
    </div>
  );
}
