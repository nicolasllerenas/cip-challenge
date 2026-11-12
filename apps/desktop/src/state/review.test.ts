import type { Claim } from "../api/types";
import { undoSteps } from "./review";

const claim = (review: Claim["review"], text = "Texto original"): Claim => ({
  claim_id: "c1",
  text,
  citations: [],
  verdict: "partial",
  rationale: "",
  review,
});

describe("undoSteps", () => {
  it("returns a pending claim to pending after accept or remove", () => {
    expect(undoSteps(claim("pending"), "accept")).toEqual([{ action: "restore" }]);
    expect(undoSteps(claim("pending"), "remove")).toEqual([{ action: "restore" }]);
  });

  it("removes again a claim that was restored", () => {
    expect(undoSteps(claim("removed"), "restore")).toEqual([{ action: "remove" }]);
  });

  it("brings back the original text and status after an edit", () => {
    expect(undoSteps(claim("pending"), "edit")).toEqual([{ action: "edit", text: "Texto original" }, { action: "restore" }]);
    expect(undoSteps(claim("accepted"), "edit")).toEqual([{ action: "edit", text: "Texto original" }, { action: "accept" }]);
  });

  it("keeps an accepted claim accepted when removing is undone", () => {
    expect(undoSteps(claim("accepted"), "remove")).toEqual([{ action: "restore" }, { action: "accept" }]);
  });
});
