"use client";

import { Component, type ReactNode } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
          <AlertTriangle size={40} className="text-[var(--danger)]" />
          <p className="text-sm font-medium text-[var(--text)]">出了点问题</p>
          <p className="max-w-xs text-sm text-[var(--muted)]">
            {this.state.error?.message || "组件渲染出错"}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--line)] bg-[var(--panel)] px-4 py-2 text-sm text-[var(--accent)] hover:bg-[var(--panel-soft)]"
          >
            <RotateCcw size={14} />
            重试
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
