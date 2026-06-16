"""
NCube: Hipercubo n-dimensional inmutable para operaciones IIT 4.0 en QNodes.

Módulo central del modelo de dominio QNodes. Define ``NCube``, un dataclass
``frozen=True`` que representa la distribución de probabilidad de transición
de un nodo del sistema organizada como hipercubo binario n-dimensional.
Toda transformación (condicionamiento, marginalización) produce una nueva
instancia; nunca se mutan los atributos del NCube original.

Typical usage example::

    import numpy as np
    from src.models.core.ncube import NCube

    data = np.ones((2, 2, 2)) * 0.5
    cubo = NCube(
        indice=0,
        dims=np.array([0, 1, 2], dtype=np.int8),
        data=data,
    )
    cubo_cond = cubo.condicionar(
        np.array([2], dtype=np.int8),
        np.array([1, 0, 0], dtype=np.int8),
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class NCube:
    """Hipercubo n-dimensional inmutable que representa un nodo en IIT 4.0.

    Cada instancia corresponde a un nodo del sistema cuya distribución de
    probabilidad de transición está organizada como un hipercubo binario de
    ``n`` dimensiones (una por nodo activo). Al ser ``frozen=True``, los
    atributos no pueden reasignarse; cualquier transformación retorna una
    nueva instancia. El diccionario ``memo`` es mutable por diseño (caché
    lazy) aunque la referencia al dict es inmutable.

    Attributes:
        indice (int): Índice del nodo en el sistema (0=A, 1=B, 2=C, …).
        dims (NDArray[np.int8]): Dimensiones activas del hipercubo. Se
            reduce al condicionar o marginalizar.
        data (np.ndarray): Datos del hipercubo con shape ``(2,)*len(dims)``
            en notación little-endian.
        memo (dict[int, NCube]): Caché de marginalizaciones indexado por
            máscara de bits canónica (intersección ejes ∩ dims activas).
            Compartible entre instancias sin riesgo dado que NCube es
            inmutable.

    Example::

        import numpy as np
        from src.models.core.ncube import NCube

        data = np.array([[[0.1, 0.9], [0.3, 0.7]],
                         [[0.5, 0.5], [0.8, 0.2]]])
        cubo = NCube(
            indice=0,
            dims=np.array([0, 1, 2], dtype=np.int8),
            data=data,
        )
        cubo_marginalizado = cubo.marginalizar(np.array([1], dtype=np.int8))
    """

    indice: int
    dims: NDArray[np.int8]
    data: np.ndarray
    memo: dict[int, NCube] = field(
        default_factory=dict, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        """Valida forma del hipercubo y precalcula máscara de dimensiones.

        Verifica que ``data.shape`` sea ``(2,) * dims.size`` (hipercubo
        binario) y almacena la máscara de bits de las dimensiones activas
        para acelerar la memoización en ``marginalizar``.

        Raises:
            ValueError: Si ``data.shape`` no corresponde a
                ``(2,) * dims.size`` cuando ``dims`` no está vacío.
        """
        if self.dims.size and self.data.shape != (2,) * self.dims.size:
            raise ValueError(
                f"Forma inválida {self.data.shape} "
                f"para dimensiones {self.dims}"
            )
        mascara = 0
        for dim in self.dims:
            mascara |= 1 << int(dim)
        object.__setattr__(self, "_mascara_dims", mascara)

    def condicionar(
        self,
        indices_condicionados: NDArray[np.int8],
        estado_inicial: NDArray[np.int8],
    ) -> NCube:
        """Aplica condiciones de fondo seleccionando caras fijas del hipercubo.

        Para cada dimensión en ``indices_condicionados``, fija la cara
        correspondiente al valor en ``estado_inicial``. La dimensión más
        externa es la más significativa (selección de afuera hacia adentro).
        No muta el NCube; retorna una nueva instancia con dimensiones
        condicionadas eliminadas de ``dims``.

        Args:
            indices_condicionados (NDArray[np.int8]): Dimensiones globales
                sobre las cuales se aplica el condicionamiento de fondo.
            estado_inicial (NDArray[np.int8]): Estado binario del sistema;
                ``estado_inicial[j]`` fija el valor de la dimensión ``j``.

        Returns:
            NCube: Nueva instancia con ``dims`` y ``data`` reducidas. No
                mutar el NCube retornado; crear nueva instancia si se
                requieren cambios.

        Example::

            estado = np.array([1, 0, 0], dtype=np.int8)
            cubo_cond = mi_ncubo.condicionar(
                np.array([2], dtype=np.int8),
                estado,
            )
            # cubo_cond.dims == [0, 1]; cubo_cond.data.shape == (2, 2)
        """
        numero_dims = self.dims.size
        seleccion = [slice(None)] * numero_dims

        for condicion in indices_condicionados:
            level_arr = numero_dims - (condicion + 1)
            seleccion[level_arr] = estado_inicial[condicion]

        nuevas_dims = np.array(
            [dim for dim in self.dims if dim not in indices_condicionados],
            dtype=np.int8,
        )
        return NCube(
            data=self.data[tuple(seleccion)],
            indice=self.indice,
            dims=nuevas_dims,
        )

    def marginalizar(self, ejes: NDArray[np.int8]) -> NCube:
        """Marginaliza el hipercubo promediando sobre las dimensiones dadas.

        Colapsa las dimensiones en ``ejes`` calculando la media uniforme,
        preservando la probabilidad condicional marginal. Usa memoización
        por máscara de bits canónica (intersección ``ejes ∩ dims``) para
        evitar recálculos con los mismos ejes efectivos. No muta el NCube;
        retorna ``self`` si ningún eje intersecta con ``self.dims``.

        Args:
            ejes (NDArray[np.int8]): Dimensiones globales a marginalizar.
                Solo se procesan las que intersecten con ``self.dims``.

        Returns:
            NCube: Nueva instancia con dimensiones reducidas, o ``self`` si
                la intersección con ``self.dims`` es vacía. No mutar el
                NCube retornado.

        Example::

            cubo_marg = mi_ncubo.marginalizar(
                np.array([1, 2], dtype=np.int8)
            )
            # cubo_marg.dims == [0]; cubo_marg.data.shape == (2,)
        """
        mascara_ejes = 0
        for eje in ejes:
            mascara_ejes |= 1 << int(eje)
        # Clave canónica: solo la intersección efectiva con las dims activas,
        # así ejes equivalentes (orden u elementos ajenos) comparten entrada.
        interseccion = mascara_ejes & self._mascara_dims
        if not interseccion:
            return self
        memoizado = self.memo.get(interseccion)
        if memoizado is None:
            numero_dims = self.dims.size - 1
            ejes_locales = tuple(
                numero_dims - dim_idx
                for dim_idx, axis in enumerate(self.dims)
                if (interseccion >> int(axis)) & 1
            )
            new_dims = np.array(
                [d for d in self.dims if not (interseccion >> int(d)) & 1],
                dtype=np.int8,
            )
            memoizado = NCube(
                data=np.mean(self.data, axis=ejes_locales, keepdims=False),
                dims=new_dims,
                indice=self.indice,
            )
            self.memo[interseccion] = memoizado
        return memoizado

    def __str__(self) -> str:
        """Representación legible con índice, dims, shape y datos del NCube."""
        dims_str = f"dims={self.dims}"
        forma_str = f"shape={self.data.shape}"
        datos_str = str(self.data).replace("\n", "\n" + " " * 8)
        return (
            f"NCube(index={self.indice}):\n"
            f"    {dims_str}\n"
            f"    {forma_str}\n"
            f"    data=\n        {datos_str}"
        )
