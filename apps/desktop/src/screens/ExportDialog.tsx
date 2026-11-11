import { CheckCircle2, Download, FileText, FolderOpen, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { ApiError, api } from "../api/client";
import type { Draft, ExportFormat, ExportResult } from "../api/types";
import { Banner, Button } from "../components/ui";
import { inDesktop, openLocalFile, revealLocalFile } from "../platform";

const FORMATS: { value: ExportFormat; title: string; detail: string }[] = [
  { value: "docx", title: "Word (.docx)", detail: "Para seguir editando con tu equipo. Recomendado." },
  { value: "md", title: "Markdown + BibTeX", detail: "Para LaTeX u Overleaf mediante Pandoc." },
];

export function ExportDialog({ draft, open, onClose, pending }: { draft: Draft; open: boolean; onClose: () => void; pending: number }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [format, setFormat] = useState<ExportFormat>("docx");
  const [comments, setComments] = useState(true);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ExportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    if (open && !element.open) {
      setResult(null);
      setError(null);
      element.showModal();
    }
    if (!open && element.open) element.close();
  }, [open]);

  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      setResult(await api.exportDraft(draft.draft_id, format, comments));
    } catch (failure) {
      setError(failure instanceof ApiError ? failure.message : "No pude generar el archivo.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <dialog
      ref={dialog}
      onClose={onClose}
      aria-labelledby="export-title"
      className="m-auto w-[min(36rem,92vw)] rounded-2xl border border-rule bg-sheet p-0 text-ink shadow-2xl backdrop:bg-ink/40 backdrop:backdrop-blur-sm"
    >
      <div className="p-7">
        <div className="flex items-start justify-between gap-4">
          <h2 id="export-title" className="font-display text-2xl font-semibold">
            Exportar borrador
          </h2>
          <button type="button" onClick={onClose} aria-label="Cerrar" className="rounded-md p-1 hover:bg-paper">
            <X aria-hidden className="size-5" />
          </button>
        </div>

        {result ? (
          <div className="mt-5 space-y-4">
            <Banner kind="success" title="Listo. Guardé tu documento.">
              {result.pending_review > 0
                ? `${result.pending_review} afirmaciones van resaltadas con un comentario para que las revises en Word.`
                : "Incluye la bibliografía y la declaración de uso de IA."}
            </Banner>
            <ul className="space-y-2">
              {result.files.map((file) => (
                <li key={file.path} className="flex flex-wrap items-center gap-3 rounded-xl border border-rule bg-paper p-3">
                  <FileText aria-hidden className="size-5 text-accent" />
                  <span className="min-w-0 flex-1 truncate font-mono text-sm" title={file.path}>
                    {file.file_name}
                  </span>
                  {inDesktop() ? (
                    <>
                      <Button variant="primary" onClick={() => openLocalFile(file.path, api.absolute(file.url))}>
                        Abrir
                      </Button>
                      <Button variant="ghost" onClick={() => revealLocalFile(file.path)} icon={<FolderOpen aria-hidden className="size-4" />}>
                        Mostrar en carpeta
                      </Button>
                    </>
                  ) : (
                    <a
                      href={api.absolute(file.url)}
                      download={file.file_name}
                      className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 font-bold text-white"
                    >
                      <Download aria-hidden className="size-4" /> Descargar
                    </a>
                  )}
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <div className="mt-5 space-y-5">
            <fieldset>
              <legend className="mb-2 text-sm font-bold">Formato</legend>
              <div className="space-y-2">
                {FORMATS.map((option) => (
                  <label
                    key={option.value}
                    className={`flex cursor-pointer gap-3 rounded-xl border p-3 ${format === option.value ? "border-accent bg-accent-wash" : "border-rule"}`}
                  >
                    <input
                      type="radio"
                      name="format"
                      value={option.value}
                      checked={format === option.value}
                      onChange={() => setFormat(option.value)}
                      className="mt-1 accent-[var(--accent)]"
                    />
                    <span>
                      <span className="block font-bold">{option.title}</span>
                      <span className="block text-sm text-ink-soft">{option.detail}</span>
                    </span>
                  </label>
                ))}
              </div>
            </fieldset>
            {format === "docx" && (
              <label className="flex items-start gap-3">
                <input type="checkbox" checked={comments} onChange={(event) => setComments(event.target.checked)} className="mt-1 size-4 accent-[var(--accent)]" />
                <span>
                  <span className="block font-bold">Incluir comentarios de revisión</span>
                  <span className="block text-sm text-ink-soft">Lo pendiente aparece resaltado y con la fuente en un comentario de Word.</span>
                </span>
              </label>
            )}
            {pending > 0 && (
              <Banner kind="warning" title={`Aún quedan ${pending} afirmaciones sin revisar`}>
                Puedes exportar igual; quedarán marcadas en el documento.
              </Banner>
            )}
            {error && <Banner kind="error" title={error} />}
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={onClose}>
                Seguir revisando
              </Button>
              <Button variant="primary" onClick={run} busy={busy} icon={<CheckCircle2 aria-hidden className="size-4" />}>
                Exportar
              </Button>
            </div>
          </div>
        )}
      </div>
    </dialog>
  );
}
