import type { EventType, JobEvent, Stage } from "../api/types";
import { initialRun, overallProgress, runReducer } from "./run";

let seq = 0;
const event = (type: EventType, message: string, data: Record<string, unknown> = {}, stage: Stage | null = null): JobEvent => ({
  seq: ++seq,
  job_id: "job",
  type,
  stage,
  message,
  progress: null,
  data,
  at: "",
});

const play = (...events: JobEvent[]) => events.reduce(runReducer, initialRun());

describe("runReducer", () => {
  beforeEach(() => {
    seq = 0;
  });

  it("builds the outline and marks earlier stages done as later ones start", () => {
    const state = play(
      event("job.started", "Empecé", { provider: "anthropic" }),
      event("stage.started", "Planificando", {}, "planning"),
      event("section.planned", "Respuestas fisiológicas", { section_id: "s1", goal: "Mecanismos" }),
      event("stage.started", "Buscando", { section_id: "s1" }, "retrieving"),
    );

    expect(state.provider).toBe("anthropic");
    expect(state.steps).toMatchObject({ planning: "done", retrieving: "active", writing: "pending" });
    expect(state.sections).toEqual([expect.objectContaining({ id: "s1", phase: "searching", goal: "Mecanismos" })]);
  });

  it("deduplicates sources globally but keeps them per section", () => {
    const found = { section_id: "s1", paper_id: "p1", citation: "Quispe et al., 2019", page: 1 };
    const state = play(
      event("section.planned", "A", { section_id: "s1" }),
      event("source.found", "Stomatal regulation", found),
      event("source.found", "Stomatal regulation", { ...found, page: 2 }),
    );

    expect(state.sources).toHaveLength(1);
    expect(state.sections[0].sources).toHaveLength(2);
  });

  it("records verification results and completion", () => {
    const state = play(
      event("section.planned", "A", { section_id: "s1" }),
      event("claim.checked", "Verifiqué", { section_id: "s1", supported: 4, partial: 1, unsupported: 0 }, "verifying"),
      event("job.completed", "Listo", { draft_id: "d1", stats: { pending_review: 1 } }),
    );

    expect(state.sections[0]).toMatchObject({ phase: "done", verdicts: { supported: 4, partial: 1, unsupported: 0 } });
    expect(state.status).toBe("completed");
    expect(state.draftId).toBe("d1");
    expect(overallProgress(state)).toBe(1);
  });

  it("ignores events replayed after a reconnection", () => {
    const warning = event("warning", "Sin evidencia para B");
    const state = [warning, warning].reduce(runReducer, initialRun());

    expect(state.warnings).toEqual(["Sin evidencia para B"]);
  });

  it("keeps the failure code to show the right guidance", () => {
    const state = play(event("job.failed", "No encontré artículos", { code: "no_evidence" }));

    expect(state).toMatchObject({ status: "failed", errorCode: "no_evidence" });
  });
});
