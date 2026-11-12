import { FileText, PenLine } from "lucide-react";
import { useEffect, useState } from "react";
import { ApiError, api } from "../api/client";
import type { DraftSummary } from "../api/types";
import { Banner, Button, ScreenHeader } from "../components/ui";

const DATE = new Intl.DateTimeFormat("es-PE", { dateStyle: "long", timeStyle: "short" });

export function DraftsScreen({ onOpen, onCompose }: { onOpen: (draftId: string) => void; onCompose: () => void }) {
  const [drafts, setDrafts] = useState<DraftSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .drafts()
      .then(setDrafts)
      .catch((failure) => setError(failure instanceof ApiError ? failure.message : "No pude cargar tus borradores."));
  }, []);

  return (
    <div className="mx-auto max-w-4xl px-10 py-10">
      <ScreenHeader eyebrow="Historial" title="Mis borradores">
        Retoma la revisión donde la dejaste o vuelve a exportar.
      </ScreenHeader>
      {error && <Banner kind="error" title={error} />}
      {drafts?.length === 0 && (
        <div className="rounded-2xl border border-dashed border-rule p-10 text-center">
          <p className="font-display text-xl">Aún no tienes borradores.</p>
          <Button variant="primary" className="mt-4" onClick={onCompose} icon={<PenLine aria-hidden className="size-4" />}>
            Pedir mi primer borrador
          </Button>
        </div>
      )}
      <ul className="space-y-3">
        {drafts?.map((draft, index) => (
          <li key={draft.draft_id} className="rise" style={{ animationDelay: `${index * 60}ms` }}>
            <button
              type="button"
              onClick={() => onOpen(draft.draft_id)}
              className="flex w-full items-start gap-4 rounded-2xl border border-rule bg-sheet p-5 text-left hover:border-accent"
            >
              <FileText aria-hidden className="mt-1 size-6 text-accent" />
              <span className="min-w-0 flex-1">
                <span className="font-display block text-xl font-semibold">{draft.title}</span>
                <span className="block text-sm text-ink-soft">{DATE.format(new Date(draft.created_at))}</span>
                <span className="mt-2 block text-sm">
                  {draft.stats.claims} afirmaciones · {draft.stats.sources} fuentes
                  {draft.stats.pending_review > 0 ? (
                    <span className="font-bold text-ochre"> · {draft.stats.pending_review} por revisar</span>
                  ) : (
                    <span className="font-bold text-moss"> · revisado</span>
                  )}
                </span>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
