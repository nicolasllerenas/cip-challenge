import type { JobEvent, LibraryCounts, Paper } from "../api/types";

export interface IngestionState {
  status: "running" | "completed" | "failed" | "cancelled";
  total: number;
  processed: number;
  current: string;
  papers: Paper[];
  counts: LibraryCounts | null;
  message: string;
  errorCode: string | null;
}

export const initialIngestion = (): IngestionState => ({
  status: "running",
  total: 0,
  processed: 0,
  current: "",
  papers: [],
  counts: null,
  message: "Preparando la lectura de tu carpeta…",
  errorCode: null,
});

export function ingestionReducer(state: IngestionState, event: JobEvent): IngestionState {
  const next = { ...state, message: event.message };
  switch (event.type) {
    case "job.started":
      return { ...next, total: (event.data.total as number) ?? 0 };
    case "paper.indexed": {
      const paper = event.data.paper as Paper;
      return {
        ...next,
        processed: state.processed + 1,
        current: paper.file_name,
        papers: [...state.papers.filter((item) => item.paper_id !== paper.paper_id), paper],
      };
    }
    case "job.completed":
      return { ...next, status: "completed", counts: event.data.counts as LibraryCounts };
    case "job.failed":
      return { ...next, status: "failed", errorCode: (event.data.code as string) ?? "unknown" };
    case "job.cancelled":
      return { ...next, status: "cancelled" };
    default:
      return next;
  }
}
