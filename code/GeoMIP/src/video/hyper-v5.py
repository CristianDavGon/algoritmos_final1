"""Visualizador 2D de N-Cubos con proyección isométrica y cubos anidados.

Módulo auxiliar del proyecto K-QGMIP que representa hipercubos de
dimensión 0 a 5 en una escena 2D. Usa proyección isométrica para
dimensiones ≤ 3 y el enfoque de «cubos anidados» para dimensiones
superiores. Las aristas se colorean según el eje dimensional al que
pertenecen y los vértices muestran su valor escalar en escala azul-rojo.

Escenas:

- ``NCubeVisualizer``: recorre de 0D a 4D mostrando cada hipercubo
  por separado, con leyenda de dimensiones y barra de color.
- ``Hypercube5D``: hereda de ``NCubeVisualizer`` y muestra el caso
  de 5 dimensiones.

Uso típico::

    manim -pql hyper-v5.py NCubeVisualizer
    manim -pql hyper-v5.py Hypercube5D
"""

from __future__ import annotations

import itertools

import numpy as np
from manim import (
    BLUE,
    DOWN,
    DR,
    GREEN,
    LEFT,
    MAROON,
    ORANGE,
    PURPLE,
    RED,
    RIGHT,
    TEAL,
    UP,
    WHITE,
    YELLOW,
    Create,
    Dot,
    FadeIn,
    Line,
    Rectangle,
    Rotate,
    Scene,
    Text,
    VGroup,
    Write,
    interpolate_color,
)

# ---------------------------------------------------------------------------
# Constantes de módulo
# ---------------------------------------------------------------------------
RADIO_VERTICE: float = 0.15       # Radio de los puntos de vértice.
RADIO_VERTICE_0D: float = 0.20    # Radio del punto para 0D.
RADIO_LEYENDA: float = 0.10       # Radio de puntos en la leyenda de colores.
FUENTE_TITULO: int = 36           # Tamaño de fuente para títulos.
FUENTE_VALOR: int = 18            # Tamaño de fuente para etiquetas de valor.
FUENTE_COORD: int = 16            # Tamaño de fuente para etiquetas de coord.
FUENTE_DIM_LEYENDA: int = 20      # Tamaño de fuente para leyenda de dimensión.
FUENTE_BARRA_ETIQUETA: int = 16   # Tamaño de fuente para etiquetas de barra.
FUENTE_BARRA_TITULO: int = 20     # Tamaño de fuente para título de barra.
ESCALA_3D_O_MENOS: float = 3.0    # Factor de escala para ≤ 3D.
ESCALA_4D_O_MAS: float = 2.5      # Factor de escala para ≥ 4D.
SEGMENTOS_BARRA: int = 10         # Número de segmentos en la barra de color.
ANCHO_BARRA: float = 3.0          # Ancho total de la barra de color.
ALTO_BARRA: float = 0.30          # Alto de la barra de color.

# Paleta de colores por eje dimensional
COLORES_EJES = [RED, GREEN, BLUE, YELLOW, PURPLE, TEAL, ORANGE, MAROON]


class NCubeVisualizer(Scene):
    """Visualizador 2D de N-Cubos de 0 a 4 dimensiones.

    Recorre secuencialmente representaciones de 0D (punto) a 4D
    (hipercubo), mostrando cada una con proyección isométrica o de
    cubos anidados, leyenda de dimensiones y barra de gradiente.
    """

    def construct(self) -> None:
        """Construye y anima la secuencia de hipercubos de 0D a 4D."""
        # 0D
        self.visualize_ncube(np.array(0.75))
        self.wait(1)
        self.clear()

        # 1D
        self.visualize_ncube(np.array([0.25, 0.75]))
        self.wait(1)
        self.clear()

        # 2D
        self.visualize_ncube(
            np.array([[0.2, 0.4], [0.6, 0.8]])
        )
        self.wait(1)
        self.clear()

        # 3D
        self.visualize_ncube(
            np.array([[[.5, .5], [1., 0.]], [[0., 1.], [1., 0.]]])
        )
        self.wait(1)
        self.clear()

        # 4D
        hypercube_data = np.zeros((2, 2, 2, 2))
        for indices in itertools.product([0, 1], repeat=4):
            hypercube_data[indices] = np.sum(indices) / 4
        self.visualize_ncube(hypercube_data)

    # ------------------------------------------------------------------
    # Métodos de proyección
    # ------------------------------------------------------------------

    def dim_to_letter(self, dim: int) -> str:
        """Convierte un índice de dimensión a su letra (0→A, 1→B, …).

        Args:
            dim: Índice entero de dimensión (0-based).

        Returns:
            Carácter mayúscula correspondiente al índice.
        """
        return chr(65 + dim)

    def project_isometric(self, coords: tuple) -> np.ndarray:
        """Proyección isométrica para coordenadas de hasta 3 dimensiones.

        Args:
            coords: Tupla de 0s y 1s con las coordenadas del vértice.

        Returns:
            Array NumPy ``(3,)`` con la posición proyectada.
        """
        n = len(coords)
        if n == 0:
            return np.array([0.0, 0.0, 0.0])
        if n == 1:
            return np.array([float(coords[0]), 0.0, 0.0])
        if n == 2:
            return np.array([float(coords[0]), float(coords[1]), 0.0])
        x, y, z = coords[0], coords[1], coords[2]
        return np.array([x - 0.5 * y, 0.5 * x + y + z, 0.0])

    def project_nested_cube(
        self,
        coords: tuple,
        scale_factor: float = 0.7,
    ) -> np.ndarray:
        """Proyección de cubos anidados para dimensiones > 3.

        Las primeras tres coordenadas determinan la posición base
        isométrica. Las dimensiones adicionales añaden desplazamientos
        sucesivos con magnitud decreciente.

        Args:
            coords: Tupla de 0s y 1s de longitud ``n_dims``.
            scale_factor: Factor de escala para los desplazamientos de
                dimensiones extra.

        Returns:
            Array NumPy ``(3,)`` con la posición proyectada.
        """
        n = len(coords)
        if n <= 3:
            return self.project_isometric(coords)

        base = self.project_isometric(coords[:3])
        direction = np.zeros(3)
        for i in range(3, n):
            if coords[i] == 1:
                displacement = scale_factor ** (i - 2)
                axis_idx = (i - 3) % 3
                delta = np.zeros(3)
                delta[axis_idx] = displacement
                direction = direction + delta

        return base + direction * scale_factor

    # ------------------------------------------------------------------
    # Método principal de visualización
    # ------------------------------------------------------------------

    def visualize_ncube(self, data: np.ndarray) -> None:
        """Visualiza un N-cubo con valores en los vértices.

        Detecta la dimensión del array, proyecta los vértices, dibuja
        aristas coloreadas por eje, muestra etiquetas de valor y coordenada,
        añade leyenda de dimensiones y barra de gradiente, y aplica
        rotación para dimensiones ≥ 3.

        Args:
            data: Array NumPy de forma ``(2, 2, ..., 2)`` o escalar (0D).
        """
        if np.isscalar(data):
            n_dims = 0
        else:
            n_dims = data.ndim

        title = Text(
            f"Visualización de {n_dims}-Cubo", font_size=FUENTE_TITULO
        )
        self.play(Write(title))
        self.play(title.animate.to_edge(UP))

        # Caso 0D
        if n_dims == 0:
            value = float(data)
            point = Dot(
                point=np.array([0.0, 0.0, 0.0]),
                radius=RADIO_VERTICE_0D,
                color=self.value_to_color(value),
            )
            label = Text(
                f"{value:.2f}", font_size=FUENTE_TITULO - 12
            ).next_to(point, UP)
            self.play(Create(point), Write(label))
            return

        # Coordenadas de vértices
        if n_dims == 1:
            vertex_coords = [(0,), (1,)]
        else:
            vertex_coords = list(
                itertools.product([0, 1], repeat=n_dims)
            )

        # Calcular posiciones
        vertex_positions: dict[tuple, np.ndarray] = {}
        scale = ESCALA_3D_O_MENOS if n_dims <= 3 else ESCALA_4D_O_MAS
        for coords in vertex_coords:
            if n_dims <= 3:
                pos = self.project_isometric(coords)
            else:
                pos = self.project_nested_cube(coords)
            vertex_positions[coords] = pos * scale

        # Vértices y etiquetas
        vertices = VGroup()
        value_labels = VGroup()
        coord_labels = VGroup()

        for coords in vertex_coords:
            position = vertex_positions[coords]
            try:
                value = float(
                    data[coords[0]] if n_dims == 1 else data[coords]
                )
            except (IndexError, TypeError):
                value = 0.0

            vertex = Dot(
                point=position,
                radius=RADIO_VERTICE,
                color=self.value_to_color(value),
            )
            vertices.add(vertex)

            value_label = Text(
                f"{value:.2f}", font_size=FUENTE_VALOR
            ).move_to(position + UP * 0.25)
            value_labels.add(value_label)

            if n_dims > 1:
                coord_text = "".join(
                    self.dim_to_letter(i)
                    for i, v in enumerate(coords)
                    if v == 1
                ) or "O"
                coord_label = Text(
                    coord_text, font_size=FUENTE_COORD
                ).move_to(position + DOWN * 0.25)
                coord_labels.add(coord_label)

        # Aristas
        edges = VGroup()
        if n_dims == 1:
            edge = Line(
                vertex_positions[(0,)],
                vertex_positions[(1,)],
                color=WHITE,
            )
            edges.add(edge)
        else:
            for i, c1 in enumerate(vertex_coords):
                for c2 in vertex_coords[i + 1:]:
                    if sum(a != b for a, b in zip(c1, c2)) != 1:
                        continue
                    dim_changed = next(
                        idx
                        for idx, (a, b) in enumerate(zip(c1, c2))
                        if a != b
                    )
                    edge = Line(
                        vertex_positions[c1],
                        vertex_positions[c2],
                        color=COLORES_EJES[dim_changed % len(COLORES_EJES)],
                        stroke_opacity=0.8,
                    )
                    edges.add(edge)

        # Leyenda de dimensiones
        dim_labels = VGroup()
        if n_dims > 1:
            for d in range(n_dims):
                color = COLORES_EJES[d % len(COLORES_EJES)]
                dim_label = Text(
                    f"Dim {self.dim_to_letter(d)}",
                    font_size=FUENTE_DIM_LEYENDA,
                    color=color,
                ).to_edge(LEFT).shift(UP * (2.0 - d * 0.4))
                dim_labels.add(dim_label)

        cube_group = VGroup(edges, vertices, value_labels, coord_labels)

        self.play(Create(edges), run_time=1.5)
        self.play(Create(vertices), run_time=1)
        self.play(
            Write(value_labels), Write(coord_labels), run_time=1.5
        )
        if n_dims > 1:
            self.play(Write(dim_labels), run_time=1)

        color_legend = self.create_color_legend()
        self.play(FadeIn(color_legend))

        if n_dims >= 3:
            self.play(
                Rotate(
                    cube_group, angle=np.pi / 6,
                    axis=RIGHT, about_point=np.array([0.0, 0.0, 0.0])
                ),
                run_time=2,
            )
            self.play(
                Rotate(
                    cube_group, angle=np.pi / 4,
                    axis=UP, about_point=np.array([0.0, 0.0, 0.0])
                ),
                run_time=2,
            )
            self.play(
                Rotate(
                    cube_group,
                    angle=-np.pi / 8,
                    axis=RIGHT + UP,
                    about_point=np.array([0.0, 0.0, 0.0]),
                ),
                run_time=2,
            )

        self.wait(1)

    # ------------------------------------------------------------------
    # Leyenda de colores
    # ------------------------------------------------------------------

    def create_color_legend(self) -> VGroup:
        """Crea una barra de gradiente como leyenda de la escala de colores.

        Returns:
            ``VGroup`` con la barra de gradiente, sus etiquetas de
            valor mínimo/máximo y un título, posicionado en la esquina
            inferior derecha.
        """
        gradient_group = VGroup()
        seg_w = ANCHO_BARRA / SEGMENTOS_BARRA

        for i in range(SEGMENTOS_BARRA):
            t = i / (SEGMENTOS_BARRA - 1)
            segment = Rectangle(
                height=ALTO_BARRA,
                width=seg_w,
                fill_color=self.value_to_color(t),
                fill_opacity=1,
                stroke_width=0,
            ).shift(RIGHT * seg_w * (i - SEGMENTOS_BARRA / 2 + 0.5))
            gradient_group.add(segment)

        border = Rectangle(
            height=ALTO_BARRA,
            width=ANCHO_BARRA,
            stroke_color=WHITE,
            stroke_width=1,
            fill_opacity=0,
        )
        gradient_group.add(border)

        min_label = Text(
            "0.0", font_size=FUENTE_BARRA_ETIQUETA
        ).next_to(gradient_group, LEFT)
        max_label = Text(
            "1.0", font_size=FUENTE_BARRA_ETIQUETA
        ).next_to(gradient_group, RIGHT)
        bar_title = Text(
            "Valor", font_size=FUENTE_BARRA_TITULO
        ).next_to(gradient_group, UP)

        legend = VGroup(gradient_group, min_label, max_label, bar_title)
        legend.to_corner(DR)
        return legend

    def value_to_color(self, value: float):
        """Convierte un valor entre 0 y 1 a un color en escala azul-rojo.

        Args:
            value: Valor escalar; se fuerza al rango ``[0, 1]``.

        Returns:
            Color de Manim resultante de la interpolación.
        """
        value = min(max(float(value), 0.0), 1.0)
        return interpolate_color(BLUE, RED, value)


# ---------------------------------------------------------------------------
# Escena para hipercubo 5D
# ---------------------------------------------------------------------------

class Hypercube5D(NCubeVisualizer):
    """Visualización de un hipercubo de 5 dimensiones.

    Genera un hipercubo ``(2,)^5`` cuyos valores son la suma normalizada
    de sus índices y lo visualiza con ``visualize_ncube``.
    """

    def construct(self) -> None:
        """Construye la visualización del hipercubo 5D."""
        hypercube_data = np.zeros((2, 2, 2, 2, 2))
        for indices in itertools.product([0, 1], repeat=5):
            hypercube_data[indices] = np.sum(indices) / 5
        self.visualize_ncube(hypercube_data)


# ---------------------------------------------------------------------------
# Instrucciones de ejecución
# ---------------------------------------------------------------------------
# manim -pql hyper-v5.py NCubeVisualizer   # 0D a 4D
# manim -pql hyper-v5.py Hypercube5D       # 5D
