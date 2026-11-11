import { BookOpen, CircleHelp, Files, Minus, PenLine, Plus } from "lucide-react";
import type { ReactNode } from "react";
import type { LibrarySummary, ServiceHealth } from "../api/types";
import type { Connection } from "../hooks";

export type Section = "library" | "compose" | "drafts";

const NAV: { id: Section; label: string; hint: string; Icon: typeof BookOpen }[] = [
  { id: "library", label: "Mi biblioteca", hint: "Tus PDFs", Icon: BookOpen },
  { id: "compose", label: "Nuevo borrador", hint: "Pide un documento", Icon: PenLine },
  { id: "drafts", label: "Mis borradores", hint: "Revisa y exporta", Icon: Files },
];

const CONNECTION_COPY: Record<Connection, { label: string; dot: string }> = {
  checking: { label: "Conectando…", dot: "bg-ink-soft breathe" },
  ok: { label: "Asistente listo", dot: "bg-moss" },
  degraded: { label: "Funcionando con limitaciones", dot: "bg-ochre" },
  offline: { label: "Sin conexión con el asistente", dot: "bg-brick breathe" },
};

const SERVICE_NAMES: Record<string, string> = {
  library: "biblioteca",
  agents: "redacción",
  documents: "documentos",
};

function Mark() {
  return (
    <svg viewBox="0 0 40 40" aria-hidden className="size-9">
      <rect width="40" height="40" rx="11" fill="var(--accent)" />
      <path d="M12 27c0-8 5-14 13-15-1 8-6 14-13 15Z" fill="#fff" opacity=".95" />
      <path d="M13 26c3-4 6-7 10-10" stroke="var(--accent)" strokeWidth="1.6" strokeLinecap="round" fill="none" />
      <circle cx="28" cy="27" r="3.2" fill="#fff" opacity=".8" />
    </svg>
  );
}

export function Shell({
  active,
  onNavigate,
  onHelp,
  connection,
  services,
  library,
  scale,
  onScale,
  children,
}: {
  active: Section | null;
  onNavigate: (section: Section) => void;
  onHelp: () => void;
  connection: Connection;
  services: ServiceHealth[];
  library: LibrarySummary | null;
  scale: number;
  onScale: (value: number) => void;
  children: ReactNode;
}) {
  const status = CONNECTION_COPY[connection];
  const down = services.filter((service) => !service.ok).map((service) => SERVICE_NAMES[service.name] ?? service.name);
  const offline = services.find((service) => service.name === "agents")?.provider === "offline";

  return (
    <div className="grid h-screen grid-cols-[17rem_minmax(0,1fr)] grid-rows-[minmax(0,1fr)_auto] overflow-hidden">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:bg-sheet focus:p-2">
        Saltar al contenido
      </a>
      <nav aria-label="Secciones" className="row-span-2 flex flex-col border-r border-rule bg-sheet/70 px-4 py-5 backdrop-blur">
        <div className="mb-8 flex items-center gap-3 px-2">
          <Mark />
          <div>
            <p className="font-display text-lg leading-tight font-semibold">Asistente de</p>
            <p className="font-display text-lg leading-tight font-semibold">Investigación</p>
          </div>
        </div>
        <ul className="space-y-1">
          {NAV.map(({ id, label, hint, Icon }) => (
            <li key={id}>
              <button
                type="button"
                onClick={() => onNavigate(id)}
                aria-current={active === id ? "page" : undefined}
                className={`group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition ${
                  active === id ? "bg-accent-wash text-accent-ink" : "text-ink hover:bg-paper"
                }`}
              >
                <Icon aria-hidden className="size-5 shrink-0" />
                <span>
                  <span className="block font-bold">{label}</span>
                  <span className="block text-sm text-ink-soft">{hint}</span>
                </span>
              </button>
            </li>
          ))}
        </ul>
        <div className="mt-auto space-y-3 px-2">
          <div className="flex items-center justify-between rounded-xl border border-rule px-3 py-2" role="group" aria-label="Tamaño del texto">
            <span className="text-sm text-ink-soft">Texto {scale}%</span>
            <span className="flex gap-1">
              <button type="button" aria-label="Reducir texto" onClick={() => onScale(scale - 10)} className="rounded-md p-1.5 hover:bg-paper">
                <Minus aria-hidden className="size-4" />
              </button>
              <button type="button" aria-label="Agrandar texto" onClick={() => onScale(scale + 10)} className="rounded-md p-1.5 hover:bg-paper">
                <Plus aria-hidden className="size-4" />
              </button>
            </span>
          </div>
          <button type="button" onClick={onHelp} className="flex items-center gap-2 text-sm text-ink-soft hover:text-accent-ink">
            <CircleHelp aria-hidden className="size-4" /> Cómo funciona
          </button>
        </div>
      </nav>
      <main id="main" className="overflow-y-auto">
        {children}
      </main>
      <footer className="flex min-w-0 items-center gap-4 border-t border-rule bg-sheet/70 px-6 py-2 text-sm whitespace-nowrap text-ink-soft" aria-live="polite">
        <span className="flex items-center gap-2">
          <span aria-hidden className={`size-2.5 rounded-full ${status.dot}`} />
          {status.label}
          {down.length > 0 && connection !== "offline" && <span>· no responde: {down.join(", ")}</span>}
        </span>
        {offline && <span className="shrink-0 rounded-full bg-ochre-wash px-2 text-ochre">Modo demostración sin IA externa</span>}
        {library && (
          <span className="ml-auto min-w-0 truncate font-mono text-xs" title={library.path}>
            {library.counts.indexed} artículos listos · {library.path}
          </span>
        )}
      </footer>
    </div>
  );
}
