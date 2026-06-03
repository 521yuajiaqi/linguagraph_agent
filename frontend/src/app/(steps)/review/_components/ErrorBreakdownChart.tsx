"use client";

import { useState, useEffect } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface Props {
  data: Array<{ tag: string; count: number }>;
}

const BAR_COLORS = [
  "var(--danger)",
  "var(--amber)",
  "var(--accent)",
  "var(--purple)",
  "var(--teal)",
  "var(--green)",
];

export function ErrorBreakdownChart({ data }: Props) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);

  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4">
      <h3 className="mb-3 text-sm font-semibold">错误分类统计</h3>
      <div className="h-[220px] w-full">
        {mounted ? (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 10 }}>
            <CartesianGrid stroke="var(--line)" strokeDasharray="3 3" />
            <XAxis type="number" tick={{ fontSize: 12, fill: "var(--muted)" }} />
            <YAxis
              dataKey="tag"
              type="category"
              tick={{ fontSize: 12, fill: "var(--text)" }}
              width={80}
            />
            <Tooltip
              contentStyle={{
                background: "var(--panel)",
                border: "1px solid var(--line)",
                borderRadius: "8px",
                fontSize: "13px",
              }}
            />
            <Bar dataKey="count" radius={[0, 4, 4, 0]}>
              {data.map((_entry, i) => (
                <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        ) : (
          <div className="h-full w-full" />
        )}
      </div>
    </div>
  );
}
