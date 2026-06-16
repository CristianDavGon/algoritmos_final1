"""Visualización adaptable de sistemas de N-Cubos con Manim.

Módulo auxiliar del proyecto K-QGMIP que demuestra la proyección
recursiva de hipercubos de dimensión arbitraria y la comparación
entre un hipercubo 4D original y su versión 3D obtenida mediante
promediado del último eje.

Escena:

- ``NCubeSystem``: muestra un hipercubo 4D junto con el cubo 3D
  resultante de aplicar ``np.mean`` sobre la cuarta dimensión y
  anima una transformación (morfismo) entre ambas representaciones.

Uso típico::

    manim -pql hyper-v3.py NCubeSystem
"""

from __future__ import annotations

import itertools

import numpy as np
from manim import (
    BLUE,
    DOWN,
    LEFT,
    ORIGIN,
    OUT,
    RED,
    RIGHT,
    UP,
    WHITE,
    Create,
    Line3D,
    Sphere,
    Text,
    ThreeDScene,
    Transform,
    VGroup,
    Write,
    interpolate_color,
)

# ---------------------------------------------------------------------------
# Constantes de módulo
# ---------------------------------------------------------------------------
CAMARA_PHI: float = 70.0          # Ángulo polar de la cámara (grados).
CAMARA_THETA: float = -30.0       # Ángulo azimutal de la cámara (grados).
RADIO_VERTICE: float = 0.10       # Radio de esfera para vértices.
GROSOR_ARISTA: float = 0.02       # Grosor de las aristas 3D.
ESCALA_CUBO: float = 2.0          # Factor de escalado de coordenadas.
OFFSET_CENTRADO: float = 1.0      # Desplazamiento para centrar el cubo.
OFFSET_EXTRA: float = 1.5         # Desplazamiento por cada dimensión extra.
FUENTE_ETIQUETA: int = 14         # Tamaño de fuente para etiquetas de vértice.
FUENTE_LABEL_CUBO: int = 24       # Tamaño de fuente para etiquetas de cubo.
TIEMPO_ESPERA_INICIAL: float = 1.0
TIEMPO_ESPERA_FINAL: float = 3.0


class NCubeSystem(ThreeDScene):
    """Escena que compara un hipercubo 4D con su reducción 3D promediada.

    Crea dos representaciones visuales: el hipercubo 4D original a la
    izquierda y el cubo 3D resultante de promediar la cuarta dimensión
    a la derecha, y anima la transformación entre ellas.
    """

    def construct(self) -> None:
        """Construye y anima la comparación entre representaciones."""
        self.set_camera_orientation(
            phi=CAMARA_PHI * DEGREES,
            theta=CAMARA_THETA * DEGREES,
        )

        hypercube = np.array([
            [
                [[0.0, 1.0], [1.0, 0.0]],
                [[0.5, 0.5], [0.5, 0.5]],
            ],
            [
                [[0.5, 0.5], [0.5, 0.5]],
                [[1.0, 0.0], [0.0, 1.0]],
            ],
        ])

        original = self.create_hypercube(hypercube, LEFT * 3)
        original_label = Text(
            "4D Original", font_size=FUENTE_LABEL_CUBO
        ).next_to(original, DOWN)

        # Reducción de dimensión: promedio sobre el eje 3 (4.ª dimensión)
        transformed_data = np.mean(hypercube, axis=3, keepdims=False)
        transformed = self.create_hypercube(transformed_data, RIGHT * 3)
        transformed_label = Text(
            "3D Promediado", font_size=FUENTE_LABEL_CUBO
        ).next_to(transformed, DOWN)

        self.play(
            Create(original),
            Write(original_label),
            run_time=2,
        )
        self.wait(TIEMPO_ESPERA_INICIAL)

        self.play(
            Transform(original.copy(), transformed),
            Write(transformed_label),
            run_time=3,
        )
        self.wait(TIEMPO_ESPERA_FINAL)

    def create_hypercube(
        self,
        data: np.ndarray,
        position: np.ndarray = ORIGIN,
    ) -> VGroup:
        """Visualiza un N-cubo usando proyección jerárquica recursiva.

        Proyecta cada vértice del hipercubo al espacio 3D de forma
        recursiva: las primeras tres dimensiones definen las coordenadas
        base y las dimensiones adicionales se codifican como
        desplazamientos a lo largo de ``RIGHT``, ``UP`` u ``OUT``.

        Args:
            data: Array NumPy de forma ``(2, 2, ..., 2)`` con los valores
                escalares de cada vértice. Todas las dimensiones deben
                tener tamaño 2.
            position: Vector de traslación 3D. Por defecto ``ORIGIN``.

        Returns:
            ``VGroup`` con esferas (vértices), etiquetas de valor y
            líneas (aristas) del hipercubo.
        """
        n_dims = data.ndim
        vertices = list(itertools.product([0, 1], repeat=n_dims))

        # Direcciones para desplazamientos de dimensiones extra
        offset_dirs = [RIGHT, UP, OUT]

        def project(v: tuple) -> np.ndarray:
            """Proyecta recursivamente un vértice n-dimensional a R³.

            Args:
                v: Tupla de 0s y 1s con las coordenadas del vértice.

            Returns:
                Array NumPy ``(3,)`` con la posición 3D proyectada.
            """
            if len(v) <= 3:
                padded = list(v) + [0] * (3 - len(v))
                return (
                    np.array(padded, dtype=float) * ESCALA_CUBO
                    - np.array([OFFSET_CENTRADO] * 3)
                )
            extra_index = len(v) - 3   # 1 para 4D, 2 para 5D, etc.
            offset_dir = offset_dirs[(extra_index - 1) % len(offset_dirs)]
            return project(v[:-1]) + v[-1] * OFFSET_EXTRA * offset_dir

        cube = VGroup()
        edge_cache: set = set()

        for v in vertices:
            pos = project(v) + position
            value = float(data[tuple(v)])

            sphere = Sphere(
                radius=RADIO_VERTICE, color=self.color_map(value)
            )
            sphere.move_to(pos)
            label = Text(
                f"{value:.1f}", font_size=FUENTE_ETIQUETA
            ).next_to(pos, OUT)
            cube.add(sphere, label)
            self.add_fixed_in_frame_mobjects(label)

            # Aristas hacia vértices vecinos (distancia Hamming = 1)
            for i in range(n_dims):
                neighbor = list(v)
                neighbor[i] = 1 - neighbor[i]
                neighbor_t = tuple(neighbor)
                if neighbor_t in set(vertices):
                    edge_key = tuple(sorted((v, neighbor_t)))
                    if edge_key not in edge_cache:
                        start = project(v) + position
                        end = project(neighbor_t) + position
                        line = Line3D(
                            start, end,
                            color=WHITE,
                            thickness=GROSOR_ARISTA,
                        )
                        cube.add(line)
                        edge_cache.add(edge_key)

        return cube

    def color_map(self, value: float):
        """Mapea un valor escalar a un color en escala azul-rojo.

        Args:
            value: Valor en el rango ``[0, 1]``.

        Returns:
            Color de Manim resultante de la interpolación.
        """
        return interpolate_color(BLUE, RED, value)
