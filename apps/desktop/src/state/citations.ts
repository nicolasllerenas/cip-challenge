import type { Author, Claim, Draft, Reference } from "../api/types";

function shortAuthors(authors: Author[], fallback: string): string {
  const families = authors.map((author) => author.family);
  if (!families.length) return fallback;
  if (families.length === 1) return families[0];
  if (families.length === 2) return `${families[0]} y ${families[1]}`;
  return `${families[0]} et al.`;
}

export function citationLabels(references: Reference[]): Map<string, string> {
  const groups = new Map<string, Reference[]>();
  const ordered = [...references].sort((a, b) => (a.title ?? "").localeCompare(b.title ?? ""));
  for (const reference of ordered) {
    const key = `${shortAuthors(reference.authors, reference.title ?? reference.file_name)}|${reference.year ?? ""}`;
    groups.set(key, [...(groups.get(key) ?? []), reference]);
  }
  const labels = new Map<string, string>();
  for (const [key, group] of groups) {
    const [authors] = key.split("|");
    group.forEach((reference, index) => {
      const suffix = group.length > 1 ? String.fromCharCode(97 + index) : "";
      labels.set(reference.paper_id, `${authors}, ${reference.year ?? "s.f."}${suffix}`);
    });
  }
  return labels;
}

export function parenthetical(claim: Claim, labels: Map<string, string>): string {
  const unique = [...new Set(claim.citations.map((link) => labels.get(link.paper_id)).filter(Boolean))] as string[];
  return unique.length ? `(${unique.sort((a, b) => a.localeCompare(b)).join("; ")})` : "";
}

export function allClaims(draft: Draft): Claim[] {
  return draft.sections.flatMap((section) => section.paragraphs.flatMap((paragraph) => paragraph.claims));
}

export function needsReview(claim: Claim): boolean {
  return claim.verdict !== "supported" && claim.review === "pending";
}

const WORD = /[\p{L}\d]+/gu;

export function sharedTerms(claim: string, passage: string): Set<string> {
  const claimTerms = new Set((claim.toLowerCase().match(WORD) ?? []).filter((term) => term.length > 3));
  return new Set((passage.toLowerCase().match(WORD) ?? []).filter((term) => claimTerms.has(term)));
}
