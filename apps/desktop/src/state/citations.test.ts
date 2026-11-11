import type { Claim, Reference } from "../api/types";
import { citationLabels, parenthetical, sharedTerms } from "./citations";

const reference = (paperId: string, families: string[], year: number, title: string): Reference => ({
  key: paperId,
  paper_id: paperId,
  authors: families.map((family) => ({ family, given: "" })),
  year,
  title,
  journal: null,
  doi: null,
  file_name: `${paperId}.pdf`,
});

const references = [
  reference("quispe", ["Quispe", "Huaman", "Vargas"], 2019, "Stomatal"),
  reference("condori", ["Condori", "Flores"], 2021, "Roots"),
  reference("nina-b", ["Nina"], 2023, "Thermal"),
  reference("nina-a", ["Nina"], 2023, "Canopy"),
];

it("formats APA style labels with Spanish conjunction and year suffixes", () => {
  const labels = citationLabels(references);

  expect(labels.get("quispe")).toBe("Quispe et al., 2019");
  expect(labels.get("condori")).toBe("Condori y Flores, 2021");
  expect(labels.get("nina-a")).toBe("Nina, 2023a");
  expect(labels.get("nina-b")).toBe("Nina, 2023b");
});

it("groups citations of a claim alphabetically without repeats", () => {
  const claim = {
    citations: [
      { passage_id: "x", paper_id: "quispe", page: 1 },
      { passage_id: "y", paper_id: "condori", page: 2 },
      { passage_id: "z", paper_id: "quispe", page: 3 },
    ],
  } as Claim;

  expect(parenthetical(claim, citationLabels(references))).toBe("(Condori y Flores, 2021; Quispe et al., 2019)");
});

it("finds the terms a claim shares with its source passage", () => {
  expect(sharedTerms("La conductancia estomática cayó 58 percent", "conductance fell 58 percent")).toEqual(
    new Set(["percent"]),
  );
});
