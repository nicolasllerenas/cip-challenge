import { ArrowDownToLine, Check, ExternalLink, FileText, Info, Pencil, RotateCcw, SkipForward, Trash2 } from "lucide-react";
import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import { ApiError, api, type ClaimAction } from "../api/client";
import type { Claim, Draft, Passage } from "../api/types";
import { Banner, Button, Eyebrow, Kbd, VerdictBadge } from "../components/ui";
import { openExternal, openLocalFile } from "../platform";
import { allClaims, citationLabels, needsReview, parenthetical, sharedTerms } from "../state/citations";
import { ExportDialog } from "./ExportDialog";

const WORD = /([\p{L}\d]+)/u;

function Highlighted({ text, terms }: { text: string; terms: Set<string> }) {
  return (
    <>
      {text.split(WORD).map((part, index) =>
        terms.has(part.toLowerCase()) ? (
          <mark key={index} className="rounded bg-accent-wash px-0.5 text-ink">
            {part}
          </mark>
        ) : (
          <Fragment key={index}>{part}</Fragment>
        ),
      )}
    </>
  );
}

function claimTone(claim: Claim): string {
  if (claim.review === "removed") return "text-ink-soft line-through decoration-1 opacity-60";
  if (claim.review === "accepted") return "";
  if (claim.verdict === "partial") return "underline-partial";
  if (claim.verdict === "unsupported") return "underline-unsupported";
  return "";
}

const VERDICT_SPOKEN = { supported: "respaldada", partial: "con respaldo parcial", unsupported: "sin respaldo" };

function SourceCard({ passage, label, claim }: { passage: Passage; label: string; claim: Claim }) {
  const terms = useMemo(() => sharedTerms(claim.text, passage.text), [claim.text, passage.text]);
  return (
    <li className="rise rounded-xl border border-rule bg-paper/70 p-4">
      <div className="flex items-baseline justify-between gap-2">
        <p className="font-mono text-xs font-medium text-accent-ink">{label}</p>
        <p className="rounded-full bg-sheet px-2 font-mono text-xs">p. {passage.page}</p>
      </div>
      <p className="font-display mt-1 leading-snug font-medium">{passage.metadata.title ?? passage.file_name}</p>
      {passage.metadata.journal && <p className="text-xs text-ink-soft italic">{passage.metadata.journal}</p>}
      <blockquote className="font-display mt-3 border-l-2 border-accent/60 pl-3 text-[0.95rem] leading-relaxed">
        <Highlighted text={passage.text} terms={terms} />
      </blockquote>
      <div className="mt-3 flex flex-wrap gap-3 text-sm">
        <button
          type="button"
          onClick={() => openLocalFile(passage.file_path, api.paperUrl(passage.paper_id, passage.page))}
          className="inline-flex items-center gap-1 font-bold text-accent-ink hover:underline"
        >
          <FileText aria-hidden className="size-4" /> Abrir PDF (p. {passage.page})
        </button>
        {passage.metadata.doi && (
          <button
            type="button"
            onClick={() => openExternal(`https://doi.org/${passage.metadata.doi}`)}
            className="inline-flex items-center gap-1 text-ink-soft hover:underline"
          >
            <ExternalLink aria-hidden className="size-4" /> doi:{passage.metadata.doi}
          </button>
        )}
      </div>
    </li>
  );
}

function EvidencePanel({
  draft,
  claim,
  labels,
  onAction,
  onNext,
  busy,
  remaining,
  editing,
  setEditing,
}: {
  draft: Draft;
  claim: Claim | null;
  labels: Map<string, string>;
  onAction: (action: ClaimAction, text?: string) => void;
  onNext: () => void;
  busy: boolean;
  remaining: number;
  editing: boolean;
  setEditing: (editing: boolean) => void;
}) {
  const [text, setText] = useState("");
  useEffect(() => {
    setText(claim?.text ?? "");
  }, [claim?.claim_id, claim?.text]);

  if (!claim) {
    return (
      <div className="space-y-5">
        <p className="font-display text-xl">Selecciona cualquier afirmación del texto para ver de qué página sale.</p>
        <ul className="space-y-2 text-sm">
          <li className="flex items-center gap-3">
            <VerdictBadge verdict="supported" /> La fuente dice exactamente esto.
          </li>
          <li className="flex items-center gap-3">
            <VerdictBadge verdict="partial" /> La fuente apoya solo una parte.
          </li>
          <li className="flex items-center gap-3">
            <VerdictBadge verdict="unsupported" /> No encontré respaldo suficiente.
          </li>
        </ul>
        {remaining > 0 && (
          <Button variant="primary" onClick={onNext} icon={<SkipForward aria-hidden className="size-4" />}>
            Ir a la primera por revisar
          </Button>
        )}
      </div>
    );
  }

  const passages = claim.citations
    .map((link) => ({ link, passage: draft.evidence[link.passage_id] }))
    .filter((item) => item.passage);

  return (
    <div>
      <Eyebrow>Afirmación seleccionada</Eyebrow>
      {editing ? (
        <form
          className="mt-2"
          onSubmit={(event) => {
            event.preventDefault();
            onAction("edit", text);
          }}
        >
          <label htmlFor="claim-text" className="sr-only">
            Texto de la afirmación
          </label>
          <textarea
            id="claim-text"
            autoFocus
            value={text}
            onChange={(event) => setText(event.target.value)}
            rows={4}
            className="font-display w-full rounded-xl border border-accent bg-sheet p-3 text-lg leading-snug"
          />
          <div className="mt-2 flex gap-2">
            <Button type="submit" variant="primary" busy={busy} disabled={!text.trim()}>
              Guardar cambio
            </Button>
            <Button variant="ghost" onClick={() => setEditing(false)}>
              Descartar
            </Button>
          </div>
        </form>
      ) : (
        <p className="font-display mt-2 text-xl leading-snug">{claim.text}</p>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <VerdictBadge verdict={claim.verdict} />
        {claim.review === "accepted" && <span className="text-sm font-bold text-moss">Revisada por ti</span>}
        {claim.review === "removed" && <span className="text-sm font-bold text-ink-soft">Quitada del borrador</span>}
      </div>

      {claim.rationale && claim.verdict !== "supported" && (
        <div className="mt-4 flex gap-2 rounded-xl bg-ochre-wash p-3 text-sm">
          <Info aria-hidden className="mt-0.5 size-4 shrink-0 text-ochre" />
          <p>
            <span className="font-bold">Por qué la marqué: </span>
            {claim.rationale}
          </p>
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        {claim.review === "removed" ? (
          <Button onClick={() => onAction("restore")} busy={busy} icon={<RotateCcw aria-hidden className="size-4" />}>
            Restaurar
          </Button>
        ) : (
          <>
            {needsReview(claim) && (
              <Button variant="primary" onClick={() => onAction("accept")} busy={busy} icon={<Check aria-hidden className="size-4" />}>
                Aceptar <Kbd>A</Kbd>
              </Button>
            )}
            <Button onClick={() => setEditing(true)} icon={<Pencil aria-hidden className="size-4" />}>
              Editar <Kbd>E</Kbd>
            </Button>
            <Button variant="danger" onClick={() => onAction("remove")} busy={busy} icon={<Trash2 aria-hidden className="size-4" />}>
              Quitar <Kbd>X</Kbd>
            </Button>
          </>
        )}
        {remaining > 0 && (
          <Button variant="ghost" onClick={onNext} icon={<SkipForward aria-hidden className="size-4" />}>
            Siguiente <Kbd>N</Kbd>
          </Button>
        )}
      </div>

      <h3 className="mt-6 mb-2 font-bold">
        {passages.length ? `De dónde sale (${passages.length})` : "Esta afirmación no cita ninguna fuente"}
      </h3>
      <ul className="space-y-3">
        {passages.map(({ link, passage }) => (
          <SourceCard key={link.passage_id} passage={passage} label={labels.get(link.paper_id) ?? passage.file_name} claim={claim} />
        ))}
      </ul>
    </div>
  );
}

export function ReviewScreen({ draftId }: { draftId: string }) {
  const [draft, setDraft] = useState<Draft | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [onlyPending, setOnlyPending] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    setDraft(null);
    api
      .draft(draftId)
      .then(setDraft)
      .catch((failure) => setError(failure instanceof ApiError ? failure.message : "No pude abrir el borrador."));
  }, [draftId]);

  const labels = useMemo(() => citationLabels(draft?.references ?? []), [draft?.references]);
  const claims = useMemo(() => (draft ? allClaims(draft) : []), [draft]);
  const flagged = claims.filter((claim) => claim.verdict !== "supported");
  const pending = flagged.filter((claim) => claim.review === "pending");
  const current = claims.find((claim) => claim.claim_id === selected) ?? null;

  const select = (claimId: string) => {
    setSelected(claimId);
    setEditing(false);
  };

  const goNext = useCallback(() => {
    if (!pending.length) return;
    const index = pending.findIndex((claim) => claim.claim_id === selected);
    const next = pending[(index + 1) % pending.length];
    setSelected(next.claim_id);
    setEditing(false);
    document.getElementById(`claim-${next.claim_id}`)?.scrollIntoView({ block: "center", behavior: "smooth" });
  }, [pending, selected]);

  const act = useCallback(
    async (action: ClaimAction, text?: string) => {
      if (!draft || !current) return;
      setBusy(true);
      setError(null);
      try {
        setDraft(await api.review(draft.draft_id, current.claim_id, action, text));
        setEditing(false);
      } catch (failure) {
        setError(failure instanceof ApiError ? failure.message : "No pude guardar tu revisión.");
      } finally {
        setBusy(false);
      }
    },
    [draft, current],
  );

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      if (["TEXTAREA", "INPUT"].includes(target.tagName) || event.metaKey || event.ctrlKey || exporting) return;
      const key = event.key.toLowerCase();
      if (key === "n") goNext();
      if (key === "a" && current && needsReview(current)) act("accept");
      if (key === "x" && current && current.review !== "removed") act("remove");
      if (key === "e" && current && current.review !== "removed") {
        event.preventDefault();
        setEditing(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [goNext, act, current, exporting]);

  if (error && !draft) return <div className="p-10"><Banner kind="error" title={error} /></div>;
  if (!draft) return <p className="p-10 text-ink-soft">Abriendo tu borrador…</p>;

  const reviewed = flagged.length - pending.length;

  return (
    <div className="grid min-h-full grid-cols-[minmax(0,1fr)_27rem]">
      <article className="px-12 py-10" aria-labelledby="draft-title">
        <div className="sticky top-0 z-10 -mx-12 mb-8 flex items-center gap-3 border-b border-rule bg-paper/90 px-12 py-3 backdrop-blur">
          <span className="text-sm whitespace-nowrap">
            <strong>{claims.filter((claim) => claim.review !== "removed").length}</strong> afirmaciones ·{" "}
            <strong>{draft.references.length}</strong> fuentes
          </span>
          {flagged.length > 0 && (
            <span className="rounded-full bg-ochre-wash px-3 py-0.5 text-sm font-bold whitespace-nowrap text-ochre">
              Revisaste {reviewed} de {flagged.length}
            </span>
          )}
          <label className="ml-auto flex items-center gap-2 text-sm whitespace-nowrap">
            <input type="checkbox" checked={onlyPending} onChange={(event) => setOnlyPending(event.target.checked)} className="size-4 accent-[var(--accent)]" />
            Solo pendientes
          </label>
          <Button variant="primary" onClick={() => setExporting(true)} icon={<ArrowDownToLine aria-hidden className="size-4" />}>
            Exportar
          </Button>
        </div>

        <Eyebrow>Paso 4 · Revisión</Eyebrow>
        <h1 id="draft-title" tabIndex={-1} data-screen-title className="font-display mt-2 max-w-[24ch] text-[2.6rem] leading-[1.08] font-semibold outline-none">
          {draft.title}
        </h1>
        <p className="mt-3 max-w-[70ch] text-sm text-ink-soft">
          Borrador generado con IA a partir de tu biblioteca. Las afirmaciones subrayadas necesitan tu criterio: haz clic para ver
          la fuente y decidir.
        </p>
        {error && (
          <div className="mt-4">
            <Banner kind="error" title={error} />
          </div>
        )}

        <div className="font-display mt-8 max-w-[70ch] text-[1.17rem] leading-[1.75]">
          {draft.sections.map((section) => (
            <section key={section.section_id} aria-labelledby={`h-${section.section_id}`} className="mb-8">
              <h2 id={`h-${section.section_id}`} className="mb-3 text-2xl font-semibold">
                {section.heading}
              </h2>
              {section.paragraphs.map((paragraph, index) => (
                <p key={index} className="mb-4">
                  {paragraph.claims.map((claim) => {
                    const citation = parenthetical(claim, labels);
                    const dim = onlyPending && !needsReview(claim);
                    return (
                      <Fragment key={claim.claim_id}>
                        <span
                          id={`claim-${claim.claim_id}`}
                          role="button"
                          tabIndex={0}
                          onClick={() => select(claim.claim_id)}
                          onKeyDown={(event) => {
                            if (event.key === "Enter" || event.key === " ") {
                              event.preventDefault();
                              select(claim.claim_id);
                            }
                          }}
                          aria-pressed={selected === claim.claim_id}
                          aria-label={`${claim.text} ${citation}. Afirmación ${VERDICT_SPOKEN[claim.verdict]}${claim.review === "removed" ? ", quitada" : ""}`}
                          className={`cursor-pointer rounded-md px-0.5 box-decoration-clone transition ${claimTone(claim)} ${
                            selected === claim.claim_id ? "bg-accent/15 ring-2 ring-accent/60" : "hover:bg-sheet"
                          } ${dim ? "opacity-40" : ""}`}
                        >
                          {claim.text.trim().replace(/\.$/, "")}
                          {citation && <span className="font-sans text-[0.8em] text-accent-ink"> {citation}</span>}.
                        </span>{" "}
                      </Fragment>
                    );
                  })}
                </p>
              ))}
            </section>
          ))}
          <section aria-labelledby="refs" className="mt-12 border-t border-rule pt-6">
            <h2 id="refs" className="mb-3 text-2xl font-semibold">
              Referencias
            </h2>
            <ul className="space-y-2 font-sans text-base">
              {[...draft.references]
                .sort((a, b) => (labels.get(a.paper_id) ?? "").localeCompare(labels.get(b.paper_id) ?? ""))
                .map((reference) => (
                  <li key={reference.paper_id} className="pl-6 -indent-6">
                    {reference.authors.map((author) => author.family).join(", ")} ({reference.year ?? "s.f."}).{" "}
                    {reference.title}. <span className="italic">{reference.journal}</span>
                    {reference.doi && <span className="font-mono text-sm text-ink-soft"> https://doi.org/{reference.doi}</span>}
                  </li>
                ))}
            </ul>
          </section>
        </div>
      </article>

      <aside aria-label="Evidencia" className="sticky top-0 h-screen overflow-y-auto border-l border-rule bg-sheet px-7 py-10">
        <EvidencePanel
          draft={draft}
          claim={current}
          labels={labels}
          onAction={act}
          onNext={goNext}
          busy={busy}
          remaining={pending.filter((claim) => claim.claim_id !== selected).length}
          editing={editing}
          setEditing={setEditing}
        />
      </aside>

      <ExportDialog draft={draft} open={exporting} onClose={() => setExporting(false)} pending={pending.length} />
    </div>
  );
}
