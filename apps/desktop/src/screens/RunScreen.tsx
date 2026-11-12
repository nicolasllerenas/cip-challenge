import { BookMarked, Check, FileSearch, FileText, Layers, Loader2, PenLine, ShieldCheck, X } from "lucide-react";
import { useEffect, useReducer, useRef, useState } from "react";
import { api } from "../api/client";
import { useJobEvents } from "../api/useJobEvents";
import { Banner, Button, ProgressBar, ScreenHeader } from "../components/ui";
import { useElapsed } from "../hooks";
import { notifyInBackground } from "../platform";
import { STAGES, initialRun, overallProgress, runReducer, type RunStage, type SectionProgress } from "../state/run";

const STEP_COPY: Record<RunStage, { label: string; Icon: typeof Layers }> = {
  planning: { label: "Estructura", Icon: Layers },
  retrieving: { label: "Buscar evidencia", Icon: FileSearch },
  writing: { label: "Redactar", Icon: PenLine },
  verifying: { label: "Verificar citas", Icon: ShieldCheck },
  assembling: { label: "Armar documento", Icon: FileText },
};

const PHASE_COPY: Record<SectionProgress["phase"], string> = {
  planned: "En espera",
  searching: "Buscando evidencia",
  writing: "Redactando",
  verifying: "Verificando citas",
  done: "Lista",
};

const FAILURE_HELP: Record<string, string> = {
  no_evidence:
    "Prueba con términos más generales, revisa que elegiste la carpeta correcta o quita el filtro de años. Si tus artículos están en otro idioma, menciónalo en la solicitud.",
  rate_limited: "El servicio de IA está saturado. Espera un par de minutos y vuelve a intentarlo; tu solicitud quedó guardada.",
  service_unavailable: "Algún componente del asistente se detuvo. Cierra y vuelve a abrir la app; tu biblioteca está intacta.",
  library_unavailable: "No pude leer tu biblioteca. Vuelve a abrir la carpeta desde “Mi biblioteca”.",
  interrupted: "La app se cerró mientras trabajaba. Puedes pedir el borrador otra vez.",
};

function SectionCard({ section, index }: { section: SectionProgress; index: number }) {
  const working = section.phase !== "done" && section.phase !== "planned";
  return (
    <li className="rise rounded-xl border border-rule bg-sheet p-4" style={{ animationDelay: `${index * 70}ms` }}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-mono text-xs text-ink-soft">Sección {index + 1}</p>
          <h3 className="font-display text-lg leading-snug font-semibold">{section.heading}</h3>
        </div>
        <span className={`flex shrink-0 items-center gap-1.5 text-sm ${section.phase === "done" ? "text-moss" : "text-ink-soft"}`}>
          {section.phase === "done" ? <Check aria-hidden className="size-4" /> : working && <Loader2 aria-hidden className="size-4 animate-spin" />}
          {PHASE_COPY[section.phase]}
        </span>
      </div>
      {section.goal && <p className="mt-1 text-sm text-ink-soft">{section.goal}</p>}
      <p className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm">
        <span>{new Set(section.sources.map((source) => source.paperId)).size} fuentes</span>
        {section.claims > 0 && <span>{section.claims} afirmaciones</span>}
        {section.verdicts && (
          <span>
            <span className="text-moss">{section.verdicts.supported} respaldadas</span>
            {section.verdicts.partial + section.verdicts.unsupported > 0 && (
              <span className="text-ochre"> · {section.verdicts.partial + section.verdicts.unsupported} por revisar</span>
            )}
          </span>
        )}
      </p>
      {section.preview && <p className="font-display mt-3 border-l-2 border-accent/50 pl-3 text-ink-soft italic">“{section.preview}”</p>}
    </li>
  );
}

export function RunScreen({
  jobId,
  prompt,
  onReview,
  onAdjust,
}: {
  jobId: string;
  prompt: string;
  onReview: (draftId: string) => void;
  onAdjust: () => void;
}) {
  const [state, dispatch] = useReducer(runReducer, undefined, initialRun);
  const [announcement, setAnnouncement] = useState("");
  const [confirmCancel, setConfirmCancel] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const reviewButton = useRef<HTMLButtonElement>(null);
  const stream = useJobEvents(jobId, (event) => {
    dispatch(event);
    if (event.type === "job.completed") {
      const stats = event.data.stats as { claims: number; pending_review: number } | undefined;
      notifyInBackground(
        "Tu borrador está listo",
        stats ? `${stats.claims} afirmaciones · ${stats.pending_review} por revisar` : event.message,
      );
    }
    if (event.type === "job.failed") notifyInBackground("No pude terminar el borrador", event.message);
    if (["stage.started", "stage.completed", "warning", "job.completed", "job.failed", "job.cancelled"].includes(event.type)) {
      setAnnouncement(event.message);
    }
  });
  const running = state.status === "running";
  const elapsed = useElapsed(running);

  useEffect(() => {
    if (state.status === "completed") reviewButton.current?.focus();
  }, [state.status]);

  const cancel = async () => {
    setCancelling(true);
    try {
      await api.cancel(jobId);
    } finally {
      setCancelling(false);
      setConfirmCancel(false);
    }
  };

  const title = {
    running: "Estoy redactando tu borrador",
    completed: "Tu borrador está listo para revisar",
    failed: "No pude terminar el borrador",
    cancelled: "Cancelaste el borrador",
  }[state.status];

  return (
    <div className="mx-auto max-w-6xl px-10 py-10">
      <ScreenHeader eyebrow="Paso 3 · Redacción" title={title}>
        <span className="font-display italic">“{prompt}”</span>
      </ScreenHeader>
      <p aria-live="polite" className="sr-only">
        {announcement}
      </p>

      <section aria-label="Avance general" className="rise rounded-2xl border border-rule bg-sheet p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <p className="text-lg">
            <span className="font-bold">{state.message}</span>
          </p>
          <div className="flex items-center gap-3 text-sm text-ink-soft">
            <span className="font-mono" aria-label={`Tiempo transcurrido ${elapsed}`}>
              {elapsed}
            </span>
            {running && !confirmCancel && (
              <Button variant="ghost" onClick={() => setConfirmCancel(true)} icon={<X aria-hidden className="size-4" />}>
                Cancelar
              </Button>
            )}
          </div>
        </div>
        {confirmCancel && running && (
          <div role="group" aria-label="Confirmar cancelación" className="mt-4 flex flex-wrap items-center gap-3 rounded-xl bg-paper p-3">
            <span>¿Cancelar? Perderás el avance de este borrador.</span>
            <Button variant="danger" onClick={cancel} busy={cancelling}>
              Sí, cancelar
            </Button>
            <Button variant="ghost" onClick={() => setConfirmCancel(false)}>
              Seguir redactando
            </Button>
          </div>
        )}
        <div className="mt-5">
          <ProgressBar value={overallProgress(state)} label="Avance del borrador" />
        </div>
        <ol className="mt-6 grid grid-cols-5 gap-2" aria-label="Etapas">
          {STAGES.map((stage) => {
            const { label, Icon } = STEP_COPY[stage];
            const step = state.steps[stage];
            return (
              <li
                key={stage}
                aria-current={step === "active" ? "step" : undefined}
                className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${
                  step === "active" ? "bg-accent-wash font-bold text-accent-ink" : step === "done" ? "text-moss" : "text-ink-soft"
                }`}
              >
                {step === "done" ? <Check aria-hidden className="size-4" /> : <Icon aria-hidden className={`size-4 ${step === "active" ? "breathe" : ""}`} />}
                {label}
                <span className="sr-only">{step === "done" ? "(completada)" : step === "active" ? "(en curso)" : "(pendiente)"}</span>
              </li>
            );
          })}
        </ol>
      </section>

      {stream === "reconnecting" && running && (
        <div className="mt-6">
          <Banner kind="warning" title="Reconectando con el asistente…">
            Sigo trabajando en segundo plano; no perderás el avance.
          </Banner>
        </div>
      )}

      {state.status === "completed" && state.stats && state.draftId && (
        <div className="mt-6">
          <Banner
            kind="success"
            title={`${state.stats.claims} afirmaciones con ${state.stats.sources} fuentes de tu biblioteca`}
            actions={
              <Button ref={reviewButton} variant="primary" onClick={() => onReview(state.draftId as string)}>
                Revisar el borrador
              </Button>
            }
          >
            {state.stats.pending_review > 0
              ? `${state.stats.pending_review} afirmaciones necesitan tu revisión antes de exportar. Te las señalo una por una.`
              : "Todas las afirmaciones quedaron respaldadas por su fuente. Aun así, dale una lectura experta."}
          </Banner>
        </div>
      )}

      {state.status === "failed" && (
        <div className="mt-6">
          <Banner
            kind="error"
            title={state.message}
            actions={
              <Button variant="primary" onClick={onAdjust}>
                {state.errorCode === "no_evidence" ? "Ajustar la solicitud" : "Intentar de nuevo"}
              </Button>
            }
          >
            {FAILURE_HELP[state.errorCode ?? ""] ?? "Vuelve a intentarlo en unos minutos."}
          </Banner>
        </div>
      )}

      {state.status === "cancelled" && (
        <div className="mt-6">
          <Banner kind="info" title="Detuve el trabajo" actions={<Button onClick={onAdjust}>Volver a la solicitud</Button>}>
            Tu solicitud sigue guardada por si quieres ajustarla.
          </Banner>
        </div>
      )}

      {state.warnings.length > 0 && (
        <div className="mt-6 space-y-2">
          {[...new Set(state.warnings)].map((warning) => (
            <Banner key={warning} kind="warning" title={warning} />
          ))}
        </div>
      )}

      <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_22rem]">
        <section aria-labelledby="outline-title">
          <h2 id="outline-title" className="mb-3 font-bold">
            Estructura del documento
          </h2>
          {state.sections.length === 0 ? (
            <p className="flex items-center gap-2 text-ink-soft">
              <Loader2 aria-hidden className="size-4 animate-spin" /> Pensando en la mejor estructura…
            </p>
          ) : (
            <ol className="space-y-3">
              {state.sections.map((section, index) => (
                <SectionCard key={section.id} section={section} index={index} />
              ))}
            </ol>
          )}
        </section>
        <section aria-labelledby="sources-title" className="self-start rounded-2xl border border-rule bg-sheet p-5">
          <h2 id="sources-title" className="flex items-center gap-2 font-bold">
            <BookMarked aria-hidden className="size-4 text-accent" /> Fuentes consultadas
            <span className="ml-auto font-mono text-sm text-ink-soft">{state.sources.length}</span>
          </h2>
          {state.sources.length === 0 ? (
            <p className="mt-3 text-sm text-ink-soft">Aparecerán aquí a medida que las encuentre.</p>
          ) : (
            <ul className="mt-3 max-h-[26rem] space-y-3 overflow-y-auto pr-1">
              {state.sources.map((source) => (
                <li key={source.paperId} className="rise border-b border-rule/60 pb-3 last:border-none">
                  <p className="font-mono text-xs text-accent-ink">{source.citation}</p>
                  <p className="font-display text-sm leading-snug">{source.title}</p>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
