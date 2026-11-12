import { normalize, passageBoxes, type TextBox } from "./highlight";

const box = (text: string): TextBox => ({ text, x: 0, y: 0, width: 10, height: 10 });

const page = [
  box("Synthetic Journal of Potato Physiology"),
  box("Drought is the main abiotic constraint for potato"),
  box("in the Andean highlands."),
  box("Under progressive soil drying, potato plants closed"),
  box("their"),
  box("Published: 15 March 2019"),
  box("stomata early: stomatal conductance decreased by 58"),
  box("percent when soil water content fell below 60 percent"),
  box("Leaf abscisic acid (ABA) concentration increased fourfold"),
];

const passage =
  "Under progressive soil drying, potato plants closed their stomata early: stomatal conductance decreased by 58 percent when soil water content fell below 60 percent of field capacity.";

it("normalizes punctuation, case and hyphenated line endings", () => {
  expect(normalize("Stomatal  Con-")).toBe("stomatal con");
  expect(normalize("(ABA) 58 %")).toBe("aba 58");
});

it("highlights the contiguous block of lines that belongs to the passage", () => {
  expect(passageBoxes(page, passage).map((item) => item.text)).toEqual([
    "Under progressive soil drying, potato plants closed",
    "their",
    "stomata early: stomatal conductance decreased by 58",
    "percent when soil water content fell below 60 percent",
  ]);
});

it("returns nothing when the passage is not on the page", () => {
  expect(passageBoxes(page, "Late blight caused by Phytophthora infestans is destructive.")).toEqual([]);
});
