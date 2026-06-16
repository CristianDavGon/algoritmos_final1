"""
System: Colección de NCubes con operaciones de subsistema para IIT 4.0 (GeoMIP).

Módulo del modelo de dominio GeoMIP. Define ``System``, que agrupa los
``NCube`` de todos los nodos de la TPM y expone las operaciones centrales
del framework IIT 4.0: ``condicionar`` (condiciones de fondo), ``substraer``
(generación de subsistemas) y ``bipartir`` (bipartición para cálculo de φ).
La distribución marginal resultante alimenta directamente el cálculo de
EMD-Effect.

Typical usage example::

    import numpy as np
    from src.models.core.system import System

    tpm = np.load("ruta/a/tpm.npy")
    estado = np.array([1, 0, 0, 0, 0, 0, 0, 0], dtype=np.int8)
    sistema = System(tpm, estado)
    subsistema = sistema.condicionar(np.array([2, 3])).substraer(
        np.array([0, 1]), np.array([0, 1])
    )
"""

from __future__ import annotations

from functools import cached_property

import numpy as np
from numpy.typing import NDArray

from src.constants.base import COLS_IDX
from src.funcs.base import reindexar, seleccionar_subestado
from src.models.base.application import aplicacion
from src.models.core.ncube import NCube
from src.models.enums.notation import Notation


class System:
    """Colección de NCubes que representa el sistema completo en IIT 4.0.

    Gestiona los NCubes de todos los nodos derivados de la TPM y permite
    aplicar condicionamiento, substracción y bipartición para el análisis de
    irreductibilidad del sistema (SIA). Las instancias intermedias se crean
    con ``System.__new__`` para evitar re-inicialización costosa.

    Attributes:
        estado_inicial (np.ndarray): Estado binario del sistema con shape
            ``(n_nodos,)``.
        ncubos (tuple[NCube, ...]): Tupla inmutable de NCubes activos. Cada
            NCube es ``frozen=True``; no mutar sus atributos directamente.
        memo (dict): Caché de biparticiones previas (clave: par de tuplas
            alcance × mecanismo).

    Example::

        import numpy as np
        from src.models.core.system import System

        tpm = np.random.rand(8, 3)
        estado = np.array([1, 0, 0], dtype=np.int8)
        sistema = System(tpm, estado)
        subsistema = sistema.condicionar(np.array([2], dtype=np.int8))
        particion = subsistema.bipartir(
            np.array([0], dtype=np.int8),
            np.array([0, 1], dtype=np.int8),
        )
    """

    def __init__(
        self,
        tpm: np.ndarray,
        estado_inicio: np.ndarray,
        notacion: str = aplicacion.notacion,
    ) -> None:
        """Construye el sistema a partir de la TPM y el estado inicial.

        Crea un ``NCube`` por cada nodo (columna de la TPM), reshapeando
        la columna en un hipercubo de dimensiones ``(2,) * n_nodos`` según
        la notación indicada.

        Args:
            tpm (np.ndarray): Matriz de Probabilidad de Transición con shape
                ``(2**n_nodos, n_nodos)`` en notación little-endian.
            estado_inicio (np.ndarray): Estado inicial binario con shape
                ``(n_nodos,)``.
            notacion (str): Notación de indexación de la TPM. Por defecto
                ``Notation.LIL_ENDIAN``.

        Raises:
            ValueError: Si ``estado_inicio.size`` no coincide con el número
                de columnas de ``tpm``.
        """
        if estado_inicio.size != (n_nodes := tpm.shape[COLS_IDX]):
            raise ValueError(f"Estado inicial debe tener longitud {n_nodes}")
        self.estado_inicial = estado_inicio
        self.ncubos = tuple(
            NCube(
                indice=i,
                dims=np.array(range(n_nodes), dtype=np.int8),
                data=tpm[:, i].reshape((2,) * n_nodes)
                if notacion == Notation.LIL_ENDIAN.value
                else tpm[:, i][reindexar(tpm[COLS_IDX])].reshape(
                    (2,) * n_nodes
                ),
            )
            for i in range(n_nodes)
        )
        self.memo = {}

    @cached_property
    def indices_ncubos(self) -> NDArray[np.int8]:
        """Índices de los NCubes activos en el sistema actual.

        Computed property (cached) que retorna el arreglo de índices de
        los NCubes remanentes tras condicionamiento, substracción o
        bipartición.

        Returns:
            NDArray[np.int8]: Arreglo con los índices de los NCubes activos.
        """
        return np.array([cube.indice for cube in self.ncubos], dtype=np.int8)

    @property
    def dims_ncubos(self) -> NDArray[np.int8]:
        """Dimensiones activas del primer NCube del sistema.

        No aplicable tras bipartición porque los NCubes pueden tener
        dimensiones heterogéneas.

        Returns:
            NDArray[np.int8]: Dimensiones del primer NCube, o arreglo vacío
                si no hay NCubes.
        """
        return self.ncubos[0].dims if len(self.ncubos) > 0 else np.array([])

    def condicionar(self, indices: NDArray[np.int8]) -> System:
        """Aplica condiciones de fondo al sistema descartando nodos condicionados.

        Intersecta ``indices`` con los índices actuales de los NCubes para
        evitar referencias inexistentes. Los NCubes cuyos índices coincidan
        con la intersección se eliminan del sistema; los restantes son
        condicionados en esas dimensiones según ``estado_inicial``.

        Args:
            indices (NDArray[np.int8]): Índices de los nodos a condicionar.

        Returns:
            System: Sistema candidato con NCubes condicionados. Los NCubes
                retornados son nuevas instancias (``frozen=True``; no mutar).

        Example::

            sistema_cand = sistema.condicionar(np.array([2, 3], dtype=np.int8))
        """
        indices_validos = np.intersect1d(self.indices_ncubos, indices)
        if not indices_validos.size:
            return self
        nuevo_sis = System.__new__(System)
        nuevo_sis.estado_inicial = self.estado_inicial
        nuevo_sis.memo = {}
        nuevo_sis.ncubos = tuple(
            cube.condicionar(indices_validos, self.estado_inicial)
            for cube in self.ncubos
            if cube.indice not in indices_validos
        )
        return nuevo_sis

    def substraer(
        self,
        alcance_dims: NDArray[np.int8],
        mecanismo_dims: NDArray[np.int8],
    ) -> System:
        """Genera un subsistema eliminando nodos del alcance y marginalizando.

        Descarta los NCubes cuyos índices están en ``alcance_dims`` (futuro
        excluido) y marginaliza los restantes sobre ``mecanismo_dims``
        (presente excluido), produciendo el subsistema para bipartición.

        Args:
            alcance_dims (NDArray[np.int8]): Índices de nodos del alcance a
                excluir del subsistema (eliminados del futuro/t+1).
            mecanismo_dims (NDArray[np.int8]): Dimensiones del mecanismo a
                marginalizar en los NCubes restantes (eliminadas del
                presente/t).

        Returns:
            System: Subsistema listo para bipartición. Los NCubes retornados
                son nuevas instancias inmutables.

        Example::

            subsistema = sistema.substraer(
                np.array([0], dtype=np.int8),
                np.array([2], dtype=np.int8),
            )
        """
        valid_futures = np.setdiff1d(self.indices_ncubos, alcance_dims)
        new_sys = System.__new__(System)
        new_sys.estado_inicial = self.estado_inicial
        new_sys.memo = {}
        new_sys.ncubos = tuple(
            cube.marginalizar(mecanismo_dims)
            for cube in self.ncubos
            if cube.indice in valid_futures
        )
        return new_sys

    def bipartir(
        self,
        alcance: NDArray[np.int8],
        mecanismo: NDArray[np.int8],
    ) -> System:
        """Genera una bipartición del subsistema para el cálculo de φ.

        Para cada NCube: si su índice está en ``alcance``, marginaliza las
        dimensiones fuera de ``mecanismo`` (desconecta el futuro del
        mecanismo excluido); en caso contrario, marginaliza sobre
        ``mecanismo`` (desconecta el presente). Usa caché interna para
        evitar recomputar la misma bipartición.

        Args:
            alcance (NDArray[np.int8]): Índices de nodos incluidos en el
                alcance de la bipartición.
            mecanismo (NDArray[np.int8]): Dimensiones del mecanismo de la
                bipartición.

        Returns:
            System: Bipartición del subsistema. La pérdida φ se obtiene
                comparando su distribución marginal con la del subsistema
                original mediante EMD-Effect.

        Example::

            biparticion = subsistema.bipartir(
                np.array([0], dtype=np.int8),
                np.array([0, 1], dtype=np.int8),
            )
            perdida = emd_efecto(subsistema, biparticion)
        """
        new_sys = System.__new__(System)
        new_sys.estado_inicial = self.estado_inicial
        new_sys.memo = self.memo

        clave = tuple(alcance), tuple(mecanismo)
        if clave not in self.memo:
            self.memo[clave] = tuple(
                cube.marginalizar(np.setdiff1d(cube.dims, mecanismo))
                if cube.indice in alcance
                else cube.marginalizar(mecanismo)
                for cube in self.ncubos
            )

        new_sys.ncubos = self.memo[clave]
        return new_sys

    def distribucion_marginal(self) -> NDArray[np.float32]:
        """Calcula la distribución marginal del sistema para EMD-Effect.

        Para cada NCube activo, selecciona la probabilidad de transición
        al estado OFF (complemento: ``1 - p``) indexada por el estado
        inicial actual. Esta representación es la requerida por
        ``emd_efecto`` en GeoMIP para medir la pérdida φ.

        Returns:
            NDArray[np.float32]: Arreglo de tamaño ``n_ncubos`` con la
                probabilidad marginal de estado OFF por cada nodo.
        """
        distribuciones = np.empty(self.indices_ncubos.size, dtype=np.float32)

        for i, ncubo in enumerate(self.ncubos):
            probabilidad = ncubo.data
            if ncubo.dims.size:
                sub_estado_inicial = tuple(
                    self.estado_inicial[j] for j in ncubo.dims
                )
                probabilidad = ncubo.data[
                    seleccionar_subestado(sub_estado_inicial)
                ]
            distribuciones[i] = 1 - probabilidad
        return distribuciones

    def __str__(self) -> str:
        """Representación legible con índices, dims, estado inicial y NCubes."""
        sub_dims = self.dims_ncubos
        cubes_info = [f"{c}" for c in self.ncubos]
        return (
            f"\nSystem(indices={self.indices_ncubos}, dims={sub_dims})"
            f"\nInitial state: {self.estado_inicial}"
            f"\nNCubes:\n" + "\n".join(cubes_info)
        )
