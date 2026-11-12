import { CheckCircle2, FileWarning, FolderOpen, PenLine, RefreshCw, ScanLine, TriangleAlert } from "lucide-react";
import { useReducer, useState, type FormEvent } from "react";
import { ApiError, api } from "../api/client";
import type { LibrarySummary, Paper } from "../api/types";
import { useJobEvents } from "../api/useJobEvents";
import { Banner, Button, ProgressBar, ScreenHeader } from "../components/ui";
import { inDesktop, pickFolder } from "../platform";
import { ingestionReducer, initialIngestion } from "../state/ingestion";

const STATUS = {
  indexed: { label: "Listo para citar", tone: "text-moss", Icon: CheckCircle2 },
  needs_ocr: { label: "Escaneado, sin texto", tone: "text-ochre", Icon: ScanLine },
  failed: { label: "No se pudo abrir", tone: "text-brick", Icon: FileWarning },
} as const;

const HELP: Record<Paper["status"], string> = {
  indexed: "",
  needs_ocr: "Pásalo por OCR (por ejemplo, “Reconocer texto” en tu lector de PDF), guárdalo en la misma carpeta y vuelve a indexar.",
  failed: "Vuelve a descargarlo desde la revista o el repositorio y reemplázalo en la carpeta.",
};

function authorsLine(paper: Paper): string {
  const authors = paper.metadata.authors.map((author) => author.family);
  if (!authors.length) return "Autores sin identificar";
  return authors.length > 2 ? `${authors[0]} et al.` : authors.join(" y ");
}

function MetadataForm({ paper, onSaved }: { paper: Paper; onSaved: () => void }) {
  const [authors, setAuthors] = useState(paper.metadata.authors.map((a) => `${a.family}, ${a.given}`).join("; "));
  const [year, setYear] = useState(paper.metadata.year?.toString() ?? "");
  const [title, setTitle] = useState(paper.metadata.title ?? "");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.patchPaper(paper.paper_id, {
        title: title.trim() || null,
        year: year ? Number(year) : null,
        authors: authors
          .split(";")
          .map((name) => name.trim())
          .filter(Boolean)
          .map((name) => {
            const [family, given = ""] = name.split(",").map((part) => part.trim());
            return { family, given };
          }),
      });
      onSaved();
    } catch (failure) {
      setError(failure instanceof ApiError ? failure.message : "No pude guardar los datos.");
    } finally {
      setSaving(false);
    }
  };

  const field = "mt-1 w-full rounded-lg border border-rule bg-paper px-3 py-2";
  return (
    <form onSubmit={submit} className="mt-3 grid gap-3 rounded-xl border border-rule bg-paper/60 p-4 md:grid-cols-[2fr_1fr]">
      <label className="md:col-span-2">
        <span className="text-sm font-bold">Título</span>
        <input className={field} value={title} onChange={(event) => setTitle(event.target.value)} />
      </label>
      <label>
        <span className="text-sm font-bold">Autores</span>
        <span className="block text-xs text-ink-soft">Apellido, Nombre; Apellido, Nombre</span>
        <input className={field} value={authors} onChange={(event) => setAuthors(event.target.value)} />
      </label>
      <label>
        <span className="text-sm font-bold">Año</span>
        <span className="block text-xs text-ink-soft">Año de publicación</span>
        <input className={field} inputMode="numeric" pattern="\d{4}" value={year} onChange={(event) => setYear(event.target.value)} />
      </label>
      {error && <p role="alert" className="text-brick md:col-span-2">{error}</p>}
      <div className="md:col-span-2">
        <Button type="submit" variant="primary" busy={saving}>
          Guardar datos de cita
        </Button>
      </div>
    </form>
  );
}

function PaperRow({ paper, onChanged }: { paper: Paper; onChanged: () => void }) {
  const [editing, setEditing] = useState(false);
  const { label, tone, Icon } = STATUS[paper.status];
  const hasIssue = paper.issues.length > 0;
  return (
    <li className="border-b border-rule/70 py-4 last:border-none">
      <div className="flex items-start gap-4">
        <Icon aria-hidden className={`mt-1 size-5 shrink-0 ${tone}`} />
        <div className="min-w-0 flex-1">
          <p className="font-display text-[1.05rem] leading-snug font-medium">{paper.metadata.title ?? paper.file_name}</p>
          <p className="mt-0.5 text-sm text-ink-soft">
            {authorsLine(paper)} · {paper.metadata.year ?? "año desconocido"}
            {paper.metadata.doi && <span className="font-mono"> · doi:{paper.metadata.doi}</span>}
          </p>
          {hasIssue && (
            <div className="mt-2 text-sm">
              {paper.issues.map((issue) => (
                <p key={issue}>{issue}</p>
              ))}
              {HELP[paper.status] && <p className="mt-1 text-ink-soft">{HELP[paper.status]}</p>}
            </div>
          )}
          {editing && (
            <MetadataForm
              paper={paper}
              onSaved={() => {
                setEditing(false);
                onChanged();
              }}
            />
          )}
        </div>
        <div className="flex shrink-0 flex-col items-end gap-2">
          <span className={`text-sm font-bold ${tone}`}>{label}</span>
          {paper.status === "indexed" && hasIssue && !editing && (
            <Button variant="ghost" className="min-h-8 px-2 text-sm" onClick={() => setEditing(true)}>
              Completar datos
            </Button>
          )}
        </div>
      </div>
    </li>
  );
}

function FolderPicker({ onOpen, busy }: { onOpen: (path: string) => void; busy: boolean }) {
  const [path, setPath] = useState("");
  const choose = async () => {
    const selected = await pickFolder();
    if (selected) onOpen(selected);
  };
  return (
    <div className="rise rounded-2xl border-2 border-dashed border-rule bg-sheet/70 p-10 text-center">
      <FolderOpen aria-hidden className="mx-auto size-12 text-accent" />
      <h2 className="font-display mt-4 text-2xl font-semibold">¿Dónde guardas tus artículos?</h2>
      <p className="mx-auto mt-2 max-w-[48ch] text-ink-soft">
        Elige la carpeta con tus PDFs. Incluyo las subcarpetas y no modifico ni muevo tus archivos.
      </p>
      {inDesktop() ? (
        <Button variant="primary" className="mt-6 px-6" onClick={choose} busy={busy} icon={<FolderOpen aria-hidden className="size-4" />}>
          Elegir carpeta
        </Button>
      ) : (
        <form
          className="mx-auto mt-6 flex max-w-xl gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            if (path.trim()) onOpen(path.trim());
          }}
        >
          <label className="sr-only" htmlFor="folder-path">
            Ruta de la carpeta
          </label>
          <input
            id="folder-path"
            value={path}
            onChange={(event) => setPath(event.target.value)}
            placeholder="C:\Users\tu-usuario\Documents\Articulos"
            className="flex-1 rounded-lg border border-rule bg-paper px-3 py-2 font-mono text-sm"
          />
          <Button type="submit" variant="primary" busy={busy}>
            Abrir
          </Button>
        </form>
      )}
    </div>
  );
}

export function LibraryScreen({
  library,
  ingestJobId,
  onOpened,
  onReset,
  onIngestJob,
  onRefresh,
  onCompose,
}: {
  library: LibrarySummary | null;
  ingestJobId: string | null;
  onOpened: (library: LibrarySummary, jobId: string) => void;
  onReset: () => void;
  onIngestJob: (jobId: string | null) => void;
  onRefresh: () => Promise<void>;
  onCompose: () => void;
}) {
  const [progress, dispatch] = useReducer(ingestionReducer, undefined, initialIngestion);
  const [error, setError] = useState<string | null>(null);
  const [opening, setOpening] = useState(false);
  const [filter, setFilter] = useState<"all" | "issues">("all");

  useJobEvents(ingestJobId, (event) => {
    dispatch(event);
    if (event.type === "job.completed" || event.type === "job.failed") {
      onRefresh().then(() => event.type === "job.completed" && onIngestJob(null));
    }
  });

  const open = async (path: string) => {
    setOpening(true);
    setError(null);
    try {
      const result = await api.openLibrary(path);
      onOpened(result.library, result.job_id);
    } catch (failure) {
      setError(failure instanceof ApiError ? failure.message : "No pude abrir esa carpeta.");
    } finally {
      setOpening(false);
    }
  };

  const reindex = async () => {
    if (!library) return;
    try {
      const { job_id } = await api.reindex(library.library_id);
      onIngestJob(job_id);
    } catch (failure) {
      setError(failure instanceof ApiError ? failure.message : "No pude volver a leer la carpeta.");
    }
  };

  const indexing = Boolean(ingestJobId) && progress.status === "running";
  const papers = [...(indexing ? progress.papers : (library?.papers ?? []))].sort(
    (a, b) => Number(b.issues.length > 0) - Number(a.issues.length > 0) || a.file_name.localeCompare(b.file_name),
  );
  const visible = filter === "issues" ? papers.filter((paper) => paper.issues.length) : papers;
  const counts = library?.counts;
  const problems = papers.filter((paper) => paper.issues.length).length;

  return (
    <div className="mx-auto max-w-5xl px-10 py-10">
      <ScreenHeader eyebrow="Paso 1 · Biblioteca" title={library ? "Tu biblioteca de artículos" : "Empecemos por tus artículos"}>
        {library
          ? "Esto es lo que encontré en tu carpeta. Los artículos con problemas no se usarán para citar hasta que los resuelvas."
          : "El asistente solo escribe a partir de los PDFs que tú eliges: así cada afirmación del borrador tiene una fuente tuya."}
      </ScreenHeader>

      {error && (
        <div className="mb-6">
          <Banner kind="error" title={error} />
        </div>
      )}

      {!library && <FolderPicker onOpen={open} busy={opening} />}

      {library && indexing && (
        <section aria-labelledby="indexing-title" className="rise mb-8 rounded-2xl border border-rule bg-sheet p-6">
          <div className="flex items-baseline justify-between gap-4">
            <h2 id="indexing-title" className="text-lg font-bold">
              Leyendo {progress.processed} de {progress.total || "…"} artículos
            </h2>
            <span className="truncate font-mono text-sm text-ink-soft">{progress.current}</span>
          </div>
          <div className="mt-4">
            <ProgressBar value={progress.total ? progress.processed / progress.total : 0} label="Progreso de lectura de la carpeta" />
          </div>
          <p className="mt-4 text-ink-soft">
            Puedes ir escribiendo tu solicitud mientras termino; usaré los artículos que ya estén listos.{" "}
            <button type="button" onClick={onCompose} className="font-bold text-accent-ink underline underline-offset-4">
              Escribir solicitud
            </button>
          </p>
        </section>
      )}

      {library && !indexing && progress.status === "failed" && progress.errorCode === "empty_folder" && (
        <div className="mb-8">
          <Banner kind="warning" title="No encontré PDFs en esta carpeta" actions={<Button onClick={onReset}>Elegir otra carpeta</Button>}>
            Revisa que sea la carpeta donde descargas tus artículos. También busco dentro de las subcarpetas.
          </Banner>
        </div>
      )}

      {library && counts && !indexing && (
        <section aria-label="Resumen de la biblioteca" className="rise mb-8 grid gap-4 md:grid-cols-4">
          <div className="rounded-2xl border border-moss/30 bg-moss-wash/60 p-5 md:col-span-2">
            <p className="font-display text-5xl font-semibold text-moss">{counts.indexed}</p>
            <p className="mt-1 font-bold">artículos listos para citar</p>
            <p className="text-sm text-ink-soft">de {counts.total} PDFs en la carpeta</p>
          </div>
          <div className="rounded-2xl border border-rule bg-sheet p-5">
            <p className="font-display text-3xl font-semibold">{counts.needs_ocr + counts.failed}</p>
            <p className="mt-1 text-sm font-bold">no se pueden leer</p>
            <p className="text-sm text-ink-soft">escaneados o dañados</p>
          </div>
          <div className="rounded-2xl border border-rule bg-sheet p-5">
            <p className="font-display text-3xl font-semibold">{counts.incomplete_metadata}</p>
            <p className="mt-1 text-sm font-bold">con datos incompletos</p>
            <p className="text-sm text-ink-soft">puedes completarlos aquí</p>
          </div>
        </section>
      )}

      {library && !indexing && (
        <div className="mb-6 flex flex-wrap items-center gap-3">
          <Button variant="primary" onClick={onCompose} icon={<PenLine aria-hidden className="size-4" />} disabled={!counts?.indexed}>
            Pedir un borrador
          </Button>
          <Button onClick={reindex} icon={<RefreshCw aria-hidden className="size-4" />}>
            Volver a leer la carpeta
          </Button>
          <Button variant="ghost" onClick={onReset} icon={<FolderOpen aria-hidden className="size-4" />}>
            Cambiar de carpeta
          </Button>
        </div>
      )}

      {papers.length > 0 && (
        <section aria-labelledby="papers-title" className="rounded-2xl border border-rule bg-sheet px-6 pt-4 pb-2">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-rule pb-3">
            <h2 id="papers-title" className="font-bold">
              Artículos
            </h2>
            <div role="radiogroup" aria-label="Filtrar artículos" className="flex rounded-lg border border-rule p-0.5 text-sm">
              {(
                [
                  ["all", `Todos (${papers.length})`],
                  ["issues", `Con algo por resolver (${problems})`],
                ] as const
              ).map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  role="radio"
                  aria-checked={filter === value}
                  onClick={() => setFilter(value)}
                  className={`rounded-md px-3 py-1 ${filter === value ? "bg-accent-wash font-bold text-accent-ink" : "text-ink-soft"}`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          {visible.length === 0 ? (
            <p className="flex items-center gap-2 py-6 text-ink-soft">
              <TriangleAlert aria-hidden className="size-4" /> Nada por resolver: todos tus artículos están listos.
            </p>
          ) : (
            <ul>
              {visible.map((paper) => (
                <PaperRow key={paper.paper_id} paper={paper} onChanged={onRefresh} />
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
}
