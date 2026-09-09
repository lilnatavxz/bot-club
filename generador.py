import textwrap
from PIL import Image, ImageDraw, ImageFont

RUTA_PLANTILLA = "assets/plantilla1.png"
RUTA_FUENTE_TITULO = "assets/DejaVuSerif-Bold.ttf"
RUTA_FUENTE_CONTENIDO = "assets/DejaVuSerif.ttf"

COLOR_TEXTO = (10, 10, 10)
COLOR_CAJA_BLANCA = (253, 253, 251)

# Coordenadas calibradas a partir de la plantilla real (1254x1254 px).
# El cuadro blanco principal ocupa aproximadamente x:[97,1156] y:[362,923]
CAJA_TITULO = {"x0": 140, "x1": 1114, "y0": 372, "y1": 460}
CAJA_CONTENIDO = {"x0": 150, "x1": 1104, "y0": 480, "y1": 905}


def _ajustar_lineas(draw, texto, fuente_path, ancho_max, tam_inicial, tam_minimo, interlineado=1.25):
    """Prueba tamaños de fuente de mayor a menor hasta que el texto envuelto entre en el ancho."""
    for tam in range(tam_inicial, tam_minimo - 1, -2):
        fuente = ImageFont.truetype(fuente_path, tam)
        palabras = texto.split()
        lineas = []
        linea_actual = ""

        for palabra in palabras:
            prueba = f"{linea_actual} {palabra}".strip()
            ancho = draw.textlength(prueba, font=fuente)
            if ancho <= ancho_max:
                linea_actual = prueba
            else:
                if linea_actual:
                    lineas.append(linea_actual)
                linea_actual = palabra
        if linea_actual:
            lineas.append(linea_actual)

        return fuente, lineas, tam

    # nunca debería llegar acá, pero por las dudas devolvemos el tamaño mínimo
    fuente = ImageFont.truetype(fuente_path, tam_minimo)
    return fuente, [texto], tam_minimo


def _texto_cabe(draw, lineas, fuente, alto_max, interlineado=1.25):
    alto_linea = fuente.size * interlineado
    return len(lineas) * alto_linea <= alto_max


def _dibujar_bloque(draw, texto, fuente_path, caja, tam_inicial, tam_minimo, alinear="centro_v"):
    ancho_max = caja["x1"] - caja["x0"]
    alto_max = caja["y1"] - caja["y0"]

    fuente, lineas, tam = None, None, tam_inicial
    for candidato in range(tam_inicial, tam_minimo - 1, -2):
        f, l, t = _ajustar_lineas(draw, texto, fuente_path, ancho_max, candidato, candidato)
        if _texto_cabe(draw, l, f, alto_max):
            fuente, lineas, tam = f, l, t
            break

    if fuente is None:
        fuente, lineas, tam = _ajustar_lineas(draw, texto, fuente_path, ancho_max, tam_minimo, tam_minimo)

    alto_linea = fuente.size * 1.25
    alto_total = len(lineas) * alto_linea

    if alinear == "centro_v":
        y = caja["y0"] + (alto_max - alto_total) / 2
    else:
        y = caja["y0"]

    for linea in lineas:
        ancho_linea = draw.textlength(linea, font=fuente)
        x = caja["x0"] + (ancho_max - ancho_linea) / 2
        draw.text((x, y), linea, font=fuente, fill=COLOR_TEXTO)
        y += alto_linea


def generar_comunicado(titulo: str, contenido: str) -> Image.Image:
    imagen = Image.open(RUTA_PLANTILLA).convert("RGBA")
    draw = ImageDraw.Draw(imagen)

    # Tapamos el placeholder "Título" original y cualquier resto en el área de
    # contenido, pintando de blanco (el mismo blanco del cuadro) antes de escribir.
    draw.rectangle(
        [CAJA_TITULO["x0"] - 20, CAJA_TITULO["y0"] - 10, CAJA_TITULO["x1"] + 20, CAJA_TITULO["y1"] + 10],
        fill=COLOR_CAJA_BLANCA
    )
    draw.rectangle(
        [CAJA_CONTENIDO["x0"] - 20, CAJA_CONTENIDO["y0"] - 10, CAJA_CONTENIDO["x1"] + 20, CAJA_CONTENIDO["y1"] + 10],
        fill=COLOR_CAJA_BLANCA
    )

    _dibujar_bloque(
        draw, titulo.upper(), RUTA_FUENTE_TITULO, CAJA_TITULO,
        tam_inicial=56, tam_minimo=24, alinear="centro_v"
    )
    _dibujar_bloque(
        draw, contenido, RUTA_FUENTE_CONTENIDO, CAJA_CONTENIDO,
        tam_inicial=34, tam_minimo=16, alinear="arriba"
    )

    return imagen
