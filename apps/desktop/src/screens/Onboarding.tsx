import { ArrowRight, FolderOpen, MessageSquareText, ShieldCheck, SearchCheck } from "lucide-react";
import { Button, Eyebrow } from "../components/ui";

const STEPS = [
  {
    Icon: FolderOpen,
    title: "Elige tu carpeta de artículos",
    body: "Leo tus PDFs en esta computadora y anoto autor, año, DOI y página de cada fragmento para poder citarlos bien.",
  },
  {
    Icon: MessageSquareText,
    title: "Pide lo que necesitas",
    body: "Escríbelo como se lo pedirías a un colega: “un estado del arte sobre tolerancia a sequía en papa”.",
  },
  {
    Icon: SearchCheck,
    title: "Revisa cada cita y exporta",
    body: "Te muestro de qué página sale cada afirmación. Lo dudoso queda marcado para que decidas tú antes de llevarlo a Word.",
  },
];

export function Onboarding({ onStart, onSkip }: { onStart: () => void; onSkip: () => void }) {
  return (
    <div className="mx-auto flex min-h-full max-w-5xl flex-col justify-center px-10 py-14">
      <div className="rise">
        <Eyebrow>Bienvenida</Eyebrow>
        <h1 tabIndex={-1} data-screen-title className="font-display mt-3 max-w-[18ch] text-[3.2rem] leading-[1.05] font-semibold outline-none">
          Tu biblioteca de PDFs, convertida en un borrador con citas que puedes verificar.
        </h1>
      </div>
      <ol className="mt-12 grid gap-5 md:grid-cols-3">
        {STEPS.map(({ Icon, title, body }, index) => (
          <li
            key={title}
            className="rise relative rounded-2xl border border-rule bg-sheet p-6"
            style={{ animationDelay: `${120 + index * 110}ms` }}
          >
            <span aria-hidden className="font-display absolute top-4 right-5 text-5xl font-semibold text-rule">
              {index + 1}
            </span>
            <Icon aria-hidden className="size-7 text-accent" />
            <h2 className="mt-4 text-lg font-bold">{title}</h2>
            <p className="mt-2 text-ink-soft">{body}</p>
          </li>
        ))}
      </ol>
      <aside
        className="rise mt-6 flex gap-4 rounded-2xl border border-moss/30 bg-moss-wash/60 p-5"
        style={{ animationDelay: "480ms" }}
        aria-label="Privacidad"
      >
        <ShieldCheck aria-hidden className="mt-0.5 size-6 shrink-0 text-moss" />
        <p>
          <strong>Tus PDFs no salen de tu computadora.</strong> Para redactar, solo se envían los fragmentos necesarios
          al servicio de IA aprobado por el CIP, que no los usa para entrenar modelos. El borrador declara el uso de IA y
          siempre necesita tu revisión experta.
        </p>
      </aside>
      <div className="rise mt-10 flex items-center gap-4" style={{ animationDelay: "560ms" }}>
        <Button variant="primary" onClick={onStart} icon={<ArrowRight aria-hidden className="size-4" />} className="px-6 text-base">
          Empezar con mi carpeta
        </Button>
        <Button variant="ghost" onClick={onSkip}>
          Ya conozco la herramienta
        </Button>
      </div>
    </div>
  );
}
