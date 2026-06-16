"""Visualización de N-Cubos con proyección de matriz aleatoria a R³.

Módulo auxiliar del proyecto K-QGMIP que representa un N-cubo de
dimensión arbitraria proyectando sus vértices al espacio 3D mediante
una matriz de proyección aleatoria ortonormalizada (o la identidad
para ``n=3``). Los valores de cada vértice se muestran sobre un fondo
translúcido y las aristas se colorean según el eje dimensional al que
pertenecen.

Escena:

- ``NCubeVisualization``: visualización estática de un cubo 3D de
  ejemplo con etiquetas de valor en cada vértice.

Uso típico::

    manim -pql hyper-v4.py NCubeVisualization
"""

from __future__ import annotations

import itertools

import numpy as np
from manim import (
    BLACK,
    BLUE,
    DEGREES,
    LOGO_BLUE,
    ORIGIN,
    TEAL,
    UL,
    WHITE,
    Circle,
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
RADIO_FONDO_VERTICE: float = 0.15 # Radio del círculo de fondo del vértice.
FUENTE_TITULO: int = 36           # Tamaño de fuente para el título.
FUENTE_VALOR: int = 24            # Tamaño de fuente para etiquetas de valor.
TIEMPO_ESPERA: float = 2.0        # Tiempo de espera al final de la escena.
SEMILLA_ALEATORIA: int = 0        # Semilla fija para reproducibilidad.

# Colores para cada eje dimensional (cubo 3D)
COLORES_DIMENSIONES = [LOGO_BLUE, BLUE, TEAL]


class NCubeVisualization(ThreeDScene):
    """Escena 3D que visualiza un N-cubo con proyección matricial.

    Para ``n=3`` utiliza la identidad como proyección. Para ``n>3``
    genera una matriz aleatoria con filas ortonormalizadas que mapea
    R^n a R³.
    """

    def construct(self) -> None:
        """Construye la escena con etiquetas de valor en cada vértice."""
        self.set_camera_orientation(
            phi=CAMARA_PHI * DEGREES,
            theta=CAMARA_THETA * DEGREES,
        )
        self.camera.frame_center = ORIGIN

        title = Text(
            "Visualizador de N-Cubos", font_size=FUENTE_TITULO
        )
        title.to_corner(UL)
        self.add_fixed_in_frame_mobjects(title)

        # Número de dimensiones del NCube de ejemplo
        n = 3

        # Datos del NCube (cubo 3D con array de forma (2, 2, 2))
        ncube_data = np.array([
            [[0., 1.], [1., 0.]],
            [[0., 1.], [1., 0.]],
        ])

        # Vértices: combinaciones de 0 y 1, centrados en el origen
        vertices = [
            np.array(v, dtype=float) - 0.5
            for v in itertools.product([0, 1], repeat=n)
        ]

        # Matriz de proyección R^n → R³
        if n == 3:
            P = np.eye(3)
        else:
            rng = np.random.default_rng(SEMILLA_ALEATORIA)
            raw = rng.standard_normal((3, n))
            P = raw / np.linalg.norm(raw, axis=1, keepdims=True)

        projected_vertices = [np.dot(P, v) for v in vertices]

        # Crear indicadores de valor en cada vértice
        for v, proj in zip(vertices, projected_vertices):
            index = tuple(int(coord + 0.5) for coord in v)
            cube_value = ncube_data[index]

            bg_circle = Circle(
                radius=RADIO_FONDO_VERTICE,
                color=WHITE,
                fill_color=BLACK,
                fill_opacity=0.2,
            )
            bg_circle.set_flat(True)
            bg_circle.move_to(proj)

            value_text = Text(
                str(cube_value), font_size=FUENTE_VALOR, color=WHITE
            )
            value_text.set_flat(True)
            value_text.move_to(proj)

            vertex_group = VGroup(bg_circle, value_text)
            self.add(vertex_group)

        # Aristas coloreadas por dimensión
        for i, v1 in enumerate(vertices):
            for j, v2 in enumerate(vertices):
                if j <= i:
                    continue
                diff = np.abs(v1 - v2)
                if not np.isclose(np.sum(diff), 1.0):
                    continue
                dim = int(np.argmax(diff))
                start = np.dot(P, v1)
                end = np.dot(P, v2)
                color = COLORES_DIMENSIONES[dim % len(COLORES_DIMENSIONES)]
                line = Line3D(start, end, color=color)
                self.add(line)

        self.play(Write(title))
        self.wait(TIEMPO_ESPERA)
