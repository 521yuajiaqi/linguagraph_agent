"use client";

import { useState, useEffect } from "react";

export function LevelBadge({ level }: { level: string }) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setShow(true), 200);
    return () => clearTimeout(t);
  }, []);

  const colors: Record<string, string> = {
    A1: "from-[var(--muted)] to-[var(--line)]",
    A2: "from-[var(--teal)] to-[var(--green)]",
    B1: "from-[var(--accent)] to-[var(--purple)]",
    B2: "from-[var(--purple)] to-[var(--amber)]",
    C1: "from-[var(--amber)] to-[var(--danger)]",
  };

  const gradient = colors[level] || colors["B1"];

  return (
    <div
      className={`inline-flex flex-col items-center transition-all duration-700 ${
        show ? "opacity-100 scale-100" : "opacity-0 scale-75"
      }`}
    >
      <div
        className={`flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br ${gradient} text-3xl font-bold text-white shadow-lg`}
      >
        {level}
      </div>
      <p className="mt-2 text-xs font-medium text-[var(--muted)]">
        CEFR 估计水平
      </p>
    </div>
  );
}
