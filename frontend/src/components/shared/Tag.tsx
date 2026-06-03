interface TagProps {
  label: string;
  variant?: "default" | "warn" | "success" | "accent";
  onClick?: () => void;
}

const variants = {
  default: "border-[var(--line)] bg-[var(--panel)] text-[var(--text)]",
  warn: "border-[#f2c36b] bg-[#fff7e6] text-[#754200]",
  success: "border-[#9bd2b6] bg-[#f2fbf6] text-[var(--green)]",
  accent: "border-[#cfe3f7] bg-[#eef6ff] text-[var(--accent)]",
};

export function Tag({ label, variant = "default", onClick }: TagProps) {
  const base =
    "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium";
  const interactive = onClick ? "cursor-pointer hover:opacity-80" : "";

  return (
    <span
      className={`${base} ${variants[variant]} ${interactive}`}
      onClick={onClick}
    >
      {label}
    </span>
  );
}
