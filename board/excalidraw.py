import json
import random
from pathlib import Path

INK = "#1e1e1e"
MUTED = "#868e96"
PAPER = "#fffdf7"
ACCENT = "#c4501f"
ACCENT_SOFT = "#ffe8cc"
GREEN = "#2b8a3e"
GREEN_SOFT = "#d3f9d8"
YELLOW = "#e67700"
YELLOW_SOFT = "#fff3bf"
RED = "#c92a2a"
RED_SOFT = "#ffe3e3"
BLUE = "#1971c2"
BLUE_SOFT = "#e7f5ff"
VIOLET = "#6741d9"
VIOLET_SOFT = "#f3f0ff"
GRAY_SOFT = "#f1f3f5"
HAND, SANS, MONO = 5, 6, 3


class Board:
    def __init__(self, seed: int = 7) -> None:
        self.elements: list[dict] = []
        self._random = random.Random(seed)
        self._counter = 0

    def _element(self, kind: str, x: float, y: float, width: float, height: float, **style) -> dict:
        self._counter += 1
        element = {
            "id": f"el{self._counter:05d}",
            "type": kind,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "angle": 0,
            "strokeColor": style.get("stroke", INK),
            "backgroundColor": style.get("fill", "transparent"),
            "fillStyle": style.get("fill_style", "solid"),
            "strokeWidth": style.get("stroke_width", 1),
            "strokeStyle": style.get("stroke_style", "solid"),
            "roughness": style.get("roughness", 1),
            "opacity": style.get("opacity", 100),
            "groupIds": [],
            "frameId": None,
            "roundness": {"type": 3} if style.get("rounded", True) else None,
            "seed": self._random.randint(1, 2**31 - 1),
            "version": 1,
            "versionNonce": self._random.randint(1, 2**31 - 1),
            "isDeleted": False,
            "boundElements": None,
            "updated": 1,
            "link": None,
            "locked": False,
        }
        self.elements.append(element)
        return element

    def rect(self, x: float, y: float, width: float, height: float, **style) -> dict:
        return self._element("rectangle", x, y, width, height, **style)

    def ellipse(self, x: float, y: float, width: float, height: float, **style) -> dict:
        return self._element("ellipse", x, y, width, height, rounded=False, **style)

    def text(
        self,
        x: float,
        y: float,
        content: str,
        size: int = 16,
        color: str = INK,
        font: int = SANS,
        align: str = "left",
    ) -> dict:
        lines = content.split("\n")
        width = max(len(line) for line in lines) * size * 0.56
        height = len(lines) * size * 1.25
        left = x - width / 2 if align == "center" else x
        element = self._element("text", left, y, width, height, stroke=color, rounded=False, roughness=0)
        element.update(
            {
                "text": content,
                "originalText": content,
                "fontSize": size,
                "fontFamily": font,
                "textAlign": align,
                "verticalAlign": "top",
                "containerId": None,
                "autoResize": True,
                "lineHeight": 1.25,
            }
        )
        return element

    def _path(self, kind: str, points: list[tuple[float, float]], **style) -> dict:
        x0, y0 = points[0]
        relative = [[px - x0, py - y0] for px, py in points]
        xs, ys = [p[0] for p in relative], [p[1] for p in relative]
        element = self._element(kind, x0, y0, max(xs) - min(xs), max(ys) - min(ys), rounded=False, **style)
        element["roundness"] = {"type": 2}
        element.update({"points": relative, "lastCommittedPoint": None, "startBinding": None, "endBinding": None})
        return element

    def arrow(
        self,
        points: list[tuple[float, float]],
        color: str = INK,
        dashed: bool = False,
        width: int = 2,
        both: bool = False,
    ) -> dict:
        element = self._path(
            "arrow", points, stroke=color, stroke_width=width, stroke_style="dashed" if dashed else "solid"
        )
        element.update({"startArrowhead": "arrow" if both else None, "endArrowhead": "arrow", "elbowed": False})
        return element

    def line(self, points: list[tuple[float, float]], color: str = INK, width: int = 1, dashed: bool = False) -> dict:
        element = self._path(
            "line", points, stroke=color, stroke_width=width, stroke_style="dashed" if dashed else "solid"
        )
        element.update({"startArrowhead": None, "endArrowhead": None, "polygon": False})
        return element

    def save(self, target: Path) -> None:
        scene = {
            "type": "excalidraw",
            "version": 2,
            "source": "https://excalidraw.com",
            "elements": self.elements,
            "appState": {"gridSize": 20, "viewBackgroundColor": "#ffffff", "currentItemFontFamily": HAND},
            "files": {},
        }
        target.write_text(json.dumps(scene, ensure_ascii=False, indent=1))


class Kit:
    def __init__(self, board: Board) -> None:
        self.b = board

    def window(
        self, x: float, y: float, width: float, height: float, title: str, active: str | None
    ) -> tuple[float, float]:
        b = self.b
        b.rect(x, y, width, height, fill=PAPER, stroke_width=2)
        b.rect(x, y, width, 30, fill=GRAY_SOFT, stroke_width=2)
        for index, color in enumerate((RED_SOFT, YELLOW_SOFT, GREEN_SOFT)):
            b.ellipse(x + 12 + index * 18, y + 9, 12, 12, fill=color)
        b.text(x + 76, y + 7, title, 13, MUTED)
        b.rect(x, y + 30, 132, height - 30, fill="#f8f9fa", rounded=False)
        b.rect(x + 12, y + 42, 22, 22, fill=ACCENT, stroke=ACCENT)
        b.text(x + 40, y + 44, "Asistente", 13, INK, SANS)
        for index, label in enumerate(("Mi biblioteca", "Nuevo borrador", "Mis borradores")):
            top = y + 84 + index * 40
            if label == active:
                b.rect(x + 8, top - 6, 116, 32, fill=ACCENT_SOFT, stroke=ACCENT_SOFT)
            b.text(x + 18, top, label, 13, ACCENT if label == active else INK)
        b.text(x + 12, y + height - 26, "A− A+", 12, MUTED)
        b.text(x + 146, y + height - 22, "● Asistente listo", 12, GREEN)
        return x + 152, y + 46

    def button(self, x: float, y: float, label: str, kind: str = "primary", width: float | None = None) -> float:
        width = width or len(label) * 8.2 + 28
        colors = {
            "primary": (ACCENT, ACCENT, "#ffffff"),
            "secondary": (INK, "#ffffff", INK),
            "danger": (RED, "#ffffff", RED),
            "ghost": ("transparent", "transparent", MUTED),
        }[kind]
        self.b.rect(x, y, width, 30, stroke=colors[0], fill=colors[1])
        self.b.text(x + width / 2, y + 7, label, 13, colors[2], SANS, "center")
        return width

    def lines(self, x: float, y: float, width: float, count: int, gap: float = 14, color: str = "#ced4da") -> None:
        for index in range(count):
            length = width * (0.62 if index == count - 1 else 1)
            self.b.line([(x, y + index * gap), (x + length, y + index * gap)], color, 2)

    def chip(self, x: float, y: float, label: str, stroke: str, fill: str) -> float:
        width = len(label) * 7.4 + 20
        self.b.rect(x, y, width, 24, stroke=stroke, fill=fill)
        self.b.text(x + 10, y + 4, label, 12, stroke)
        return width

    def progress(self, x: float, y: float, width: float, ratio: float) -> None:
        self.b.rect(x, y, width, 10, fill=GRAY_SOFT, stroke="#ced4da")
        self.b.rect(x, y, width * ratio, 10, fill=ACCENT, stroke=ACCENT)

    def note(self, x: float, y: float, width: float, title: str, bullets: list[str]) -> float:
        height = 44 + len(bullets) * 27
        self.b.rect(x, y, width, height, fill=YELLOW_SOFT, stroke=YELLOW, roughness=2)
        self.b.text(x + 16, y + 12, title, 20, YELLOW, HAND)
        for index, bullet in enumerate(bullets):
            self.b.text(x + 16, y + 42 + index * 27, f"• {bullet}", 17, INK, HAND)
        return height

    def card(
        self, x: float, y: float, width: float, height: float, title: str, body: list[str], tone: tuple[str, str]
    ) -> None:
        stroke, fill = tone
        self.b.rect(x, y, width, height, fill=fill, stroke=stroke, stroke_width=2)
        self.b.text(x + 18, y + 14, title, 20, stroke, HAND)
        for index, line in enumerate(body):
            self.b.text(x + 18, y + 48 + index * 24, line, 15, INK, SANS)

    def box(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        title: str,
        lines: list[str],
        tone: tuple[str, str],
        size: int = 15,
    ) -> None:
        stroke, fill = tone
        self.b.rect(x, y, width, height, fill=fill, stroke=stroke, stroke_width=2)
        self.b.text(x + 16, y + 12, title, 19, stroke, SANS)
        for index, line in enumerate(lines):
            self.b.text(x + 16, y + 42 + index * (size + 8), line, size, INK, SANS)
