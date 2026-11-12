import { BookOpen, FileText, ListChecks, Search, ShieldCheck, Sparkles } from "lucide-react";
import { useId, useState, type FormEvent, type KeyboardEvent } from "react";
import { ApiError, api } from "../api/client";
import type { Length, LibrarySummary } from "../api/types";
import { Banner, Button, Kbd, ScreenHeader } from "../components/ui";
import { useStored } from "../hooks";
import { prepareNotifications } from "../platform";

const EXAMPLES = [
  "Redáctame un borrador del estado del arte sobre tolerancia a sequía en papa, con citas y bibliografía, en un .docx que pueda editar.",
  "Resume qué métodos de fenotipado se han usado para evaluar estrés hídrico en papa y compara sus ventajas.",
  "¿Qué genes o QTL se han asociado a la tolerancia a sequía? Organízalo por cromosoma.",
];

const LENGTHS: { value: Length; label: string; detail: string }[] = [
  { value: "short", label: "Breve", detail: "3 secciones · ~2 páginas" },
  { value: "medium", label: "Media", detail: "5 secciones · ~4 páginas" },
  { value: "long", label: "Extensa", detail: "7 secciones · ~7 páginas" },
];

const PLAN = [
  { Icon: ListChecks, text: "Propongo una estructura de secciones" },
  { Icon: Search, text: "Busco evidencia en tus artículos para cada sección" },
  { Icon: FileText, text: "Redacto conectando hallazgos, con cita en cada afirmación" },
  { Icon: ShieldCheck, text: "Compruebo cada cita contra la página de donde sale" },
];

function Segmented<T extends string | number>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T;
  options: { value: T; label: string; detail?: string }[];
  onChange: (value: T) => void;
}) {
  const id = useId();
  return (
    <fieldset>
      <legend id={id} className="mb-2 text-sm font-bold">
        {label}
      </legend>
      <div role="radiogroup" aria-labelledby={id} className="grid auto-cols-fr grid-flow-col gap-2">
        {options.map((option) => (
          <button
            key={String(option.value)}
            type="button"
            role="radio"
            aria-checked={value === option.value}
            onClick={() => onChange(option.value)}
            className={`rounded-xl border px-3 py-2 text-left transition ${
              value === option.value ? "border-accent bg-accent-wash text-accent-ink" : "border-rule bg-sheet hover:border-ink-soft"
            }`}
          >
            <span className="block font-bold">{option.label}</span>
            {option.detail && <span className="block text-xs text-ink-soft">{option.detail}</span>}
          </button>
        ))}
      </div>
    </fieldset>
  );
}

export function ComposeScreen({
  library,
  onStarted,
  onOpenLibrary,
}: {
  library: LibrarySummary | null;
  onStarted: (jobId: string, prompt: string) => void;
  onOpenLibrary: () => void;
}) {
  const [prompt, setPrompt] = useStored("cip.prompt", "");
  const [length, setLength] = useStored<Length>("cip.length", "medium");
  const [language, setLanguage] = useStored("cip.language", "es");
  const [yearFrom, setYearFrom] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const ready = (library?.counts.indexed ?? 0) > 0;
  const tooShort = prompt.trim().length < 10;

  const submit = async (event?: FormEvent) => {
    event?.preventDefault();
    if (!library || tooShort) return;
    setSending(true);
    setError(null);
    void prepareNotifications();
    try {
      const { job_id } = await api.createDraft(library.library_id, prompt.trim(), {
        length,
        language,
        citation_style: "apa",
        year_from: yearFrom ? Number(yearFrom) : null,
      });
      onStarted(job_id, prompt.trim());
    } catch (failure) {
      setError(failure instanceof ApiError ? failure.message : "No pude enviar tu solicitud.");
    } finally {
      setSending(false);
    }
  };

  const shortcut = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) submit();
  };

  if (!ready) {
    return (
      <div className="mx-auto max-w-3xl px-10 py-10">
        <ScreenHeader eyebrow="Paso 2 · Solicitud" title="Primero necesito tus artículos">
          Solo escribo a partir de los PDFs de tu biblioteca, así cada afirmación tiene una fuente que puedes revisar.
        </ScreenHeader>
        <Button variant="primary" onClick={onOpenLibrary} icon={<BookOpen aria-hidden className="size-4" />}>
          Elegir mi carpeta de artículos
        </Button>
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="mx-auto grid max-w-6xl gap-10 px-10 py-10 xl:grid-cols-[1fr_20rem]">
      <div>
        <ScreenHeader eyebrow="Paso 2 · Solicitud" title="¿Qué necesitas escribir?">
          Escríbelo como se lo pedirías a un colega. Usaré tus {library?.counts.indexed} artículos y nada más.
        </ScreenHeader>

        <label htmlFor="prompt" className="sr-only">
          Tu solicitud
        </label>
        <textarea
          id="prompt"
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          onKeyDown={shortcut}
          rows={6}
          maxLength={2000}
          aria-describedby="prompt-help"
          placeholder={EXAMPLES[0]}
          className="font-display w-full resize-y rounded-2xl border border-rule bg-sheet p-5 text-xl leading-relaxed shadow-[inset_0_1px_0_rgba(0,0,0,.03)] placeholder:text-ink-soft/60"
        />
        <p id="prompt-help" className="mt-2 flex flex-wrap items-center gap-2 text-sm text-ink-soft">
          Menciona el tema, el enfoque y para qué lo usarás. <Kbd>Ctrl</Kbd>+<Kbd>Enter</Kbd> para enviar.
        </p>

        <div className="mt-5">
          <p className="mb-2 text-sm font-bold">Ideas para empezar</p>
          <ul className="flex flex-wrap gap-2">
            {EXAMPLES.map((example) => (
              <li key={example}>
                <button
                  type="button"
                  onClick={() => setPrompt(example)}
                  className="flex max-w-md items-start gap-2 rounded-xl border border-rule bg-sheet px-3 py-2 text-left text-sm hover:border-accent"
                >
                  <Sparkles aria-hidden className="mt-0.5 size-4 shrink-0 text-accent" />
                  <span className="line-clamp-2">{example}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-8 grid gap-6 md:grid-cols-2">
          <Segmented label="Extensión" value={length} options={LENGTHS} onChange={setLength} />
          <Segmented
            label="Idioma del borrador"
            value={language}
            options={[
              { value: "es", label: "Español" },
              { value: "en", label: "English" },
            ]}
            onChange={setLanguage}
          />
          <label>
            <span className="block text-sm font-bold">Solo artículos desde el año (opcional)</span>
            <input
              inputMode="numeric"
              pattern="\d{4}"
              value={yearFrom}
              onChange={(event) => setYearFrom(event.target.value)}
              placeholder="Ej. 2015"
              className="mt-2 w-40 rounded-lg border border-rule bg-sheet px-3 py-2"
            />
          </label>
          <div>
            <span className="block text-sm font-bold">Estilo de cita</span>
            <p className="mt-2 rounded-lg border border-rule bg-sheet px-3 py-2">APA 7.ª edición</p>
          </div>
        </div>

        {error && (
          <div className="mt-6">
            <Banner kind="error" title={error} />
          </div>
        )}

        <div className="mt-8 flex items-center gap-4">
          <Button type="submit" variant="primary" busy={sending} disabled={tooShort} className="px-6 text-base">
            Redactar borrador
          </Button>
          {tooShort && <span className="text-sm text-ink-soft">Cuéntame un poco más (al menos 10 caracteres).</span>}
        </div>
      </div>

      <aside className="rise self-start rounded-2xl border border-rule bg-sheet p-6 xl:mt-24" aria-labelledby="plan-title">
        <h2 id="plan-title" className="font-display text-xl font-semibold">
          Qué voy a hacer
        </h2>
        <ol className="mt-4 space-y-4">
          {PLAN.map(({ Icon, text }, index) => (
            <li key={text} className="flex gap-3">
              <span className="font-mono text-sm text-accent-ink">{index + 1}</span>
              <Icon aria-hidden className="mt-0.5 size-4 shrink-0 text-ink-soft" />
              <span>{text}</span>
            </li>
          ))}
        </ol>
        <p className="mt-6 border-t border-rule pt-4 text-sm text-ink-soft">
          Suele tardar entre 3 y 6 minutos. Verás el avance en vivo y puedes cancelar en cualquier momento.
        </p>
      </aside>
    </form>
  );
}
