"""Modelo de datos y algoritmo voraz para la asignación de salas.

Escenario 5 del proyecto final de Estructura de Datos y Análisis de Algoritmos
(CECAR). El problema consiste en asignar conferencias, cada una con hora de
inicio y de finalización, a salas de modo que no existan solapamientos y que se
utilice el menor número posible de salas.

El algoritmo implementado es la *partición de intervalos* (interval
partitioning):

1. Ordenar las conferencias por hora de inicio ascendente.
2. Recorrerlas en ese orden.
3. Reutilizar la sala que se libera más pronto (cola de prioridad).
4. Si ninguna sala está libre, crear una nueva.

Bajo estas condiciones el número de salas coincide con la cantidad máxima de
conferencias simultáneas, por lo que la solución es óptima.
"""

from __future__ import annotations

import heapq
import re
import time
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

MINUTOS_POR_DIA = 24 * 60
"""Minutos que tiene un día (1440)."""

_PATRON_HORA = re.compile(r"^(\d{1,2}):(\d{2})$")


class ErrorConferencia(ValueError):
    """Error de validación de los datos de una conferencia."""


def hhmm_a_minutos(texto: str) -> int:
    """Convierte una hora ``HH:MM`` en minutos transcurridos desde la medianoche.

    Se aceptan horas con uno o dos dígitos (``8:05`` y ``08:05``). La hora
    ``24:00`` se admite únicamente como fin de una actividad que termina a
    medianoche.

    Raises:
        ErrorConferencia: si el texto no tiene el formato esperado o el valor
            está fuera de rango.
    """

    if texto is None:
        raise ErrorConferencia("La hora no puede estar vacía.")
    limpio = str(texto).strip().replace(".", "").replace(" ", "")
    coincidencia = _PATRON_HORA.match(limpio)
    if not coincidencia:
        raise ErrorConferencia(
            f"Hora inválida: '{texto}'. Usa el formato HH:MM, por ejemplo 08:30."
        )
    horas = int(coincidencia.group(1))
    minutos = int(coincidencia.group(2))
    if horas == 24 and minutos == 0:
        return MINUTOS_POR_DIA
    if not (0 <= horas <= 23 and 0 <= minutos <= 59):
        raise ErrorConferencia(f"Hora fuera de rango: '{texto}'.")
    return horas * 60 + minutos


def minutos_a_hhmm(minutos: int) -> str:
    """Convierte minutos desde la medianoche a una cadena ``HH:MM``."""

    valor = int(minutos)
    if valor == MINUTOS_POR_DIA:
        return "24:00"
    valor %= MINUTOS_POR_DIA
    return f"{valor // 60:02d}:{valor % 60:02d}"


@dataclass(frozen=True, slots=True)
class Conferencia:
    """Actividad académica que debe asignarse a una sala.

    Attributes:
        id: Identificador único (por ejemplo ``C01``).
        nombre: Nombre visible de la actividad.
        inicio: Minutos desde la medianoche en que inicia.
        fin: Minutos desde la medianoche en que termina (exclusivo).
        categoria: Etiqueta usada para colorear la línea de tiempo.
    """

    id: str
    nombre: str
    inicio: int
    fin: int
    categoria: str = "Académica"

    def __post_init__(self) -> None:
        if not str(self.id).strip():
            raise ErrorConferencia("El identificador de la conferencia es obligatorio.")
        if not str(self.nombre).strip():
            raise ErrorConferencia("El nombre de la conferencia es obligatorio.")
        if not isinstance(self.inicio, int) or not isinstance(self.fin, int):
            raise ErrorConferencia("Las horas deben expresarse en minutos enteros.")
        if not (0 <= self.inicio < self.fin <= MINUTOS_POR_DIA):
            raise ErrorConferencia(
                "Horario inválido para "
                f"'{self.nombre}': {minutos_a_hhmm(self.inicio)} - "
                f"{minutos_a_hhmm(self.fin)}. La hora final debe ser mayor que "
                "la inicial y ambas deben estar dentro del día."
            )

    @property
    def duracion(self) -> int:
        """Duración en minutos."""

        return self.fin - self.inicio

    @property
    def hora_inicio(self) -> str:
        return minutos_a_hhmm(self.inicio)

    @property
    def hora_fin(self) -> str:
        return minutos_a_hhmm(self.fin)

    @property
    def horario(self) -> str:
        return f"{self.hora_inicio} - {self.hora_fin}"

    def solapa_con(self, otra: "Conferencia", margen: int = 0) -> bool:
        """Indica si dos actividades se solapan.

        Args:
            otra: Conferencia con la que se compara.
            margen: Minutos de separación exigidos entre actividades. Un margen
                de cero permite que una actividad empiece exactamente cuando
                termina otra.
        """

        if margen < 0:
            raise ValueError("El margen no puede ser negativo.")
        return self.inicio < otra.fin + margen and otra.inicio < self.fin + margen

    @classmethod
    def desde_texto(
        cls,
        id: str,
        nombre: str,
        inicio: str,
        fin: str,
        categoria: str = "Académica",
    ) -> "Conferencia":
        """Construye una conferencia a partir de horas en formato ``HH:MM``."""

        return cls(
            id=str(id).strip(),
            nombre=str(nombre).strip(),
            inicio=hhmm_a_minutos(inicio),
            fin=hhmm_a_minutos(fin),
            categoria=str(categoria).strip() or "Académica",
        )


@dataclass(frozen=True, slots=True)
class Asignacion:
    """Relación entre una conferencia y la sala que la aloja."""

    conferencia: Conferencia
    sala: int

    @property
    def nombre_sala(self) -> str:
        return f"Sala {self.sala}"


@dataclass(frozen=True, slots=True)
class PasoAsignacion:
    """Registro de una decisión voraz para la ejecución paso a paso."""

    numero: int
    conferencia: Conferencia
    sala: int
    reutilizada: bool
    salas_antes: tuple[tuple[int, int], ...]
    solapamientos: tuple[str, ...]
    ids_solapadas: tuple[str, ...]
    explicacion: str

    @property
    def nombre_sala(self) -> str:
        return f"Sala {self.sala}"


@dataclass(frozen=True, slots=True)
class DemandaPico:
    """Instante de mayor demanda y conferencias simultáneas en ese momento."""

    cantidad: int
    inicio: int | None
    fin: int | None
    conferencias: tuple[str, ...]

    @property
    def horario(self) -> str:
        if self.inicio is None or self.fin is None:
            return "Sin datos"
        return f"{minutos_a_hhmm(self.inicio)} - {minutos_a_hhmm(self.fin)}"



def validar_conferencias(conferencias: Iterable[Conferencia]) -> list[str]:
    """Revisa una colección de conferencias y devuelve los errores encontrados.

    La validación de cada horario se realiza en :class:`Conferencia`; aquí se
    comprueban condiciones globales como la unicidad de los identificadores.
    """

    lista = list(conferencias)
    errores: list[str] = []
    vistos: set[str] = set()
    duplicados: set[str] = set()
    for conferencia in lista:
        if not isinstance(conferencia, Conferencia):
            errores.append("La colección contiene un elemento que no es una conferencia.")
            continue
        if conferencia.id in vistos:
            duplicados.add(conferencia.id)
        vistos.add(conferencia.id)
    for identificador in sorted(duplicados):
        errores.append(f"El identificador '{identificador}' está repetido.")
    return errores


CRITERIOS: dict[str, tuple[str, Callable[[Conferencia], tuple] | None]] = {
    "inicio": (
        "Voraz por hora de inicio",
        lambda c: (c.inicio, c.fin, c.id),
    ),
    "original": (
        "Orden de registro",
        None,
    ),
    "duracion": (
        "Duración ascendente",
        lambda c: (c.duracion, c.inicio, c.id),
    ),
    "fin": (
        "Hora de finalización ascendente",
        lambda c: (c.fin, c.inicio, c.id),
    ),
    "inicio_desc": (
        "Hora de inicio descendente",
        lambda c: (-c.inicio, c.fin, c.id),
    ),
}
"""Criterios de ordenamiento disponibles para comparar estrategias.

El criterio ``inicio`` corresponde al algoritmo exigido por el escenario 5.
Los demás se incluyen para demostrar que el orden de selección afecta la
calidad de una heurística voraz.
"""


def nombre_criterio(clave: str) -> str:
    """Devuelve la etiqueta legible de un criterio."""

    if clave not in CRITERIOS:
        raise ValueError(f"Criterio desconocido: '{clave}'.")
    return CRITERIOS[clave][0]


def ordenar_conferencias(
    conferencias: Iterable[Conferencia], criterio: str = "inicio"
) -> list[Conferencia]:
    """Ordena las conferencias según el criterio indicado.

    El ordenamiento es estable, por lo que el criterio ``original`` conserva el
    orden en que las conferencias fueron registradas.
    """

    if criterio not in CRITERIOS:
        raise ValueError(
            f"Criterio desconocido: '{criterio}'. "
            f"Opciones: {', '.join(CRITERIOS)}."
        )
    lista = list(conferencias)
    clave_orden = CRITERIOS[criterio][1]
    if clave_orden is None:
        return lista
    return sorted(lista, key=clave_orden)


def calcular_demanda_maxima(
    conferencias: Iterable[Conferencia], margen: int = 0
) -> DemandaPico:
    """Calcula el mayor número de conferencias simultáneas mediante un barrido.

    Se construyen eventos de inicio y de fin. En un mismo instante se procesan
    primero los fines y después los inicios, de modo que dos actividades
    consecutivas (una termina cuando la otra empieza) no se consideran
    simultáneas. El costo es :math:`O(n \\log n)` por el ordenamiento de los
    eventos.

    Args:
        conferencias: Actividades a analizar.
        margen: Minutos de separación exigidos entre actividades.

    Returns:
        La cantidad máxima de actividades simultáneas, el intervalo donde ocurre
        y los nombres de las conferencias activas al inicio de ese intervalo.
    """

    if margen < 0:
        raise ValueError("El margen no puede ser negativo.")
    lista = list(conferencias)
    if not lista:
        return DemandaPico(0, None, None, ())

    eventos: dict[int, tuple[list[Conferencia], list[Conferencia]]] = {}
    for conferencia in lista:
        inicios, _ = eventos.setdefault(conferencia.inicio, ([], []))
        inicios.append(conferencia)
        _, fines = eventos.setdefault(conferencia.fin + margen, ([], []))
        fines.append(conferencia)

    tiempos = sorted(eventos)
    activos: dict[str, Conferencia] = {}
    maximo = 0
    pico_inicio: int | None = None
    pico_fin: int | None = None
    pico_nombres: tuple[str, ...] = ()
    en_pico = False

    for indice, instante in enumerate(tiempos):
        inicios, fines = eventos[instante]
        for conferencia in fines:
            activos.pop(conferencia.id, None)
        for conferencia in inicios:
            activos[conferencia.id] = conferencia

        cantidad = len(activos)
        siguiente = tiempos[indice + 1] if indice + 1 < len(tiempos) else instante
        if cantidad > maximo:
            maximo = cantidad
            pico_inicio = instante
            pico_fin = siguiente
            en_pico = True
            pico_nombres = tuple(
                c.nombre
                for c in sorted(
                    activos.values(), key=lambda c: (c.inicio, c.fin, c.id)
                )
            )
        elif cantidad == maximo and pico_inicio is not None and en_pico:
            # El pico se mantiene: se amplía el intervalo representativo.
            pico_fin = siguiente
        elif cantidad < maximo:
            en_pico = False

    return DemandaPico(maximo, pico_inicio, pico_fin, pico_nombres)



@dataclass(frozen=True, slots=True)
class ResultadoAsignacion:
    """Solución completa producida por el algoritmo voraz."""

    conferencias: tuple[Conferencia, ...]
    orden: tuple[Conferencia, ...]
    asignaciones: tuple[Asignacion, ...]
    pasos: tuple[PasoAsignacion, ...]
    criterio: str
    margen: int
    demanda: DemandaPico
    tiempo_ms: float

    @property
    def total_salas(self) -> int:
        """Cantidad de salas utilizadas por la solución."""

        return max((asignacion.sala for asignacion in self.asignaciones), default=0)

    @property
    def es_optimo(self) -> bool:
        """``True`` cuando el número de salas iguala la demanda máxima."""

        return self.total_salas == self.demanda.cantidad

    @property
    def salas_usadas(self) -> tuple[int, ...]:
        return tuple(range(1, self.total_salas + 1))

    def asignacion_de(self, id_conferencia: str) -> Asignacion | None:
        """Busca la asignación de una conferencia por su identificador."""

        for asignacion in self.asignaciones:
            if asignacion.conferencia.id == id_conferencia:
                return asignacion
        return None

    def por_sala(self) -> dict[int, list[Asignacion]]:
        """Agrupa las asignaciones por número de sala."""

        agrupadas: dict[int, list[Asignacion]] = {
            sala: [] for sala in self.salas_usadas
        }
        for asignacion in self.asignaciones:
            agrupadas.setdefault(asignacion.sala, []).append(asignacion)
        for asignaciones in agrupadas.values():
            asignaciones.sort(key=lambda a: (a.conferencia.inicio, a.conferencia.id))
        return agrupadas

    def resumen(self) -> str:
        """Texto corto con los indicadores principales de la solución."""

        if not self.conferencias:
            return "Sin conferencias registradas."
        return (
            f"{len(self.conferencias)} conferencias · {self.total_salas} salas · "
            f"demanda máxima {self.demanda.cantidad} ({self.demanda.horario}) · "
            f"{self.tiempo_ms:.2f} ms"
        )



def asignar_salas(
    conferencias: Iterable[Conferencia],
    criterio: str = "inicio",
    margen: int = 0,
    registrar_pasos: bool = True,
) -> ResultadoAsignacion:
    """Asigna salas a las conferencias mediante el algoritmo voraz.

    El procedimiento es el exigido por el escenario 5:

    1. Registrar las conferencias con su hora de inicio y finalización.
    2. Ordenarlas por hora de inicio ascendente (criterio ``inicio``).
    3. Recorrerlas en ese orden.
    4. Buscar una sala disponible usando una cola de prioridad cuyo mínimo es
       la hora de liberación más temprana.
    5. Reutilizar esa sala o crear una nueva si todas están ocupadas.

    Args:
        conferencias: Actividades por planificar.
        criterio: Clave de :data:`CRITERIOS`. El valor ``inicio`` implementa el
            algoritmo del escenario; los demás permiten comparar heurísticas.
        margen: Minutos mínimos entre dos actividades de la misma sala.
        registrar_pasos: Si es ``True`` se guarda la bitácora para la ejecución
            paso a paso.

    Returns:
        Resultado con la solución, la demanda máxima y la bitácora de decisiones.

    Raises:
        ErrorConferencia: si hay identificadores repetidos o datos inválidos.
        ValueError: si el criterio o el margen no son válidos.
    """

    inicio_medicion = time.perf_counter()
    if criterio not in CRITERIOS:
        raise ValueError(
            f"Criterio desconocido: '{criterio}'. "
            f"Opciones: {', '.join(CRITERIOS)}."
        )
    margen = int(margen)
    if margen < 0:
        raise ValueError("El margen no puede ser negativo.")
    lista = list(conferencias)
    errores = validar_conferencias(lista)
    if errores:
        raise ErrorConferencia(" ".join(errores))

    orden = ordenar_conferencias(lista, criterio)

    # La cola de prioridad guarda (hora_de_liberacion, numero_de_sala).
    # El mínimo indica la sala que antes queda disponible.
    disponibles: list[tuple[int, int]] = []
    ultima_por_sala: dict[int, Asignacion] = {}
    asignaciones: list[Asignacion] = []
    pasos: list[PasoAsignacion] = []
    siguiente_sala = 1

    for numero, conferencia in enumerate(orden, start=1):
        salas_antes: tuple[tuple[int, int], ...] = ()
        solapadas: tuple[Conferencia, ...] = ()
        nombres_solapados: tuple[str, ...] = ()
        ids_solapados: tuple[str, ...] = ()
        if registrar_pasos:
            # Diagnóstico para la bitácora didáctica. El costo de esta parte es
            # O(s log s) por paso, donde s es el número de salas abiertas; la
            # asignación básica sigue siendo O(n log n).
            salas_antes = tuple(
                sorted(
                    (sala, asignacion.conferencia.fin)
                    for sala, asignacion in ultima_por_sala.items()
                )
            )
            solapadas = tuple(
                asignacion.conferencia
                for asignacion in ultima_por_sala.values()
                if asignacion.conferencia.solapa_con(conferencia, margen)
            )
            nombres_solapados = tuple(c.nombre for c in solapadas)
            ids_solapados = tuple(c.id for c in solapadas)

        if disponibles and disponibles[0][0] <= conferencia.inicio:
            libre_desde, sala = heapq.heappop(disponibles)
            reutilizada = True
            anterior = ultima_por_sala[sala].conferencia
            explicacion = (
                f"La Sala {sala} quedó libre a las {minutos_a_hhmm(libre_desde)} "
                f"(fin {anterior.hora_fin}"
                + (f" + {margen} min de margen" if margen else "")
                + f"). Como {minutos_a_hhmm(libre_desde)} ≤ "
                f"{conferencia.hora_inicio}, se reutiliza."
            )
        else:
            sala = siguiente_sala
            siguiente_sala += 1
            reutilizada = False
            if not disponibles:
                explicacion = (
                    f"No hay salas ocupadas todavía; se crea la Sala {sala}."
                )
            else:
                liberacion_mas_pronto = disponibles[0][0]
                explicacion = (
                    "Ninguna sala está disponible: la que se libera más pronto "
                    f"lo hace a las {minutos_a_hhmm(liberacion_mas_pronto)}, "
                    f"después del inicio {conferencia.hora_inicio}. "
                    f"Se crea la Sala {sala}."
                )

        if solapadas:
            visibles = ", ".join(nombres_solapados[:3])
            if len(nombres_solapados) > 3:
                visibles += f" y {len(nombres_solapados) - 3} más"
            explicacion += (
                f" Se solapa en el tiempo con {len(solapadas)} actividad(es) "
                f"ya programada(s): {visibles}."
            )
        else:
            explicacion += " No se solapa con actividades ya programadas."

        asignacion = Asignacion(conferencia=conferencia, sala=sala)
        asignaciones.append(asignacion)
        ultima_por_sala[sala] = asignacion
        heapq.heappush(disponibles, (conferencia.fin + margen, sala))
        if registrar_pasos:
            pasos.append(
                PasoAsignacion(
                    numero=numero,
                    conferencia=conferencia,
                    sala=sala,
                    reutilizada=reutilizada,
                    salas_antes=salas_antes,
                    solapamientos=nombres_solapados,
                    ids_solapadas=ids_solapados,
                    explicacion=explicacion,
                )
            )

    demanda = calcular_demanda_maxima(lista, margen)
    tiempo_ms = (time.perf_counter() - inicio_medicion) * 1000.0
    return ResultadoAsignacion(
        conferencias=tuple(lista),
        orden=tuple(orden),
        asignaciones=tuple(asignaciones),
        pasos=tuple(pasos),
        criterio=criterio,
        margen=margen,
        demanda=demanda,
        tiempo_ms=tiempo_ms,
    )



def validar_asignacion(resultado: ResultadoAsignacion) -> list[str]:
    """Comprueba que la solución sea factible.

    Verifica que cada conferencia aparezca exactamente una vez y que dentro de
    cada sala no existan solapamientos, considerando el margen configurado.
    Devuelve una lista vacía cuando la asignación es correcta.
    """

    errores: list[str] = []
    ids_originales = sorted(c.id for c in resultado.conferencias)
    ids_asignados = sorted(a.conferencia.id for a in resultado.asignaciones)
    if ids_originales != ids_asignados:
        errores.append(
            "Las conferencias asignadas no coinciden exactamente con las registradas."
        )

    por_sala: dict[int, list[Conferencia]] = {}
    for asignacion in resultado.asignaciones:
        por_sala.setdefault(asignacion.sala, []).append(asignacion.conferencia)

    for sala, conferencias in por_sala.items():
        ordenadas = sorted(conferencias, key=lambda c: (c.inicio, c.fin, c.id))
        for anterior, actual in zip(ordenadas, ordenadas[1:]):
            if anterior.fin + resultado.margen > actual.inicio:
                errores.append(
                    f"Conflicto en la Sala {sala}: '{anterior.nombre}' "
                    f"({anterior.horario}) y '{actual.nombre}' ({actual.horario})."
                )

    if sorted(por_sala) != list(range(1, len(por_sala) + 1)):
        errores.append("Los números de sala no son consecutivos desde 1.")
    if len(por_sala) != resultado.total_salas:
        errores.append("El total de salas no coincide con las salas utilizadas.")
    if resultado.total_salas < resultado.demanda.cantidad:
        errores.append(
            "La solución usa menos salas que la demanda máxima, lo cual es imposible."
        )
    return errores


@dataclass(frozen=True, slots=True)
class ResumenEstrategia:
    """Resultado resumido de aplicar un criterio de ordenamiento."""

    clave: str
    nombre: str
    salas: int
    tiempo_ms: float
    es_optima: bool


def comparar_estrategias(
    conferencias: Iterable[Conferencia], margen: int = 0
) -> tuple[ResumenEstrategia, ...]:
    """Ejecuta el algoritmo con todos los criterios de :data:`CRITERIOS`.

    Se usa en la interfaz y en el informe para comparar el orden exigido por el
    escenario (hora de inicio) con otros órdenes posibles.
    """

    lista = list(conferencias)
    errores = validar_conferencias(lista)
    if errores:
        raise ErrorConferencia(" ".join(errores))
    demanda = calcular_demanda_maxima(lista, margen)
    resumenes: list[ResumenEstrategia] = []
    for clave, (nombre, _) in CRITERIOS.items():
        resultado = asignar_salas(
            lista, criterio=clave, margen=margen, registrar_pasos=False
        )
        resumenes.append(
            ResumenEstrategia(
                clave=clave,
                nombre=nombre,
                salas=resultado.total_salas,
                tiempo_ms=resultado.tiempo_ms,
                es_optima=resultado.total_salas == demanda.cantidad,
            )
        )
    return tuple(resumenes)

