"use client";

import { useState, useEffect } from "react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from "recharts";
import { DIMENSION_ORDER } from "@/lib/utils/constants";
import type { DimensionScores } from "@/lib/utils/types";

export function DimensionRadar({
  scores,
  labels,
}: {
  scores: DimensionScores;
  labels: Record<string, string>;
}) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);

  const data = DIMENSION_ORDER
    .filter((dim) => scores[dim as keyof DimensionScores] !== undefined)
    .map((dim) => ({
      dimension: labels[dim] || dim,
      score: scores[dim as keyof DimensionScores] || 0,
      fullMark: 5,
    }));

  if (data.length === 0) return null;

  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4">
      <h3 className="mb-2 text-sm font-semibold">评分维度</h3>
      <div className="h-[300px] w-full">
        {mounted ? (
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
              <PolarGrid stroke="var(--line)" />
              <PolarAngleAxis
                dataKey="dimension"
                tick={{ fontSize: 13, fill: "var(--text)" }}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 5]}
                tick={{ fontSize: 10, fill: "var(--muted)" }}
                tickCount={6}
              />
              <Radar
                name="您的评分"
                dataKey="score"
                stroke="var(--accent)"
                strokeWidth={2}
                fill="var(--accent)"
                fillOpacity={0.2}
              />
            </RadarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full w-full" />
        )}
      </div>
    </div>
  );
}
