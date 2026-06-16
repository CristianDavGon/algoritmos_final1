"""
Solution: Resultado de bipartición con visualización y voz para QNodes.

Módulo del modelo de dominio QNodes. Define ``Solution``, que encapsula el
resultado de un análisis de bipartición (valor φ, distribuciones, partición
óptima) y proporciona salida visual colorizada en terminal (colorama) y
anuncio por voz (pyttsx3) de forma opcional y no bloqueante.

Typical usage example::

    import numpy as np
    from src.models.core.solution import Solution

    solucion = Solution(
        estrategia="QNodes",
        perdida=0.1234,
        distribucion_subsistema=np.array([0.5, 0.5]),
        distribucion_particion=np.array([0.6, 0.4]),
        particion="⎛A⎞⎛B⎞\\n⎝a⎠⎝∅⎠",
        tiempo_total=2.5,
        quiere_hablar=False,
    )
    print(solucion)
"""

from __future__ import annotations

from threading import Thread

import numpy as np
from colorama import Fore, Style, init
from pyttsx3.engine import Engine
from pyttsx3.voice import Voice
import pyttsx3

from src.constants.base import FLOAT_ZERO, INT_ZERO, WHITESPACE
from src.constants.models import PYPHI_LABEL
from src.models.base.application import aplicacion

# Iniciar colorama
init()

VELOCIDAD_HABLA: int = 150
VOLUMEN_HABLA: float = 0.9
ANCHO_DISPLAY: int = 64
SEGUNDOS_HORA: int = 3600
SEGUNDOS_MINUTO: int = 60


class Solution:
    """Resultado de bipartición con visualización colorizada y síntesis de voz.

    Encapsula el valor φ (perdida), las distribuciones del subsistema y de
    la bipartición encontrada, junto con la representación textual de la
    partición óptima. Al imprimir (``__str__``), genera una salida
    colorizada en terminal mediante colorama y puede anunciar el resultado
    mediante pyttsx3 en un hilo separado.

    Attributes:
        estrategia (str): Nombre de la estrategia utilizada (p. ej.
            ``"QNodes"``).
        perdida (float): Valor φ (small phi) que cuantifica la pérdida de
            información integrada en la bipartición óptima.
        distribucion_subsistema (np.ndarray): Distribución del subsistema
            original (tensorial para PyPhi, marginal para QNodes).
        distribucion_particion (np.ndarray): Distribución de la bipartición
            óptima.
        particion (str): Representación textual de la mejor bipartición
            (literales alfanuméricos en numerador/denominador).
        tiempo_ejecucion (float): Tiempo total del algoritmo en segundos.
        id_voz (str | None): Identificador de voz pyttsx3 seleccionada.
        hablar (bool): Si es ``True``, anuncia la solución por síntesis de
            voz al imprimir.

    Example::

        solucion = Solution(
            estrategia="QNodes",
            perdida=0.25,
            distribucion_subsistema=np.array([0.0, 1.0]),
            distribucion_particion=np.array([0.25, 0.75]),
            particion="⎛A⎞⎛B⎞\\n⎝a⎠⎝∅⎠",
            quiere_hablar=False,
        )
        print(solucion)
    """

    def __init__(
        self,
        estrategia: str,
        perdida: float,
        distribucion_subsistema: np.ndarray,
        distribucion_particion: np.ndarray,
        particion: str,
        tiempo_total: float = FLOAT_ZERO,
        quiere_hablar: bool = True,
        voz: str | None = None,
    ) -> None:
        """Inicializa la solución con los resultados del análisis de bipartición.

        Args:
            estrategia (str): Nombre de la estrategia de resolución usada.
            perdida (float): Valor φ de pérdida de información integrada.
            distribucion_subsistema (np.ndarray): Distribución del
                subsistema (tensorial o marginal según estrategia).
            distribucion_particion (np.ndarray): Distribución de la
                bipartición óptima.
            particion (str): Representación textual de la mejor bipartición.
            tiempo_total (float): Tiempo de ejecución del algoritmo en
                segundos. Por defecto ``0.0``.
            quiere_hablar (bool): Si ``True``, anuncia la solución por voz
                al imprimir. Por defecto ``True``.
            voz (str | None): Identificador de voz pyttsx3. Si es ``None``,
                se busca automáticamente una voz en español.
        """
        self.estrategia = estrategia
        self.perdida = perdida
        self.distribucion_subsistema = distribucion_subsistema
        self.distribucion_particion = distribucion_particion
        self.particion = particion
        self.tiempo_ejecucion = tiempo_total
        self.id_voz = voz
        self.hablar = quiere_hablar

    def __obtener_voz_espanol(self, motor: Engine) -> str | None:
        """Busca la mejor voz disponible en español en el sistema.

        Aplica un sistema de prioridades para seleccionar la voz más
        adecuada entre las disponibles en pyttsx3.

        Args:
            motor (Engine): Instancia del motor de síntesis de voz pyttsx3.

        Returns:
            str | None: Identificador de la voz seleccionada, o ``None`` si
                no hay voces disponibles.
        """
        voces: list[Voice] = motor.getProperty("voices")

        prioridades = [
            ("sabina", "méxico"),
            ("helena", "españa"),
            ("spanish", None),
            ("español", None),
            ("es-", None),
        ]

        for nombre_buscado, region in prioridades:
            for voz in voces:
                nombre_voz = voz.name.lower()
                id_voz = voz.id.lower()

                if nombre_buscado in nombre_voz or nombre_buscado in id_voz:
                    if region is None or region in nombre_voz:
                        return voz.id

        return voces[INT_ZERO].id if voces else None

    def __anunciar_solucion(self) -> None:
        """Anuncia la solución por síntesis de voz en español.

        Configura pyttsx3 con velocidad ``VELOCIDAD_HABLA`` y volumen
        ``VOLUMEN_HABLA``, luego anuncia el nombre de la estrategia y el
        valor φ. Se ejecuta en un hilo separado (no bloqueante). Las
        excepciones se silencian para no interrumpir la ejecución principal.

        Notes:
            Usa ``except Exception`` intencionalmente para no interrumpir
            el flujo principal si el motor TTS falla (dispositivo sin audio,
            drivers ausentes, etc.).
        """
        try:
            motor = pyttsx3.init()

            id_voz = self.id_voz or self.__obtener_voz_espanol(motor)
            if id_voz:
                motor.setProperty("voice", id_voz)

            motor.setProperty("rate", VELOCIDAD_HABLA)
            motor.setProperty("volume", VOLUMEN_HABLA)

            mensaje = f"Solución encontrada con {self.estrategia}." + (
                f"El valor de fi es de {self.perdida:.2f}"
                if self.perdida > FLOAT_ZERO
                else "No hubo pérdida."
            )
            motor.say(mensaje)
            motor.runAndWait()
        except Exception as e:
            print(f"Error al inicializar el motor de voz: {e}")

    def __str__(self) -> str:
        """Genera representación colorizada de la solución para terminal.

        Si ``self.hablar`` es ``True``, lanza un hilo para el anuncio por
        voz de forma no bloqueante.

        Returns:
            str: Representación visual con valor φ, distribuciones,
                partición óptima y tiempos de ejecución.
        """
        bilinea = "═" * ANCHO_DISPLAY
        trilinea = "≡" * ANCHO_DISPLAY

        def formatear_distribucion(
            distribucion: np.ndarray,
            evitar_desbordamiento: bool = True,
        ) -> str:
            rango = distribucion.size
            mensaje_desborde = ""
            if evitar_desbordamiento:
                excedente = rango - ANCHO_DISPLAY
                if excedente > FLOAT_ZERO:
                    mensaje_desborde = f" {excedente} valores más.."
                    rango = ANCHO_DISPLAY

            datos = WHITESPACE.join(
                f"{Fore.WHITE}{distribucion[idx]:.4f}"
                if distribucion[idx] > FLOAT_ZERO
                else f"{Fore.LIGHTBLACK_EX}0.    "
                for idx in range(rango)
            )
            return f"[ {datos}{mensaje_desborde} {Fore.WHITE}]"

        if self.hablar:
            voz = Thread(target=self.__anunciar_solucion)
            voz.start()

        es_pyphi = self.estrategia == PYPHI_LABEL
        tipo_distribucion = "tensorial" if es_pyphi else "marginal"

        tiempo_hrs = f"{self.tiempo_ejecucion / SEGUNDOS_HORA:.2f}"
        tiempo_min = f"{self.tiempo_ejecucion / SEGUNDOS_MINUTO:.1f}"
        tiempo_seg = f"{self.tiempo_ejecucion:.4f}"

        return f"""{Fore.CYAN}{bilinea}

{Fore.RED}{self.estrategia} fue la estrategia de solucion.

{Fore.BLUE}Distancia métrica utilizada:
{Fore.WHITE}{aplicacion.distancia_metrica}
{Fore.BLUE}Notación utilizada en indexación:
{Fore.WHITE}{aplicacion.notacion_indexado}

{Fore.YELLOW}Distribucion {tipo_distribucion} del Subsistema:
{Style.RESET_ALL}{formatear_distribucion(self.distribucion_subsistema)}
{Fore.YELLOW}Distribucion {tipo_distribucion} de la Partición:
{Style.RESET_ALL}{formatear_distribucion(self.distribucion_particion)}

{Fore.YELLOW}Mejor Bi-Partición:
{Fore.MAGENTA}{self.particion}
{Fore.GREEN}Perdida mínima ( φ ) = {self.perdida:.4f}

{Fore.BLUE}Tiempos de ejecución:
{Fore.WHITE}Horas: {tiempo_hrs} = Minutos: {tiempo_min} = Segundos: {tiempo_seg}

{Fore.CYAN}{trilinea}{Style.RESET_ALL}"""

    def __repr__(self) -> str:
        """Delegación a ``__str__`` para consistencia en repr e impresión."""
        return self.__str__()
