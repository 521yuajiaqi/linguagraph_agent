import { Inbox } from "lucide-react";

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
      <div className="text-[var(--muted)]">{icon || <Inbox size={40} />}</div>
      <p className="text-sm font-medium text-[var(--text)]">{title}</p>
      {description && (
        <p className="max-w-xs text-sm text-[var(--muted)]">{description}</p>
      )}
      {action}
    </div>
  );
}
