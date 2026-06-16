"""Constantes globales del módulo QNodes.

Define valores numéricos, cadenas de texto, rutas de sistema y
símbolos matemáticos reutilizados en todo el proyecto K-QGMIP
(componente Q-Nodes).

Typical usage example::

    from src.constants.base import FLOAT_ZERO, COLS_IDX, PATH_SAMPLES

    acumulador: float = FLOAT_ZERO
    columna_efecto: int = COLS_IDX
    ruta = PATH_SAMPLES + "mi_red.csv"
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Infinitos
# ---------------------------------------------------------------------------
INFTY_POS: float = float("inf")   # Infinito positivo
INFTY_NEG: float = float("-inf")  # Infinito negativo

# ---------------------------------------------------------------------------
# Enteros base
# ---------------------------------------------------------------------------
INT_ZERO: int = int(0)
INT_ONE: int = int(1)

# ---------------------------------------------------------------------------
# Flotantes base
# ---------------------------------------------------------------------------
FLOAT_ONE: float = float(INT_ONE)
FLOAT_ZERO: float = float(INT_ZERO)

# ---------------------------------------------------------------------------
# Aritmética auxiliar
# ---------------------------------------------------------------------------
BASE_TWO: int = INT_ONE + INT_ONE  # Base binaria (2)

# ---------------------------------------------------------------------------
# Índices y longitudes
# ---------------------------------------------------------------------------
ABC_LEN: int = 26          # Número de letras en el alfabeto latino
LAST_IDX = -INT_ONE        # Índice del último elemento (acceso negativo)

# ROWS_IDX / ACTUAL → dimensión 0 (filas / estado actual)
# COLS_IDX / EFFECT  → dimensión 1 (columnas / estado efecto)
ROWS_IDX = ACTUAL = INT_ZERO
COLS_IDX = EFFECT = INT_ONE

# ---------------------------------------------------------------------------
# Cadenas numéricas
# ---------------------------------------------------------------------------
STR_ZERO: str = str(INT_ZERO)
STR_ONE: str = str(INT_ONE)

# ---------------------------------------------------------------------------
# Cadenas de texto y delimitadores
# ---------------------------------------------------------------------------
EMPTY_STR: str = ""         # Cadena vacía
WHITESPACE: str = " "       # Espacio en blanco simple
COLON_DELIM: str = ","      # Delimitador CSV estándar
VOID_STR: str = "∅"         # Símbolo de conjunto vacío
SMALL_PHI_STR: str = "φ"    # Letra phi minúscula (Φ integrado)
ABC_START: str = "A"        # Primera letra del alfabeto (etiquetado)

# ---------------------------------------------------------------------------
# Símbolos matemáticos
# ---------------------------------------------------------------------------
EQUIV_SYM: str = "≡"   # Equivalencia lógica
EQUAL_SYM: str = "="   # Igualdad
DASH_SYM: str = "—"    # Guión largo (em dash)
MINUS_SYM: str = "–"   # Guión medio (en dash)
LINE_SYM: str = "-"    # Guión corto (hyphen)

# Símbolos de (des)igualdad extendida para reportes de partición
EQUITIES = "≌", "≆", "≇", "≄", "≒"
NEQ_SYM: str = "≠"  # No igual

# ---------------------------------------------------------------------------
# Bits y estados lógicos
# ---------------------------------------------------------------------------
BITS: tuple[int, int] = (INT_ZERO, INT_ONE)  # Valores posibles de un bit
ACTIVE, INACTIVE = True, False                # Alias booleanos de estado

# ---------------------------------------------------------------------------
# Etiquetas de red
# ---------------------------------------------------------------------------
NET_LABEL: str = "NET"  # Prefijo genérico para identificar redes

# ---------------------------------------------------------------------------
# Rutas del sistema de archivos
# ---------------------------------------------------------------------------
PATH_LOGS: str = ".logs"                   # Directorio raíz de logs
PATH_SAMPLES: str = "src/.samples/"       # Muestras de redes de prueba
PATH_PROFILING: str = "review/profiling"  # Salida de perfiles pyinstrument
PATH_RESOLVER: str = "review/resolver"    # Salida de resultados del resolver

# ---------------------------------------------------------------------------
# Extensiones de archivo
# ---------------------------------------------------------------------------
CSV_EXTENSION: str = "csv"
HTML_EXTENSION: str = "html"
EXCEL_EXTENSION: str = "xlsx"

# ---------------------------------------------------------------------------
# Etiquetas de metadatos
# ---------------------------------------------------------------------------
TYPE_TAG = "type"  # Clave usada en dicts de configuración para indicar tipo
