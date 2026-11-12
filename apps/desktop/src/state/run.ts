import type { DraftStats, JobEvent, Stage } from "../api/types";

export const STAGES = ["planning", "retrieving", "writing", "verifying", "assembling"] as const;
export type RunStage = (typeof STAGES)[number];
export type StepState = "pending" | "active" | "done";
export type SectionPhase = "planned" | "searching" | "writing" | "verifying" | "done";

export interface SourceRef {
  paperId: string;
  title: string;
  citation: string;
  page: number;
}

export interface SectionProgress {
  id: string;
  heading: string;
  goal: string;
  phase: SectionPhase;
  sources: SourceRef[];
  claims: number;
  preview: string;
  verdicts: { supported: number; partial: number; unsupported: number } | null;
}

export interface RunState {
  status: "running" | "completed" | "failed" | "cancelled";
  steps: Record<RunStage, StepState>;
  sections: SectionProgress[];
  sources: SourceRef[];
  warnings: string[];
  message: string;
  provider: string | null;
  draftId: string | null;
  stats: DraftStats | null;
  errorCode: string | null;
  lastSeq: number;
}

export const initialRun = (): RunState => ({
  status: "running",
  steps: { planning: "pending", retrieving: "pending", writing: "pending", verifying: "pending", assembling: "pending" },
  sections: [],
  sources: [],
  warnings: [],
  message: "Conectando con el asistente…",
  provider: null,
  draftId: null,
  stats: null,
  errorCode: null,
  lastSeq: 0,
});

const PHASE_BY_STAGE: Partial<Record<Stage, SectionPhase>> = {
  retrieving: "searching",
  writing: "writing",
  verifying: "verifying",
};

function advance(steps: RunState["steps"], stage: RunStage, done = false): RunState["steps"] {
  const position = STAGES.indexOf(stage);
  return Object.fromEntries(
    STAGES.map((key, index) => {
      if (index < position) return [key, "done"];
      if (index === position) return [key, done ? "done" : steps[key] === "done" ? "done" : "active"];
      return [key, steps[key]];
    }),
  ) as RunState["steps"];
}

function updateSection(state: RunState, id: unknown, change: Partial<SectionProgress>): SectionProgress[] {
  return state.sections.map((section) => (section.id === id ? { ...section, ...change } : section));
}

export function runReducer(state: RunState, event: JobEvent): RunState {
  if (event.seq && event.seq <= state.lastSeq) return state;
  const next: RunState = { ...state, lastSeq: event.seq || state.lastSeq, message: event.message };
  const data = event.data;
  const stage = event.stage as RunStage | null;
  switch (event.type) {
    case "job.started":
      return { ...next, provider: (data.provider as string) ?? null };
    case "stage.started": {
      const phase = event.stage ? PHASE_BY_STAGE[event.stage] : undefined;
      const sections = phase ? updateSection(next, data.section_id, { phase }) : next.sections;
      return { ...next, sections, steps: stage && STAGES.includes(stage) ? advance(next.steps, stage) : next.steps };
    }
    case "stage.completed":
      return { ...next, steps: stage && STAGES.includes(stage) ? advance(next.steps, stage, true) : next.steps };
    case "section.planned":
      return {
        ...next,
        sections: [
          ...next.sections,
          {
            id: data.section_id as string,
            heading: event.message,
            goal: (data.goal as string) ?? "",
            phase: "planned",
            sources: [],
            claims: 0,
            preview: "",
            verdicts: null,
          },
        ],
      };
    case "source.found": {
      const source: SourceRef = {
        paperId: data.paper_id as string,
        title: event.message,
        citation: data.citation as string,
        page: data.page as number,
      };
      const known = next.sources.some((item) => item.paperId === source.paperId);
      const section = next.sections.find((item) => item.id === data.section_id);
      return {
        ...next,
        sources: known ? next.sources : [...next.sources, source],
        sections: section ? updateSection(next, section.id, { sources: [...section.sources, source] }) : next.sections,
      };
    }
    case "section.drafted":
      return {
        ...next,
        sections: updateSection(next, data.section_id, {
          claims: data.claims as number,
          preview: (data.preview as string) ?? "",
        }),
      };
    case "claim.checked":
      return {
        ...next,
        sections: updateSection(next, data.section_id, {
          phase: "done",
          verdicts: {
            supported: data.supported as number,
            partial: data.partial as number,
            unsupported: data.unsupported as number,
          },
        }),
      };
    case "warning":
      return { ...next, warnings: [...next.warnings, event.message] };
    case "job.completed":
      return {
        ...next,
        status: "completed",
        steps: advance(next.steps, "assembling", true),
        draftId: (data.draft_id as string) ?? null,
        stats: (data.stats as DraftStats) ?? null,
      };
    case "job.failed":
      return { ...next, status: "failed", errorCode: (data.code as string) ?? "unknown" };
    case "job.cancelled":
      return { ...next, status: "cancelled" };
    default:
      return next;
  }
}

export function overallProgress(state: RunState): number {
  if (state.status === "completed") return 1;
  const weights: Record<SectionPhase, number> = { planned: 0.05, searching: 0.2, writing: 0.45, verifying: 0.75, done: 1 };
  if (!state.sections.length) return state.steps.planning === "active" ? 0.04 : 0;
  const sectionShare = state.sections.reduce((total, section) => total + weights[section.phase], 0) / state.sections.length;
  return Math.min(0.97, 0.08 + sectionShare * 0.85);
}
