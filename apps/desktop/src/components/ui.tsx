import { AlertTriangle, CheckCircle2, CircleDashed, Info, Loader2, OctagonAlert } from "lucide-react";
import type { ComponentProps, ReactNode } from "react";
import type { Verdict } from "../api/types";

type Variant = "primary" | "secondary" | "ghost" | "danger";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-accent text-white shadow-[0_1px_0_rgba(0,0,0,.15)] hover:brightness-110 disabled:opacity-50",
  secondary: "border border-rule bg-sheet text-ink hover:border-ink-soft disabled:opacity-50",
  ghost: "text-ink-soft hover:bg-accent-wash hover:text-accent-ink disabled:opacity-40",
  danger: "border border-brick/40 text-brick hover:bg-brick-wash disabled:opacity-50",
};

export function Button({
  variant = "secondary",
  busy = false,
  icon,
  children,
  className = "",
  ...props
}: ComponentProps<"button"> & { variant?: Variant; busy?: boolean; icon?: ReactNode }) {
  return (
    <button
      type="button"
      {...props}
      disabled={props.disabled || busy}
      aria-busy={busy || undefined}
      className={`inline-flex min-h-10 items-center justify-center gap-2 rounded-lg px-4 py-2 text-[0.95rem] font-bold transition ${VARIANTS[variant]} ${className}`}
    >
      {busy ? <Loader2 aria-hidden className="size-4 animate-spin" /> : icon}
      {children}
    </button>
  );
}

const VERDICTS: Record<Verdict, { label: string; tone: string; Icon: typeof CheckCircle2 }> = {
  supported: { label: "Respaldada", tone: "bg-moss-wash text-moss", Icon: CheckCircle2 },
  partial: { label: "Respaldo parcial", tone: "bg-ochre-wash text-ochre", Icon: CircleDashed },
  unsupported: { label: "Sin respaldo", tone: "bg-brick-wash text-brick", Icon: AlertTriangle },
};

export function VerdictBadge({ verdict, compact = false }: { verdict: Verdict; compact?: boolean }) {
  const { label, tone, Icon } = VERDICTS[verdict];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-sm font-bold ${tone}`}>
      <Icon aria-hidden className="size-4" />
      {compact ? <span className="sr-only">{label}</span> : label}
    </span>
  );
}

export function ProgressBar({ value, label }: { value: number; label: string }) {
  const percent = Math.round(value * 100);
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={percent}
      className="h-2.5 w-full overflow-hidden rounded-full bg-rule/60"
    >
      <div className="h-full rounded-full bg-accent transition-[width] duration-500" style={{ width: `${percent}%` }} />
    </div>
  );
}

const BANNERS = {
  info: { tone: "border-rule bg-sheet text-ink", Icon: Info, role: "status" },
  warning: { tone: "border-ochre/40 bg-ochre-wash text-ink", Icon: AlertTriangle, role: "status" },
  error: { tone: "border-brick/40 bg-brick-wash text-ink", Icon: OctagonAlert, role: "alert" },
  success: { tone: "border-moss/40 bg-moss-wash text-ink", Icon: CheckCircle2, role: "status" },
} as const;

export function Banner({
  kind = "info",
  title,
  children,
  actions,
}: {
  kind?: keyof typeof BANNERS;
  title: string;
  children?: ReactNode;
  actions?: ReactNode;
}) {
  const { tone, Icon, role } = BANNERS[kind];
  return (
    <div role={role} className={`rise flex gap-3 rounded-xl border p-4 ${tone}`}>
      <Icon aria-hidden className="mt-0.5 size-5 shrink-0" />
      <div className="min-w-0 flex-1">
        <p className="font-bold">{title}</p>
        {children && <div className="mt-1 text-ink-soft">{children}</div>}
        {actions && <div className="mt-3 flex flex-wrap gap-2">{actions}</div>}
      </div>
    </div>
  );
}

export function Eyebrow({ children }: { children: ReactNode }) {
  return <p className="font-mono text-xs tracking-[0.18em] text-accent-ink uppercase">{children}</p>;
}

export function ScreenHeader({ eyebrow, title, children }: { eyebrow: string; title: string; children?: ReactNode }) {
  return (
    <header className="rise mb-8">
      <Eyebrow>{eyebrow}</Eyebrow>
      <h1 tabIndex={-1} data-screen-title className="font-display mt-2 text-[2.4rem] leading-[1.1] font-semibold text-ink outline-none">
        {title}
      </h1>
      {children && <div className="mt-3 max-w-[62ch] text-lg text-ink-soft">{children}</div>}
    </header>
  );
}

export function Kbd({ children }: { children: ReactNode }) {
  return (
    <kbd className="rounded border border-rule bg-sheet px-1.5 py-0.5 font-mono text-xs text-ink-soft">{children}</kbd>
  );
}
