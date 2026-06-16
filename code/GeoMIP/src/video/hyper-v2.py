"""Visualización de un hipercubo 4D proyectado al espacio 3D con Manim.

Módulo auxiliar del proyecto K-QGMIP que implementa la proyección
estereográfica modificada de un tesseracto (hipercubo de cuatro
dimensiones) en una escena 3D animada.

Las aristas se colorean según la coordenada que cambia entre los dos
vértices que unen (X→rojo, Y→verde, Z→azul, W→amarillo), facilitando
la identificación visual de cada eje del hipercubo.

Escena:

- ``Hipercubo``: proyecta los 16 vértices y 32 aristas del tesseracto
  al espacio 3D y los anima con rotación ambiental continua.

Uso típico::

    manim -pql hyper-v2.py Hipercubo
"""

from __future__ import annotations

import numpy as np
from manim import (
    BLUE_B,
    DEGREES,
    DOWN,
    DR,
    GREEN_B,
    LEFT,
    RED_B,
    UL,
    YELLOW_B,
    Create,
    Dot,
    Dot3D,
    FadeIn,
    Line3D,
    Text,
    ThreeDScene,
    VGroup,
    Write,
)

# ---------------------------------------------------------------------------
# Constantes de módulo
# ---------------------------------------------------------------------------
CAMARA_PHI: float = 75.0          # Ángulo polar de la cámara (grados).
CAMARA_THETA: float = 30.0        # Ángulo azimutal de la cámara (grados).
W_FACTOR: float = 2.0             # Factor de proyección estereográfica.
W_ATENUACION: float = 0.5         # Atenuación de la 4.ª coordenada.
RADIO_VERTICE: float = 0.08       # Radio de los puntos de los vértices.
GROSOR_ARISTA: float = 0.03       # Grosor de las aristas 3D.
RADIO_LEYENDA: float = 0.10       # Radio de puntos en la leyenda.
TASA_ROTACION: float = 0.10       # Velocidad de rotación ambiental.
TIEMPO_ESPERA: float = 8.0        # Tiempo de espera al final.
FUENTE_TITULO: int = 36           # Tamaño de fuente para título.
FUENTE_SUBTITULO: int = 24        # Tamaño de fuente para subtítulo.
FUENTE_LEYENDA_TITULO: int = 20   # Tamaño de fuente para título de leyenda.
FUENTE_LEYENDA_ITEM: int = 16     # Tamaño de fuente para ítems de leyenda.

# Colores para cada coordenada del hipercubo (X, Y, Z, W)
COLORES_COORDENADAS = [RED_B, GREEN_B, BLUE_B, YELLOW_B]
NOMBRES_COORDENADAS = ["X", "Y", "Z", "W"]


def _project_4d_to_3d(
    point_4d: list[float],
    w_factor: float = W_FACTOR,
    w_atenuacion: float = W_ATENUACION,
) -> np.ndarray:
    """Proyecta un punto 4D al espacio 3D mediante proyección estereográfica.

    Aplica la fórmula ``factor = 1 / (w_factor - w * w_atenuacion)`` para
    reducir la convergencia de líneas hacia el centro de la escena.

    Args:
        point_4d: Lista ``[x, y, z, w]`` con las coordenadas 4D del punto.
        w_factor: Factor base del denominador. Controla la distancia focal.
        w_atenuacion: Ponderación de la cuarta coordenada en el denominador.

    Returns:
        Array NumPy de forma ``(3,)`` con las coordenadas 3D proyectadas.
    """
    x, y, z, w = point_4d
    factor = 1.0 / (w_factor - w * w_atenuacion)
    return np.array([x * factor, y * factor, z * factor])


class Hipercubo(ThreeDScene):
    """Escena 3D que visualiza un hipercubo 4D (tesseracto).

    Genera los 16 vértices del tesseracto con coordenadas en ``{-1, 1}^4``,
    los proyecta al espacio 3D y dibuja sus 32 aristas con colores que
    identifican el eje dimensional que conecta cada par de vértices.
    """

    def construct(self) -> None:
        """Construye la escena del hipercubo con título, leyenda y animación."""
        self.set_camera_orientation(
            phi=CAMARA_PHI * DEGREES,
            theta=CAMARA_THETA * DEGREES,
        )
        self.camera.frame_center = np.array([0.0, 0.0, 0.0])

        title = Text(
            "Visualización del Hipercubo 4D", font_size=FUENTE_TITULO
        )
        title.to_corner(UL)
        self.add_fixed_in_frame_mobjects(title)

        # Generar los 16 vértices del hipercubo 4D
        vertices_4d = [
            [x, y, z, w]
            for x in [-1, 1]
            for y in [-1, 1]
            for z in [-1, 1]
            for w in [-1, 1]
        ]
        vertices_3d = [_project_4d_to_3d(v) for v in vertices_4d]

        dots = VGroup(
            *[
                Dot3D(point=p, color=BLUE_B, radius=RADIO_VERTICE)
                for p in vertices_3d
            ]
        )

        # Aristas: vértices adyacentes que difieren en exactamente 1 coordenada
        lines = VGroup()
        for i, v1 in enumerate(vertices_4d):
            for j, v2 in enumerate(vertices_4d):
                if i >= j:
                    continue
                diffs = [a != b for a, b in zip(v1, v2)]
                if sum(diffs) != 1:
                    continue
                diff_index = diffs.index(True)
                line = Line3D(
                    vertices_3d[i],
                    vertices_3d[j],
                    color=COLORES_COORDENADAS[diff_index],
                    thickness=GROSOR_ARISTA,
                )
                lines.add(line)

        hypercube = VGroup(lines, dots)

        subtitle = Text(
            "Proyección 3D de un cubo 4-dimensional",
            font_size=FUENTE_SUBTITULO,
        )
        subtitle.next_to(title, DOWN).align_to(title, LEFT)
        self.add_fixed_in_frame_mobjects(subtitle)

        legend_title = (
            Text("Coordenadas:", font_size=FUENTE_LEYENDA_TITULO)
            .to_corner(DR)
            .shift(UP * 1.5 + LEFT * 0.5)
        )
        self.add_fixed_in_frame_mobjects(legend_title)

        legend_items = VGroup()
        for name, color in zip(NOMBRES_COORDENADAS, COLORES_COORDENADAS):
            dot = Dot(color=color, radius=RADIO_LEYENDA)
            label = Text(name, font_size=FUENTE_LEYENDA_ITEM, color=color)
            item = VGroup(dot, label)
            label.next_to(dot, RIGHT, buff=0.1)
            legend_items.add(item)

        legend_items.arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        legend_items.next_to(legend_title, DOWN, aligned_edge=LEFT)
        self.add_fixed_in_frame_mobjects(legend_items)

        self.play(Write(title), Write(subtitle), run_time=1)
        self.play(FadeIn(legend_title), FadeIn(legend_items), run_time=1)
        self.play(Create(lines), run_time=2)
        self.play(Create(dots), run_time=1)

        self.begin_ambient_camera_rotation(rate=TASA_ROTACION)
        self.wait(TIEMPO_ESPERA)
