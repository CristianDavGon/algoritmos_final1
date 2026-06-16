"""Visualización genérica de N-Cubos n-dimensionales con Manim.

Módulo auxiliar del proyecto K-QGMIP que permite representar hipercubos
de dimensión arbitraria mediante proyección jerárquica al espacio 3D.

Escena principal:

- ``NCubeDataVisualization``: toma un array NumPy de forma
  ``(2, 2, ..., 2)`` y construye la representación 3D del
  hipercubo correspondiente con esferas y aristas coloreadas.

Uso típico::

    manim -pql hyper-v1.py NCubeDataVisualization
"""

from __future__ import annotations

import itertools

import numpy as np
from manim import (
    BLUE,
    GREY,
    OUT,
    ORIGIN,
    RED,
    Create,
    Line3D,
    Sphere,
    Text,
    ThreeDScene,
    VGroup,
    interpolate_color,
)

# ---------------------------------------------------------------------------
# Constantes de módulo
# ---------------------------------------------------------------------------
RADIO_VERTICE: float = 0.10       # Radio de esfera para vértices.
GROSOR_ARISTA: float = 0.02       # Grosor de las aristas 3D.
ESCALA_CUBO: float = 2.0          # Factor de escalado de coordenadas.
OFFSET_CENTRADO: float = 1.0      # Desplazamiento para centrar el cubo.
SEPARACION_EXTRA: float = 0.5     # Separación para dimensiones > 3.
FUENTE_ETIQUETA: int = 14         # Tamaño de fuente para etiquetas de vértice.
TIEMPO_ESPERA: float = 2.0        # Tiempo de espera al final de la escena.


class NCubeDataVisualization(ThreeDScene):
    """Visualización 3D de un hipercubo n-dimensional con datos en vértices.

    Proyecta hipercubos de dimensión arbitraria al espacio 3D usando las
    primeras tres dimensiones como ejes base y desplazamientos adicionales
    para las dimensiones superiores.
    """

    def construct(self) -> None:
        """Construye la escena: crea el hipercubo y lanza la animación."""
        # Ejemplo de datos 4D (shape = 2×2×2×2)
        ncube_data = np.array([
            [
                [[0.0, 1.0], [1.0, 0.0]],
                [[0.5, 0.5], [0.5, 0.5]],
            ],
            [
                [[0.5, 0.5], [0.5, 0.5]],
                [[1.0, 0.0], [0.0, 1.0]],
            ],
        ])

        cube = self.create_cube_with_data(ncube_data)
        self.play(Create(cube))
        self.wait(TIEMPO_ESPERA)

    def create_cube_with_data(
        self,
        data: np.ndarray,
        position: np.ndarray = ORIGIN,
    ) -> VGroup:
        """Crea la representación visual de un hipercubo n-dimensional.

        Proyecta cada vértice al espacio 3D usando las tres primeras
        dimensiones como ejes cartesianos y aplica desplazamientos
        aditivos sobre los ejes para las dimensiones superiores.

        Args:
            data: Array NumPy de forma ``(2, 2, ..., 2)`` donde cada
                elemento contiene el valor escalar del vértice
                correspondiente. Se exige que todas las dimensiones
                tengan tamaño 2.
            position: Vector de traslación 3D. Por defecto ``ORIGIN``.

        Returns:
            ``VGroup`` con las esferas (vértices), etiquetas de valor y
            líneas (aristas) que componen el hipercubo.

        Raises:
            AssertionError: Si alguna dimensión del array no es de tamaño 2.
        """
        assert all(dim == 2 for dim in data.shape), (
            "El array debe ser 2×2×…×2"
        )

        n_dims = data.ndim
        vertices = list(itertools.product([0, 1], repeat=n_dims))

        # Proyección 3D con ajuste para dimensiones superiores
        scale = ESCALA_CUBO
        delta = SEPARACION_EXTRA
        projected: list[np.ndarray] = []

        for v in vertices:
            # Base 3D: rellenar con ceros si hay menos de 3 dimensiones
            coords = list(v[:3]) + [0] * (3 - len(v))
            pos = (
                np.array(coords) * scale
                - np.array([OFFSET_CENTRADO] * 3)
            )
            # Desplazamiento por dimensiones extra (> 3)
            for dim in range(3, n_dims):
                axis = (dim - 3) % 3   # Alternar ejes X/Y/Z
                pos[axis] += v[dim] * delta
            projected.append(pos + position)

        cube_group = VGroup()
        values = [float(data[v]) for v in vertices]

        # Vértices y etiquetas
        for i, pos in enumerate(projected):
            color = self.get_color_from_value(values[i])
            dot = Sphere(radius=RADIO_VERTICE, color=color).move_to(pos)
            label = Text(
                f"{values[i]:.1f}", font_size=FUENTE_ETIQUETA
            ).next_to(pos, OUT)
            cube_group.add(dot, label)
            self.add_fixed_in_frame_mobjects(label)

        # Aristas: conectar vértices adyacentes (distancia Hamming = 1)
        for i, j in itertools.combinations(range(len(vertices)), 2):
            if (
                sum(
                    a != b
                    for a, b in zip(vertices[i], vertices[j])
                )
                == 1
            ):
                line = Line3D(
                    projected[i],
                    projected[j],
                    color=GREY,
                    thickness=GROSOR_ARISTA,
                )
                cube_group.add(line)

        return cube_group

    def get_color_from_value(self, value: float):
        """Devuelve un color interpolado entre azul (0) y rojo (1).

        Args:
            value: Valor escalar en el rango ``[0, 1]``.

        Returns:
            Color de Manim resultante de la interpolación.
        """
        return interpolate_color(BLUE, RED, value)
