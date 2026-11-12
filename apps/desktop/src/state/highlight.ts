export interface TextBox {
  text: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

const MIN_ANCHOR = 12;

export function normalize(text: string): string {
  return text
    .toLowerCase()
    .replace(/-\s*$/u, "")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .trim();
}

export function passageBoxes(boxes: TextBox[], passage: string): TextBox[] {
  const target = ` ${normalize(passage)} `;
  const belongs = (text: string) => target.includes(` ${text} `);
  const anchors = boxes
    .map((box, index) => ({ index, text: normalize(box.text) }))
    .filter(({ text }) => text.length >= MIN_ANCHOR && belongs(text))
    .map(({ index }) => index);
  if (!anchors.length) return [];
  const first = Math.min(...anchors);
  const last = Math.max(...anchors);
  return boxes.slice(first, last + 1).filter((box) => {
    const text = normalize(box.text);
    return text.length > 0 && (text.length < MIN_ANCHOR || belongs(text));
  });
}
