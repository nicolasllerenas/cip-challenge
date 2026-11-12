import type { ClaimAction } from "../api/client";
import type { Claim } from "../api/types";

export interface ReviewStep {
  action: ClaimAction;
  text?: string;
}

export const REVIEW_MESSAGES: Record<ClaimAction, string> = {
  accept: "Aceptaste la afirmación",
  remove: "Quitaste la afirmación del borrador",
  restore: "Restauraste la afirmación",
  edit: "Guardé tu edición",
};

export function undoSteps(previous: Claim, action: ClaimAction): ReviewStep[] {
  const back: ReviewStep[] = previous.review === "removed" ? [{ action: "remove" }] : [{ action: "restore" }];
  const reopen = previous.review === "accepted" ? [{ action: "accept" as const }] : back;
  if (action === "edit") return [{ action: "edit", text: previous.text }, ...reopen];
  if (action === "remove" && previous.review === "accepted") return [{ action: "restore" }, { action: "accept" }];
  return back;
}
