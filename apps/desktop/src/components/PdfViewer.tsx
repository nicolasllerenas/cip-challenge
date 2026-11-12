import { ChevronLeft, ChevronRight, ExternalLink, Loader2, Minus, Plus, X } from "lucide-react";
import { GlobalWorkerOptions, getDocument, type PDFDocumentProxy } from "pdfjs-dist";
import workerUrl from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { api } from "../api/client";
import type { Passage } from "../api/types";
import { openLocalFile } from "../platform";
import { passageBoxes, type TextBox } from "../state/highlight";
import { Button } from "./ui";

GlobalWorkerOptions.workerSrc = workerUrl;

interface Highlight {
  left: number;
  top: number;
  width: number;
  height: number;
}

type Status = { kind: "loading" } | { kind: "ready"; pages: number } | { kind: "error" };

async function fetchPdf(paperId: string): Promise<Uint8Array> {
  const response = await fetch(api.paperFileUrl(paperId));
  if (!response.ok) throw new Error("pdf unavailable");
  return new Uint8Array(await response.arrayBuffer());
}

export function PdfViewer({
  passage,
  citation,
  onClose,
}: {
  passage: Passage;
  citation: string;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const [documentProxy, setDocumentProxy] = useState<PDFDocumentProxy | null>(null);
  const [status, setStatus] = useState<Status>({ kind: "loading" });
  const [page, setPage] = useState(passage.page);
  const [zoom, setZoom] = useState(1.25);
  const [highlights, setHighlights] = useState<Highlight[]>([]);

  useEffect(() => {
    dialog.current?.showModal();
  }, []);

  useEffect(() => {
    let alive = true;
    let task: ReturnType<typeof getDocument> | null = null;
    fetchPdf(passage.paper_id)
      .then((data) => {
        task = getDocument({ data });
        return task.promise;
      })
      .then((loaded) => {
        if (!alive) return;
        setDocumentProxy(loaded);
        setStatus({ kind: "ready", pages: loaded.numPages });
      })
      .catch(() => alive && setStatus({ kind: "error" }));
    return () => {
      alive = false;
      void task?.destroy();
    };
  }, [passage.paper_id]);

  useEffect(() => {
    const target = canvas.current;
    if (!documentProxy || !target) return;
    let cancelled = false;
    const render = async () => {
      const pdfPage = await documentProxy.getPage(page);
      const viewport = pdfPage.getViewport({ scale: zoom });
      const ratio = window.devicePixelRatio || 1;
      target.width = Math.floor(viewport.width * ratio);
      target.height = Math.floor(viewport.height * ratio);
      target.style.width = `${viewport.width}px`;
      target.style.height = `${viewport.height}px`;
      await pdfPage.render({ canvas: target, viewport, transform: ratio === 1 ? undefined : [ratio, 0, 0, ratio, 0, 0] })
        .promise;
      if (cancelled) return;
      const content = await pdfPage.getTextContent();
      const boxes: TextBox[] = content.items
        .filter((item) => "str" in item)
        .map((item) => {
          const [, , , , x, y] = item.transform as number[];
          const height = item.height || Math.hypot(item.transform[2], item.transform[3]);
          return { text: item.str, x, y, width: item.width, height };
        });
      const matches = page === passage.page ? passageBoxes(boxes, passage.text) : [];
      setHighlights(
        matches.map((box) => {
          const [x1, y1] = viewport.convertToViewportPoint(box.x, box.y - box.height * 0.25);
          const [x2, y2] = viewport.convertToViewportPoint(box.x + box.width, box.y + box.height);
          return { left: Math.min(x1, x2), top: Math.min(y1, y2), width: Math.abs(x2 - x1), height: Math.abs(y2 - y1) };
        }),
      );
    };
    render().catch(() => setStatus({ kind: "error" }));
    return () => {
      cancelled = true;
    };
  }, [documentProxy, page, zoom, passage.page, passage.text]);

  const pages = status.kind === "ready" ? status.pages : 0;
  const go = (next: number) => setPage(Math.min(Math.max(1, next), pages || 1));
  const keys = (event: KeyboardEvent) => {
    if (event.key === "ArrowLeft") go(page - 1);
    if (event.key === "ArrowRight") go(page + 1);
  };
  const external = () => openLocalFile(passage.file_path, api.paperUrl(passage.paper_id, page));
  const title = passage.metadata.title ?? passage.file_name;

  return (
    <dialog
      ref={dialog}
      onClose={onClose}
      onKeyDown={keys}
      aria-labelledby="pdf-title"
      className="m-auto flex h-[92vh] w-[min(72rem,94vw)] flex-col overflow-hidden rounded-2xl border border-rule bg-sheet p-0 text-ink shadow-2xl backdrop:bg-ink/50 backdrop:backdrop-blur-sm"
    >
      <header className="flex flex-wrap items-center gap-3 border-b border-rule px-5 py-3">
        <div className="min-w-0 flex-1">
          <p className="font-mono text-xs text-accent-ink">{citation}</p>
          <h2 id="pdf-title" className="font-display truncate text-lg font-semibold">
            {title}
          </h2>
        </div>
        <div role="group" aria-label="Páginas" className="flex items-center gap-1">
          <button type="button" aria-label="Página anterior" onClick={() => go(page - 1)} disabled={page <= 1} className="rounded-md p-1.5 hover:bg-paper disabled:opacity-40">
            <ChevronLeft aria-hidden className="size-5" />
          </button>
          <span className="min-w-24 text-center font-mono text-sm" aria-live="polite">
            p. {page}
            {pages ? ` de ${pages}` : ""}
          </span>
          <button type="button" aria-label="Página siguiente" onClick={() => go(page + 1)} disabled={!pages || page >= pages} className="rounded-md p-1.5 hover:bg-paper disabled:opacity-40">
            <ChevronRight aria-hidden className="size-5" />
          </button>
        </div>
        <div role="group" aria-label="Zoom" className="flex items-center gap-1">
          <button type="button" aria-label="Alejar" onClick={() => setZoom((value) => Math.max(0.75, value - 0.25))} className="rounded-md p-1.5 hover:bg-paper">
            <Minus aria-hidden className="size-4" />
          </button>
          <span className="w-12 text-center font-mono text-sm">{Math.round(zoom * 100)}%</span>
          <button type="button" aria-label="Acercar" onClick={() => setZoom((value) => Math.min(2.5, value + 0.25))} className="rounded-md p-1.5 hover:bg-paper">
            <Plus aria-hidden className="size-4" />
          </button>
        </div>
        <Button variant="ghost" onClick={external} icon={<ExternalLink aria-hidden className="size-4" />}>
          Abrir en mi lector
        </Button>
        <button type="button" onClick={() => dialog.current?.close()} aria-label="Cerrar" className="rounded-md p-1.5 hover:bg-paper">
          <X aria-hidden className="size-5" />
        </button>
      </header>
      <div className="grid min-h-0 flex-1 grid-cols-[minmax(0,1fr)_20rem]">
        <div className="overflow-auto bg-ink/5 p-6">
          {status.kind === "loading" && (
            <p className="flex items-center gap-2 text-ink-soft">
              <Loader2 aria-hidden className="size-4 animate-spin" /> Abriendo el PDF…
            </p>
          )}
          {status.kind === "error" && (
            <div role="alert" className="max-w-md rounded-xl border border-brick/40 bg-brick-wash p-4">
              <p className="font-bold">No pude abrir el PDF.</p>
              <p className="mt-1 text-ink-soft">¿Se movió o renombró el archivo? Puedes intentar con tu lector de PDF.</p>
            </div>
          )}
          <div className={`relative mx-auto w-fit bg-white shadow-lg ${status.kind === "ready" ? "" : "hidden"}`}>
            <canvas ref={canvas} aria-label={`Página ${page} de ${title}`} role="img" />
            {highlights.map((box, index) => (
              <span
                key={index}
                aria-hidden
                className="pointer-events-none absolute rounded-sm bg-accent/25 mix-blend-multiply ring-1 ring-accent/50"
                style={{ left: box.left - 2, top: box.top - 1, width: box.width + 4, height: box.height + 2 }}
              />
            ))}
          </div>
        </div>
        <aside className="overflow-y-auto border-l border-rule p-5" aria-label="Pasaje citado">
          <p className="font-mono text-xs tracking-[0.18em] text-accent-ink uppercase">Pasaje citado · p. {passage.page}</p>
          <blockquote className="font-display mt-3 border-l-2 border-accent/60 pl-3 leading-relaxed">{passage.text}</blockquote>
          <p className="mt-4 text-sm text-ink-soft" aria-live="polite">
            {page !== passage.page
              ? `Estás en la página ${page}. El pasaje está en la ${passage.page}.`
              : highlights.length
                ? `Resalté ${highlights.length} líneas del pasaje en la página.`
                : status.kind === "ready"
                  ? "No pude ubicar el pasaje exacto en el dibujo de la página; el texto de la izquierda es el que se citó."
                  : ""}
          </p>
          {page !== passage.page && (
            <Button className="mt-3" onClick={() => go(passage.page)}>
              Volver a la página {passage.page}
            </Button>
          )}
          <p className="mt-6 text-xs text-ink-soft">Usa ← y → para cambiar de página y Esc para cerrar.</p>
        </aside>
      </div>
    </dialog>
  );
}
