export type PaperStatus = "indexed" | "needs_ocr" | "failed";
export type Verdict = "supported" | "partial" | "unsupported";
export type ReviewStatus = "pending" | "accepted" | "removed";
export type Length = "short" | "medium" | "long";
export type ExportFormat = "docx" | "md" | "bib";
export type Stage = "indexing" | "planning" | "retrieving" | "writing" | "verifying" | "assembling";

export type EventType =
  | "job.started"
  | "stage.started"
  | "stage.completed"
  | "progress"
  | "paper.indexed"
  | "section.planned"
  | "source.found"
  | "section.drafted"
  | "claim.checked"
  | "warning"
  | "job.completed"
  | "job.failed"
  | "job.cancelled";

export interface Author {
  family: string;
  given: string;
}

export interface PaperMetadata {
  title: string | null;
  authors: Author[];
  year: number | null;
  doi: string | null;
  journal: string | null;
}

export interface Paper {
  paper_id: string;
  library_id: string;
  file_name: string;
  file_path: string;
  pages: number;
  status: PaperStatus;
  metadata: PaperMetadata;
  issues: string[];
}

export interface LibraryCounts {
  total: number;
  indexed: number;
  needs_ocr: number;
  failed: number;
  incomplete_metadata: number;
}

export interface LibrarySummary {
  library_id: string;
  path: string;
  counts: LibraryCounts;
  papers: Paper[];
}

export interface Passage {
  passage_id: string;
  paper_id: string;
  page: number;
  text: string;
  score: number;
  file_name: string;
  file_path: string;
  metadata: PaperMetadata;
}

export interface CitationLink {
  passage_id: string;
  paper_id: string;
  page: number;
}

export interface Claim {
  claim_id: string;
  text: string;
  citations: CitationLink[];
  verdict: Verdict;
  rationale: string;
  review: ReviewStatus;
}

export interface Section {
  section_id: string;
  heading: string;
  paragraphs: { claims: Claim[] }[];
}

export interface Reference {
  key: string;
  paper_id: string;
  authors: Author[];
  year: number | null;
  title: string | null;
  journal: string | null;
  doi: string | null;
  file_name: string;
}

export interface Draft {
  draft_id: string;
  library_id: string;
  prompt: string;
  title: string;
  language: string;
  sections: Section[];
  references: Reference[];
  evidence: Record<string, Passage>;
  models: Record<string, string>;
  created_at: string;
}

export interface DraftStats {
  claims: number;
  supported: number;
  partial: number;
  unsupported: number;
  pending_review: number;
  sources: number;
}

export interface DraftSummary {
  draft_id: string;
  job_id: string;
  title: string;
  created_at: string;
  stats: DraftStats;
}

export interface DraftOptions {
  length: Length;
  language: string;
  citation_style: string;
  year_from: number | null;
}

export interface JobEvent {
  seq: number;
  job_id: string;
  type: EventType;
  stage: Stage | null;
  message: string;
  progress: number | null;
  data: Record<string, unknown>;
  at: string;
}

export interface Job {
  job_id: string;
  kind: "ingestion" | "draft";
  subject_id: string;
  status: "running" | "completed" | "failed" | "cancelled";
  message: string;
  last_seq: number;
}

export interface ServiceHealth {
  name: string;
  ok: boolean;
  provider?: string;
  models?: Record<string, string>;
}

export interface Health {
  status: "ok" | "degraded";
  services: ServiceHealth[];
}

export interface ExportedFile {
  file_name: string;
  path: string;
  url: string;
}

export interface ExportResult {
  files: ExportedFile[];
  pending_review: number;
}

export const TERMINAL: EventType[] = ["job.completed", "job.failed", "job.cancelled"];
