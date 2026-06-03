"use client";

import { Tag } from "@/components/shared/Tag";

export function ErrorTagCloud({
  tags,
  focusAreas,
}: {
  tags: string[];
  focusAreas: string[];
}) {
  if (!tags.length) {
    return (
      <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4">
        <h3 className="mb-2 text-sm font-semibold">错误标签</h3>
        <p className="text-sm text-[var(--muted)]">未发现明显错误</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4">
      <h3 className="mb-2 text-sm font-semibold">错误标签</h3>
      <div className="flex flex-wrap gap-1.5">
        {tags.map((tag) => (
          <Tag
            key={tag}
            label={tag}
            variant="warn"
          />
        ))}
      </div>
      {focusAreas.length > 0 && (
        <p className="mt-3 text-xs text-[var(--muted)]">
          下一轮将针对：{focusAreas.join("、")} 生成专项练习
        </p>
      )}
    </div>
  );
}
