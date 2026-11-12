from pathlib import Path

from excalidraw import (
    ACCENT,
    ACCENT_SOFT,
    BLUE,
    BLUE_SOFT,
    GRAY_SOFT,
    GREEN,
    GREEN_SOFT,
    HAND,
    INK,
    MONO,
    MUTED,
    RED,
    RED_SOFT,
    SANS,
    VIOLET,
    VIOLET_SOFT,
    YELLOW,
    YELLOW_SOFT,
    Board,
    Kit,
)

SCREEN_W, SCREEN_H = 640, 440
TONE_GREEN = (GREEN, GREEN_SOFT)
TONE_BLUE = (BLUE, BLUE_SOFT)
TONE_VIOLET = (VIOLET, VIOLET_SOFT)
TONE_ACCENT = (ACCENT, ACCENT_SOFT)
TONE_GRAY = (INK, GRAY_SOFT)
TONE_RED = (RED, RED_SOFT)
TONE_YELLOW = (YELLOW, YELLOW_SOFT)


def header(b: Board, k: Kit) -> None:
    b.text(0, 0, "Asistente de Investigación CIP", 60, INK, HAND)
    b.text(
        0,
        84,
        "De una carpeta con 200 PDFs a un estado del arte en .docx con citas que se pueden verificar",
        26,
        MUTED,
        HAND,
    )
    b.text(
        0,
        130,
        "Parte A · Experiencia de la investigadora (wireframes)     Parte B · Arquitectura de alto nivel",
        20,
        ACCENT,
        HAND,
    )
    k.card(
        0,
        180,
        900,
        200,
        "Para quién diseño",
        [
            "Investigadora en mejoramiento genético de papa. Experta en su dominio, no en software.",
            "Trabaja en Word con su asesor y coautores. Tiene ~200 PDFs en una carpeta y poco tiempo.",
            "Su miedo: una cita inventada en un documento con su nombre.",
            "Su meta: un primer borrador sólido que pueda editar y defender.",
        ],
        TONE_BLUE,
    )
    k.card(
        960,
        180,
        1100,
        200,
        "Principios de diseño",
        [
            "1. Confianza antes que magia: cada afirmación muestra de qué PDF y de qué página sale.",
            "2. Ella decide: la IA propone, la investigadora aprueba, edita o quita.",
            "3. Lenguaje de investigadora, no de ingeniero. Nada de logs ni jerga técnica.",
            "4. Nunca un callejón sin salida: cada error dice qué pasó y qué puede hacer.",
            "5. Accesible por defecto: teclado, lector de pantalla, texto grande, sin depender del color.",
        ],
        TONE_GREEN,
    )
    k.card(
        2120,
        180,
        700,
        200,
        "Cómo leer este tablero",
        [
            "Números ①…⑦ = pasos del recorrido.",
            "Notas amarillas = el porqué de cada decisión.",
            "Fila roja = qué pasa cuando algo sale mal.",
            "Parte B = de la app al .docx.",
        ],
        TONE_GRAY,
    )


def journey(b: Board, top: float) -> None:
    b.text(0, top, "El recorrido en 7 pasos", 34, INK, HAND)
    steps = [
        ("Primer uso", "¿Es seguro para mis datos?"),
        ("Elige carpeta", "¿Leyó todos mis PDFs?"),
        ("Indexación", "¿Qué PDFs fallaron?"),
        ("Solicitud", "¿Cómo se lo pido?"),
        ("Progreso en vivo", "¿Está avanzando? ¿Va bien?"),
        ("Revisar citas", "¿Puedo confiar en esto?"),
        ("Exportar a Word", "¿Queda listo para editar?"),
    ]
    for index, (title, question) in enumerate(steps):
        x = index * 405
        b.ellipse(x, top + 60, 64, 64, fill=ACCENT, stroke=ACCENT)
        b.text(x + 32, top + 74, str(index + 1), 30, "#ffffff", HAND, "center")
        b.text(x + 80, top + 66, title, 24, INK, HAND)
        b.text(x + 80, top + 100, question, 17, MUTED, HAND)
        if index < len(steps) - 1:
            b.arrow([(x + 300, top + 92), (x + 395, top + 92)], ACCENT)


def onboarding(b: Board, k: Kit, x: float, y: float) -> None:
    cx, cy = k.window(x, y, SCREEN_W, SCREEN_H, "① Primer uso · Bienvenida", None)
    b.text(cx, cy, "Tu biblioteca de PDFs, convertida en un\nborrador con citas que puedes verificar.", 20, INK, SANS)
    for index, (title, body) in enumerate(
        [
            ("1 Elige tu carpeta", "Leo tus PDFs aquí"),
            ("2 Pide lo que necesitas", "Como a un colega"),
            ("3 Revisa y exporta", "Tú decides"),
        ]
    ):
        left = cx + index * 158
        b.rect(left, cy + 64, 148, 92, fill="#ffffff")
        b.text(left + 10, cy + 74, title, 13, ACCENT)
        b.text(left + 10, cy + 100, body, 12, MUTED)
    b.rect(cx, cy + 172, 468, 74, fill=GREEN_SOFT, stroke=GREEN)
    b.text(
        cx + 12,
        cy + 182,
        "🛡 Tus PDFs no salen de tu computadora. Solo los\nfragmentos necesarios van al servicio de IA aprobado\npor el CIP. El borrador declara el uso de IA.",
        12,
        INK,
    )
    k.button(cx, cy + 270, "Empezar con mi carpeta")
    k.button(cx + 200, cy + 270, "Ya conozco la herramienta", "ghost")


def library(b: Board, k: Kit, x: float, y: float) -> None:
    cx, cy = k.window(x, y, SCREEN_W, SCREEN_H, "② ③ Biblioteca · indexando", "Mi biblioteca")
    b.text(cx, cy, "Tu biblioteca de artículos", 20, INK)
    b.text(cx, cy + 34, "Leyendo 134 de 200 · Drought_QTL_2021.pdf", 13, INK)
    k.progress(cx, cy + 56, 468, 0.67)
    b.text(cx, cy + 74, "Puedes escribir tu solicitud mientras termino →", 12, ACCENT)
    offset = cx
    for label, tone in (
        ("196 listos ✓", TONE_GREEN),
        ("3 escaneados", TONE_YELLOW),
        ("1 dañado", TONE_RED),
        ("5 sin año", TONE_GRAY),
    ):
        offset += k.chip(offset, cy + 102, label, *tone) + 8
    rows = [
        ("⚠ notas_campo_2019.pdf", "Escaneado: pásalo por OCR y vuelve a indexar", YELLOW),
        ("✕ descarga(3).pdf", "Dañado: vuelve a descargarlo de la revista", RED),
        ("◐ Monneveux et al.", "Falta el año para citarlo   [Completar datos]", INK),
        ("✓ Quispe et al., 2019", "Listo para citar · doi:10.5555/spp.2019.0142", GREEN),
    ]
    for index, (title, detail, color) in enumerate(rows):
        top = cy + 146 + index * 56
        b.rect(cx, top, 468, 48, fill="#ffffff", stroke="#dee2e6")
        b.text(cx + 10, top + 6, title, 13, color)
        b.text(cx + 10, top + 26, detail, 12, MUTED)


def compose(b: Board, k: Kit, x: float, y: float) -> None:
    cx, cy = k.window(x, y, SCREEN_W, SCREEN_H, "④ Solicitud", "Nuevo borrador")
    b.text(cx, cy, "¿Qué necesitas escribir?", 20, INK)
    b.rect(cx, cy + 34, 300, 110, fill="#ffffff", stroke_width=2)
    b.text(
        cx + 10,
        cy + 44,
        "Redáctame un borrador del estado del\narte sobre tolerancia a sequía en\npapa, con citas y bibliografía, en un\n.docx que pueda editar.",
        13,
        INK,
    )
    b.text(cx, cy + 152, "Ideas: ✦ Estado del arte…  ✦ Comparar métodos…", 12, MUTED)
    b.text(cx, cy + 180, "Extensión", 12, INK)
    offset = cx
    for label, active in (("Breve", False), ("Media", True), ("Extensa", False)):
        offset += k.chip(offset, cy + 198, label, ACCENT if active else INK, ACCENT_SOFT if active else "#ffffff") + 6
    b.text(cx, cy + 234, "Idioma: Español · Desde el año: 2010 · Estilo: APA 7", 12, INK)
    k.button(cx, cy + 270, "Redactar borrador   Ctrl+Enter")
    b.rect(cx + 316, cy + 34, 152, 200, fill="#ffffff", stroke="#dee2e6")
    b.text(cx + 326, cy + 44, "Qué voy a hacer", 13, INK)
    b.text(
        cx + 326,
        cy + 70,
        "1 Estructura\n2 Buscar evidencia\n   en 196 artículos\n3 Redactar con citas\n4 Verificar cada cita\n\n~3–6 minutos",
        12,
        MUTED,
    )


def progress(b: Board, k: Kit, x: float, y: float) -> None:
    cx, cy = k.window(x, y, SCREEN_W, SCREEN_H, "⑤ Progreso en vivo", "Nuevo borrador")
    b.text(cx, cy, "Estoy redactando tu borrador", 20, INK)
    b.text(cx + 380, cy + 4, "2:41  [Cancelar]", 12, MUTED)
    b.text(cx, cy + 32, "✓ Estructura  ✓ Buscar evidencia  ● Redactar  ○ Verificar  ○ Armar", 12, INK)
    k.progress(cx, cy + 54, 468, 0.58)
    sections = [
        ("1 Contexto y relevancia", "✓ 12 fuentes · 9 afirmaciones · 8 ✓ 1 ◐", GREEN),
        ("2 Respuestas fisiológicas", "Redactando… «La conductancia estomática…»", ACCENT),
        ("3 Bases genéticas", "Buscando evidencia… 5 fuentes", MUTED),
        ("4 Mejoramiento y fenotipado", "En espera", MUTED),
    ]
    for index, (title, detail, color) in enumerate(sections):
        top = cy + 78 + index * 62
        b.rect(cx, top, 300, 54, fill="#ffffff", stroke="#dee2e6")
        b.text(cx + 10, top + 6, title, 13, INK)
        b.text(cx + 10, top + 28, detail, 11, color)
    b.rect(cx + 312, cy + 78, 156, 240, fill="#ffffff", stroke="#dee2e6")
    b.text(cx + 322, cy + 86, "Fuentes consultadas 37", 12, INK)
    b.text(
        cx + 322,
        cy + 112,
        "Quispe et al., 2019\nStomatal regulation…\n\nCondori y Flores, 2021\nRoot architecture…\n\nGutierrez y Choque,\n2022 · QTL mapping…",
        11,
        MUTED,
    )


def review(b: Board, k: Kit, x: float, y: float) -> None:
    width, height = 1360, 560
    cx, cy = k.window(x, y, width, height, "⑥ Revisión de citas · la pantalla más importante", "Mis borradores")
    b.text(cx, cy, "48 afirmaciones · 37 fuentes", 13, INK)
    k.chip(cx + 220, cy - 4, "Revisaste 3 de 7", YELLOW, YELLOW_SOFT)
    b.text(cx + 430, cy, "☐ Solo pendientes", 13, INK)
    k.button(cx + 600, cy - 6, "Exportar")
    b.text(cx, cy + 40, "Estado del arte: tolerancia a sequía en papa", 24, INK)
    b.text(cx, cy + 82, "Respuestas fisiológicas", 18, INK)
    k.lines(cx, cy + 118, 700, 3)
    b.text(cx, cy + 156, "Bajo déficit hídrico progresivo, la papa cierra sus estomas antes de mostrar", 14, INK)
    b.text(cx, cy + 178, "marchitez: la conductancia estomática cayó un 60 % (Quispe et al., 2019).", 14, INK)
    b.rect(cx - 4, cy + 152, 560, 48, fill="transparent", stroke=ACCENT, stroke_width=2)
    b.line([(cx, cy + 200), (cx + 550, cy + 200)], YELLOW, 2, True)
    k.lines(cx, cy + 222, 700, 4)
    b.text(cx, cy + 290, "Bases genéticas", 18, INK)
    k.lines(cx, cy + 326, 700, 3)
    b.text(cx, cy + 372, "Los drones eliminan por completo las mediciones manuales (Nina, 2023).", 14, INK)
    b.line([(cx, cy + 392), (cx + 500, cy + 392)], RED, 2, True)
    k.lines(cx, cy + 414, 700, 2)
    b.text(
        cx, cy + 456, "Leyenda:  ✓ Respaldada    ◐ Respaldo parcial (punteado)    ⚠ Sin respaldo (ondulado)", 12, MUTED
    )
    px = x + 900
    b.rect(px, y + 30, 460, height - 30, fill="#ffffff", stroke_width=2)
    b.text(px + 20, y + 50, "AFIRMACIÓN SELECCIONADA", 11, ACCENT)
    b.text(px + 20, y + 72, "La conductancia estomática cayó un\n60 % antes de la marchitez.", 16, INK)
    k.chip(px + 20, y + 124, "◐ Respaldo parcial", YELLOW, YELLOW_SOFT)
    b.rect(px + 20, y + 158, 420, 46, fill=YELLOW_SOFT, stroke=YELLOW)
    b.text(
        px + 30,
        y + 166,
        "Por qué la marqué: la fuente reporta 58 %, no 60 %.\nEl verificador compara cada número con la página.",
        11,
        INK,
    )
    b.text(px + 330, y + 50, "Siguiente ▸ N", 12, MUTED)
    offset = px + 20
    for label, kind in (("✓ Aceptar (A)", "primary"), ("Editar (E)", "secondary"), ("Quitar (X)", "danger")):
        offset += k.button(offset, y + 216, label, kind) + 10
    b.text(px + 20, y + 262, "De dónde sale (1)", 13, INK)
    b.rect(px + 20, y + 286, 420, 220, fill="#fffdf7", stroke="#dee2e6")
    b.text(px + 32, y + 296, "Quispe et al., 2019", 12, ACCENT)
    b.text(px + 390, y + 296, "p. 4", 12, INK, MONO)
    b.text(
        px + 32,
        y + 318,
        "Stomatal regulation and abscisic acid signalling\nin Andean potato under progressive drought",
        13,
        INK,
    )
    b.line([(px + 32, y + 362), (px + 32, y + 450)], ACCENT, 2)
    b.text(
        px + 42,
        y + 364,
        "«…stomatal conductance decreased by [58 percent]\nwhen soil water content fell below 60 percent\nof field capacity, before any visible wilting.»",
        12,
        INK,
    )
    b.text(px + 32, y + 466, "🔍 Ver en el PDF (p. 4): visor con el pasaje resaltado   ↗ doi", 12, ACCENT)


def export(b: Board, k: Kit, x: float, y: float) -> None:
    cx, cy = k.window(x, y, SCREEN_W, SCREEN_H, "⑦ Exportar", "Mis borradores")
    b.rect(cx - 10, cy - 6, 480, 360, fill="#ffffff", stroke_width=2)
    b.text(cx + 6, cy + 6, "Exportar borrador", 20, INK)
    b.rect(cx + 6, cy + 44, 448, 50, fill=ACCENT_SOFT, stroke=ACCENT)
    b.text(cx + 16, cy + 52, "(•) Word (.docx) — para seguir editando. Recomendado", 13, INK)
    b.text(cx + 16, cy + 72, "Estilos nativos, APA 7, bibliografía", 11, MUTED)
    b.rect(cx + 6, cy + 102, 448, 44, fill="#ffffff", stroke="#dee2e6")
    b.text(cx + 16, cy + 114, "( ) Markdown + BibTeX — para LaTeX / Overleaf", 13, INK)
    b.text(cx + 6, cy + 162, "☑ Incluir comentarios de revisión en Word", 13, INK)
    b.rect(cx + 6, cy + 190, 448, 46, fill=YELLOW_SOFT, stroke=YELLOW)
    b.text(
        cx + 16,
        cy + 198,
        "Quedan 4 afirmaciones sin revisar: irán resaltadas\ncon un comentario y su fuente. Puedes exportar igual.",
        11,
        INK,
    )
    k.button(cx + 330, cy + 252, "Exportar")
    b.rect(cx + 6, cy + 296, 448, 44, fill=GREEN_SOFT, stroke=GREEN)
    b.text(
        cx + 16,
        cy + 304,
        "✓ Guardado en Documentos/Asistente de Investigación\n   [Abrir en Word]  [Mostrar en carpeta]",
        11,
        INK,
    )


def word(b: Board, k: Kit, x: float, y: float) -> None:
    width, height = 640, 560
    b.rect(x, y, width, height, fill="#ffffff", stroke=BLUE, stroke_width=2)
    b.rect(x, y, width, 34, fill=BLUE, stroke=BLUE)
    b.text(x + 14, y + 8, "Word · estado-del-arte-tolerancia-a-sequia-en-papa.docx", 13, "#ffffff")
    b.text(x + 30, y + 54, "Estado del arte: tolerancia a sequía en papa", 18, INK)
    b.rect(x + 30, y + 88, 420, 54, fill=GRAY_SOFT, stroke="#dee2e6")
    b.text(
        x + 40,
        y + 96,
        "Declaración de uso de IA. Generado a partir de 37 artículos\nde tu biblioteca; 41 respaldadas, 5 parciales, 2 sin respaldo.\nQuien firme el documento debe validarlo.",
        10,
        MUTED,
    )
    b.text(x + 30, y + 156, "Respuestas fisiológicas", 15, BLUE)
    k.lines(x + 30, y + 186, 420, 3)
    b.rect(x + 28, y + 222, 300, 20, fill=YELLOW_SOFT, stroke=YELLOW_SOFT)
    b.text(x + 30, y + 224, "…cayó un 60 % (Quispe et al., 2019).", 12, INK)
    b.rect(x + 470, y + 160, 150, 116, fill=YELLOW_SOFT, stroke=YELLOW)
    b.text(
        x + 478,
        y + 168,
        "Verificador de citas\nRespaldo parcial: la\nfuente reporta 58 %.\nFuente: quispe-2019.pdf,\np. 4",
        11,
        INK,
    )
    b.line([(x + 330, y + 232), (x + 470, y + 200)], YELLOW, 1, True)
    k.lines(x + 30, y + 256, 420, 4)
    b.text(x + 30, y + 330, "Referencias", 15, BLUE)
    b.text(
        x + 30,
        y + 360,
        "Condori, M. A. y Flores, A. (2021). Root system architecture…\n       Synthetic Field Crops Research. https://doi.org/…\nQuispe, R. E., Huaman, C. y Vargas, L. (2019). Stomatal\n       regulation… https://doi.org/10.5555/spp.2019.0142",
        11,
        INK,
    )
    b.text(
        x + 30,
        y + 456,
        "También: Markdown con [@quispe2019] + references.bib →\npandoc --citeproc → LaTeX sin pérdida de citas.",
        11,
        MUTED,
    )
    b.text(x, y - 36, "Resultado: el .docx que recibe la investigadora", 20, BLUE, HAND)


def wireframes(b: Board, k: Kit, top: float) -> float:
    b.text(0, top, "Parte A · Pantallas clave y por qué", 40, ACCENT, HAND)
    row = top + 80
    gap = 80
    screens = [
        (
            onboarding,
            "Por qué así",
            [
                "Explico qué pasa con sus PDFs antes de pedirle nada",
                "3 pasos = el modelo mental de todo el flujo",
                "Se puede saltar y volver desde «Cómo funciona»",
            ],
        ),
        (
            library,
            "Por qué así",
            [
                "Progreso por archivo: prueba que leyó todo",
                "Los problemas van primero y con una acción concreta",
                "Puede pedir el borrador sin esperar al 100 %",
                "Metadatos faltantes se corrigen aquí: sin ellos no hay cita",
            ],
        ),
        (
            compose,
            "Por qué así",
            [
                "Lenguaje natural, como se lo pediría a un colega",
                "Solo opciones que cambian el resultado",
                "«Qué voy a hacer» fija método y tiempo esperado",
            ],
        ),
        (
            progress,
            "Por qué así",
            [
                "Minutos de espera se toleran si se ve trabajo real",
                "La estructura aparece primero: puede cancelar si no es su enfoque",
                "Fuentes visibles en vivo = transparencia",
                "Mensajes humanos, nunca logs",
            ],
        ),
    ]
    for index, (draw, title, bullets) in enumerate(screens):
        x = index * (SCREEN_W + gap)
        draw(b, k, x, row)
        k.note(x, row + SCREEN_H + 24, SCREEN_W, title, bullets)
    second = row + SCREEN_H + 240
    review(b, k, 0, second)
    k.note(
        0,
        second + 584,
        1360,
        "Por qué así (la pantalla crítica)",
        [
            "Verificar es la tarea crítica: la fuente aparece al lado, a un clic, con la página y los términos coincidentes",
            "Solo se revisa lo dudoso (7 de 48), no todo: respeta su tiempo",
            "Subrayado + icono + texto: el estado nunca depende solo del color",
            "Atajos A / E / X / N para revisar rápido sin mouse; el borrador se lee como prosa, no como tabla",
        ],
    )
    export(b, k, 1440, second)
    k.note(
        1440,
        second + SCREEN_H + 24,
        SCREEN_W,
        "Por qué así",
        [
            "Su trabajo real sigue en Word con su asesor",
            "Lo pendiente viaja con ella como comentarios",
            "No bloqueo: informo y ella decide",
        ],
    )
    word(b, k, 2160, second + 36)
    return second + 760


def failure_states(b: Board, k: Kit, top: float) -> float:
    b.text(0, top, "Qué pasa cuando algo tarda o sale mal", 36, RED, HAND)
    b.text(
        0,
        top + 50,
        "Regla: cada mensaje dice qué pasó, qué hago yo y qué puede hacer ella. Nunca un error técnico.",
        20,
        MUTED,
        HAND,
    )
    cases = [
        (
            "Sin conexión",
            ["No me puedo comunicar con", "el asistente. Si acabas de abrir", "la app, espera unos segundos."],
            TONE_RED,
        ),
        (
            "Reconectando…",
            ["Sigo trabajando en segundo", "plano; no perderás el avance.", "(SSE + Last-Event-ID)"],
            TONE_YELLOW,
        ),
        (
            "Sin evidencia",
            [
                "No encontré artículos que",
                "respalden este tema. Prueba",
                "términos más generales.",
                "[Ajustar la solicitud]",
            ],
            TONE_YELLOW,
        ),
        ("IA saturada", ["Espera un par de minutos;", "tu solicitud quedó guardada.", "[Intentar de nuevo]"], TONE_RED),
        (
            "PDF escaneado / dañado",
            ["Escaneado → pásalo por OCR.", "Dañado → vuelve a descargarlo.", "El resto se usa normalmente."],
            TONE_YELLOW,
        ),
        (
            "Cancelar",
            [
                "¿Cancelar? Perderás el avance.",
                "[Sí, cancelar] [Seguir]",
                "Confirmación en línea, sin",
                "ventanas emergentes.",
            ],
            TONE_GRAY,
        ),
    ]
    for index, (title, lines, tone) in enumerate(cases):
        k.card(index * 470, top + 100, 430, 210, title, lines, tone)
    return top + 360


def accessibility(b: Board, k: Kit, top: float) -> float:
    k.card(
        0,
        top,
        1360,
        250,
        "Accesibilidad e inclusión",
        [
            "Atkinson Hyperlegible en la interfaz (diseñada para baja visión) y serif para el documento",
            "Contraste AA, escala de texto 90–130 %, modo oscuro y respeto a «reducir movimiento»",
            "Teclado completo: enlace «saltar al contenido», foco gestionado al cambiar de pantalla, atajos de revisión",
            "Lectores de pantalla: landmarks, aria-live para el progreso, cada afirmación anuncia su veredicto",
            "Estados con icono + texto + forma de subrayado: nunca solo color",
            "Español por defecto, borradores en español o inglés",
        ],
        TONE_GREEN,
    )
    k.card(
        1440,
        top,
        1380,
        250,
        "Cómo sabría que funciona (métricas UX)",
        [
            "Tiempo desde instalar hasta el primer borrador: < 10 minutos",
            "% de afirmaciones dudosas revisadas antes de exportar (objetivo: > 90 %)",
            "% de afirmaciones quitadas o editadas: mide la calidad del redactor",
            "Tareas completadas sin ayuda en pruebas con 5 investigadoras del CIP",
            "Reportes de citas incorrectas después de exportar (objetivo: 0)",
        ],
        TONE_BLUE,
    )
    return top + 330


def architecture(b: Board, k: Kit, top: float) -> float:
    b.text(0, top, "Parte B · Arquitectura de alto nivel: de la app al .docx", 40, BLUE, HAND)
    area = top + 80
    b.rect(0, area, 2240, 780, stroke=BLUE, stroke_style="dashed", stroke_width=2, fill="transparent")
    b.text(
        20,
        area + 14,
        "Laptop Windows de la investigadora · instalador .exe autocontenido (sin instalar Python)",
        20,
        BLUE,
        HAND,
    )
    k.box(
        40,
        area + 80,
        420,
        220,
        "App de escritorio · Tauri 2",
        [
            "Núcleo Rust: ventana nativa, diálogos,",
            "lanza y detiene el backend (sidecar)",
            "WebView2 + React/TypeScript: la UI",
            "Solo habla con el gateway",
        ],
        TONE_ACCENT,
    )
    k.box(
        620,
        area + 80,
        420,
        220,
        "gateway · FastAPI (BFF)",
        [
            "REST para comandos",
            "SSE para resultados en vivo",
            "Trabajos y eventos en SQLite:",
            "reanudación con Last-Event-ID",
            "Health agregado de servicios",
        ],
        TONE_BLUE,
    )
    b.arrow([(460, area + 150), (620, area + 150)], ACCENT, width=2)
    b.text(468, area + 120, "① REST comandos", 15, ACCENT, HAND)
    b.arrow([(620, area + 230), (460, area + 230)], BLUE, dashed=True, width=2)
    b.text(468, area + 240, "② SSE eventos", 15, BLUE, HAND)
    k.box(
        1200,
        area + 60,
        500,
        200,
        "library · ingesta + RAG",
        [
            "pypdf por página → metadatos (DOI, autores, año)",
            "chunks por página, sin sección de referencias",
            "embeddings multilingües (fastembed)",
            "SQLite FTS5 (BM25) + vectores → fusión RRF",
            "máx. 2 pasajes por artículo (diversidad)",
        ],
        TONE_GREEN,
    )
    k.box(
        1200,
        area + 290,
        500,
        230,
        "agents · LangGraph",
        [
            "Planificador → por sección en paralelo:",
            "  Investigador → Redactor → Verificador ⟲ Reparador",
            "→ Ensamblador (borrador + referencias)",
            "Ruteo: Haiku 5.5 (planificar, verificar)",
            "          Opus 5.5 (redactar, reparar)",
            "Guardrails: citas solo a pasajes recuperados",
        ],
        TONE_VIOLET,
    )
    k.box(
        1200,
        area + 550,
        500,
        180,
        "documents · python-docx",
        [
            "APA 7 en español, bibliografía con sangría",
            "comentarios de Word en lo pendiente",
            "declaración de uso de IA",
            "Markdown [@clave] + BibTeX para LaTeX",
        ],
        TONE_GRAY,
    )
    b.arrow([(1040, area + 140), (1200, area + 140)], GREEN)
    b.text(1052, area + 108, "③ ingesta NDJSON", 15, GREEN, HAND)
    b.arrow([(1040, area + 260), (1200, area + 380)], VIOLET)
    b.text(1030, area + 330, "④ /runs NDJSON", 15, VIOLET, HAND)
    b.arrow([(1040, area + 290), (1200, area + 620)], INK)
    b.text(980, area + 470, "⑦ exportar", 15, INK, HAND)
    b.arrow([(1450, area + 290), (1450, area + 260)], GREEN, both=True)
    b.text(1462, area + 266, "⑤ búsqueda híbrida", 14, GREEN, HAND)
    for index, (title, detail) in enumerate(
        [
            ("Carpeta de PDFs", "solo lectura"),
            ("AppData", "índice SQLite, trabajos, eventos"),
            ("Documentos/Asistente", ".docx · .md · .bib"),
        ]
    ):
        left = 40 + index * 380
        b.ellipse(left, area + 600, 340, 40, fill=GRAY_SOFT)
        b.rect(left, area + 620, 340, 90, fill=GRAY_SOFT, rounded=False)
        b.text(left + 20, area + 640, title, 18, INK, SANS)
        b.text(left + 20, area + 668, detail, 14, MUTED, SANS)
    k.box(
        2340,
        area + 260,
        480,
        240,
        "API de Claude (externa)",
        [
            "claude-haiku-5-5 · esfuerzo bajo",
            "  planificar y verificar: barato y rápido",
            "claude-opus-5-5 · esfuerzo alto",
            "  redactar y reparar: síntesis de calidad",
            "Fallback del servidor ante rechazos",
            "Solo fragmentos relevantes, nunca el PDF",
        ],
        TONE_VIOLET,
    )
    b.arrow([(1700, area + 400), (2340, area + 400)], VIOLET, width=2, both=True)
    b.text(1820, area + 366, "⑥ HTTPS · salida estructurada", 15, VIOLET, HAND)
    k.box(
        2340,
        area + 560,
        480,
        120,
        "Crossref (opcional)",
        ["Completa metadatos por DOI", "Solo viaja el DOI"],
        TONE_GREEN,
    )
    b.arrow([(1700, area + 200), (2220, area + 200), (2220, area + 620), (2340, area + 620)], GREEN, dashed=True)
    k.note(
        2340,
        area,
        480,
        "Microservicios, una sola instalación",
        [
            "Contratos Pydantic compartidos",
            "En la laptop: un proceso (PyInstaller)",
            "En servidor: docker compose",
            "Mismo código, sin cambios",
        ],
    )
    return area + 860


def deep_dives(b: Board, k: Kit, top: float) -> float:
    b.text(0, top, "Profundización 1 · Comunicación app ↔ backend", 30, BLUE, HAND)
    lanes = [("App de escritorio", 80), ("gateway", 560), ("agents", 1040)]
    for name, x in lanes:
        b.rect(x - 90, top + 60, 180, 44, fill=BLUE_SOFT, stroke=BLUE)
        b.text(x, top + 70, name, 16, BLUE, SANS, "center")
        b.line([(x, top + 104), (x, top + 700)], MUTED, 1, True)
    messages = [
        (80, 560, "POST /v1/drafts  →  202 {job_id}", INK, False),
        (560, 1040, "POST /runs (stream NDJSON)", VIOLET, False),
        (80, 560, "GET /v1/jobs/{id}/events  (EventSource)", INK, False),
        (1040, 560, "section.planned · source.found · …", VIOLET, True),
        (560, 80, "id: 12  data: {section.planned}", BLUE, True),
        (560, 80, "id: 13  data: {source.found}", BLUE, True),
        (80, 560, "💤 laptop suspendida → reconexión: Last-Event-ID: 13", RED, False),
        (560, 80, "replay desde SQLite: id 14, 15… (no se pierde nada)", BLUE, True),
        (80, 560, "POST /v1/jobs/{id}/cancel → cancela la tarea aguas arriba", INK, False),
        (560, 80, "id: 27  data: {job.completed, draft_id, stats}", GREEN, True),
    ]
    for index, (start, end, label, color, dashed) in enumerate(messages):
        y = top + 140 + index * 56
        b.arrow([(start, y), (end, y)], color, dashed=dashed)
        b.text(min(start, end) + 10, y - 24, label, 14, color, SANS)
    k.card(
        0,
        top + 730,
        1360,
        230,
        "Por qué REST + SSE",
        [
            "✓ El flujo es asimétrico: pocas órdenes, muchos eventos. SSE es justo eso, sobre HTTP simple.",
            "✓ EventSource reconecta solo y envía Last-Event-ID; el gateway reproduce lo pendiente.",
            "✓ Funciona igual en local (sidecar) o en servidor y atraviesa proxies corporativos.",
            "✗ WebSocket: bidireccional innecesario; hay que reinventar reconexión y reanudación.",
            "✗ Polling: latencia y carga.  ✗ IPC local: ata el backend a la laptop.",
        ],
        TONE_BLUE,
    )
    x0 = 1440
    b.text(x0, top, "Profundización 2 · Multiagente y ruteo de modelos", 30, VIOLET, HAND)
    k.box(x0, top + 70, 300, 90, "Planificador", ["Haiku 5.5 · low", "secciones + queries en inglés"], TONE_VIOLET, 13)
    b.arrow([(x0 + 300, top + 115), (x0 + 380, top + 115)], VIOLET)
    b.text(x0 + 306, top + 80, "Send × N", 14, VIOLET, HAND)
    b.rect(x0 + 380, top + 60, 1000, 320, stroke=VIOLET, stroke_style="dashed", fill="transparent")
    b.text(x0 + 396, top + 70, "Subgrafo por sección (en paralelo)", 16, VIOLET, HAND)
    nodes = [
        ("Investigador", ["búsqueda híbrida", "sin LLM"], 400),
        ("Redactor", ["Opus 5.5 · high", "cita E1…En"], 640),
        ("Verificador", ["Haiku 5.5 + reglas", "afirmación vs pasaje"], 880),
        ("Reparador", ["Opus 5.5 · medium", "reescribe o descarta"], 1120),
    ]
    for title, lines, offset in nodes:
        k.box(x0 + offset, top + 110, 220, 100, title, lines, TONE_VIOLET, 13)
    for start in (620, 860):
        b.arrow([(x0 + start, top + 160), (x0 + start + 20, top + 160)], VIOLET)
    b.arrow([(x0 + 1100, top + 140), (x0 + 1120, top + 140)], RED)
    b.arrow(
        [(x0 + 1230, top + 210), (x0 + 1230, top + 260), (x0 + 990, top + 260), (x0 + 990, top + 210)], RED, dashed=True
    )
    b.text(x0 + 1000, top + 266, "si hay afirmaciones sin respaldo (1 intento)", 13, RED, HAND)
    b.text(x0 + 400, top + 300, "Lo que sigue dudoso → revisión humana en la app y comentario en Word", 15, INK, HAND)
    k.box(x0 + 380, top + 400, 300, 90, "Ensamblador", ["determinista", "borrador + referencias CSL"], TONE_GRAY, 13)
    b.arrow([(x0 + 880, top + 380), (x0 + 680, top + 445)], INK)
    k.card(
        x0,
        top + 520,
        1380,
        200,
        "Ruteo: el modelo según la tarea",
        [
            "Planificar / verificar → claude-haiku-5-5, esfuerzo bajo: salidas cortas, estructuradas, de alto volumen",
            "Redactar → claude-opus-5-5, esfuerzo alto: sintetizar entre estudios es donde la calidad se nota",
            "Reparar → claude-opus-5-5, esfuerzo medio · Escalamiento a Opus si Haiku se niega o devuelve JSON inválido",
            "Fallback del servidor en Opus · salidas estructuradas (Pydantic) en todos los pasos",
        ],
        TONE_VIOLET,
    )
    k.card(
        x0,
        top + 740,
        1380,
        220,
        "Guardrails contra citas inventadas",
        [
            "1. El redactor solo puede citar ids de pasajes recuperados; cualquier otra cita se descarta y se avisa",
            "2. Afirmación sin cita = sin respaldo · 3. Número que no está en la fuente = respaldo parcial",
            "4. Verificación afirmación por afirmación · 5. Un ciclo de reparación automática",
            "6. Antes de entregar: toda cita apunta a un pasaje de su biblioteca · Modo sin conexión para pruebas",
        ],
        TONE_RED,
    )
    return top + 1020


def other_topics(b: Board, k: Kit, top: float) -> None:
    k.card(
        0,
        top,
        900,
        260,
        "RAG sobre la biblioteca (resumen)",
        [
            "Extracción por página → la cita puede decir «p. 4»",
            "DOI por regex + año/título/autores; Crossref opcional",
            "Sin sección de referencias ni encabezados de revista",
            "Pregunta en español, artículos en inglés: embeddings",
            "multilingües + queries en inglés del planificador",
            "Ingesta incremental por hash: reabrir es instantáneo",
        ],
        TONE_GREEN,
    )
    k.card(
        960,
        top,
        900,
        260,
        "Uso responsable de la IA",
        [
            "Los PDFs no salen de la laptop; solo fragmentos",
            "Declaración de uso de IA en cada documento",
            "Validación experta obligatoria: nada se exporta como",
            "«verificado» sin que ella lo vea",
            "Proveedor aprobado por el CIP, sin entrenar con datos",
            "Sin datos personales en prompts, fixtures ni logs",
        ],
        TONE_ACCENT,
    )
    k.card(
        1920,
        top,
        900,
        260,
        "Pruebas, CI/CD y distribución",
        [
            "pytest por servicio + prueba end-to-end de los 4",
            "Vitest en la UI · clippy/rustfmt en el núcleo Rust",
            "GitHub Actions: CI en cada PR, Docker, instalador",
            "Windows: PyInstaller (sidecar) + Tauri → NSIS/MSI",
            "Release con tag v* · Dependabot semanal",
            "Docs: README, ADRs, guía de usuaria en la app",
        ],
        TONE_GRAY,
    )


def quality(b: Board, k: Kit, top: float) -> None:
    k.card(
        0,
        top,
        2820,
        160,
        "Cómo se mide la calidad · make eval (pandas + scikit-learn, corre en cada PR)",
        [
            "Recuperación, 14 consultas con su artículo esperado: en inglés recall@1 = 1.00. Preguntando en español: 0.25 con embeddings simples → 1.00 con embeddings multilingües.",
            "Verificador, 12 afirmaciones etiquetadas: exactitud 0.92. La regla de números atrapa todos los valores alterados.",
            "Su único error es una contradicción («la prolina fue el mejor predictor»), que solo detecta el verificador con LLM: queda como prueba de regresión.",
            "Punta a punta: 0 citas fuera de la biblioteca. Si una métrica baja de su umbral, el CI falla y el reporte queda en el resumen del job.",
        ],
        TONE_BLUE,
    )


def build(target: Path) -> None:
    board = Board()
    kit = Kit(board)
    header(board, kit)
    journey(board, 440)
    after_screens = wireframes(board, kit, 640)
    after_failures = failure_states(board, kit, after_screens)
    after_accessibility = accessibility(board, kit, after_failures)
    after_architecture = architecture(board, kit, after_accessibility + 60)
    after_dives = deep_dives(board, kit, after_architecture)
    other_topics(board, kit, after_dives)
    quality(board, kit, after_dives + 300)
    board.save(target)


if __name__ == "__main__":
    build(Path(__file__).with_name("cip-research-assistant.excalidraw"))
