import { gatewayBase } from "../platform";
import type {
  Author,
  Draft,
  DraftOptions,
  DraftSummary,
  ExportFormat,
  ExportResult,
  Health,
  Job,
  LibrarySummary,
  Paper,
} from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

const OFFLINE = "No puedo conectarme con el asistente. Revisa que la app siga abierta e inténtalo de nuevo.";
const GENERIC = "Algo salió mal. Inténtalo de nuevo en unos segundos.";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${gatewayBase()}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init.headers },
    });
  } catch {
    throw new ApiError(OFFLINE, 0);
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(typeof body.detail === "string" ? body.detail : GENERIC, response.status);
  }
  return response.json() as Promise<T>;
}

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

const patch = <T>(path: string, body: unknown) => request<T>(path, { method: "PATCH", body: JSON.stringify(body) });

export interface MetadataPatch {
  title?: string | null;
  authors?: Author[];
  year?: number | null;
  doi?: string | null;
}

export type ClaimAction = "accept" | "remove" | "restore" | "edit";

export const api = {
  health: () => request<Health>("/v1/health"),
  openLibrary: (path: string) => post<{ library: LibrarySummary; job_id: string }>("/v1/libraries", { path }),
  reindex: (libraryId: string) => post<{ job_id: string }>(`/v1/libraries/${libraryId}/reindex`),
  library: (libraryId: string) => request<LibrarySummary>(`/v1/libraries/${libraryId}`),
  patchPaper: (paperId: string, body: MetadataPatch) => patch<Paper>(`/v1/papers/${paperId}`, body),
  createDraft: (libraryId: string, prompt: string, options: DraftOptions) =>
    post<{ job_id: string }>("/v1/drafts", { library_id: libraryId, prompt, options }),
  job: (jobId: string) => request<Job>(`/v1/jobs/${jobId}`),
  cancel: (jobId: string) => post<{ cancelled: boolean }>(`/v1/jobs/${jobId}/cancel`),
  drafts: () => request<DraftSummary[]>("/v1/drafts"),
  draft: (draftId: string) => request<Draft>(`/v1/drafts/${draftId}`),
  review: (draftId: string, claimId: string, action: ClaimAction, text?: string) =>
    patch<Draft>(`/v1/drafts/${draftId}/claims/${claimId}`, { action, text }),
  exportDraft: (draftId: string, format: ExportFormat, includeReviewComments: boolean) =>
    post<ExportResult>(`/v1/drafts/${draftId}/exports`, { format, include_review_comments: includeReviewComments }),
  eventsUrl: (jobId: string) => `${gatewayBase()}/v1/jobs/${jobId}/events`,
  paperUrl: (paperId: string, page: number) => `${gatewayBase()}/v1/papers/${paperId}/file#page=${page}`,
  absolute: (url: string) => `${gatewayBase()}${url}`,
};
