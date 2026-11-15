"""Carga de datos, conjuntos de ejemplo y exportación de resultados.

El formato CSV usado por la aplicación tiene las columnas ``id``, ``nombre``,
``inicio``, ``fin`` y ``categoria``. Las horas se escriben como ``HH:MM`` y el
separador puede ser punto y coma (recomendado para Excel en español) o coma.
"""

from __future__ import annotations

import csv
import random
import unicodedata
from pathlib import Path
from typing import Iterable, Sequence

from .modelo import Conferencia, ErrorConferencia, ResultadoAsignacion, minutos_a_hhmm

RUTA_DATOS = Path(__file__).resolve().parent.parent / "datos"
RUTA_EJEMPLO = RUTA_DATOS / "conferencias_ejemplo.csv"


class ErrorDatos(ValueError):
    """Error al leer o escribir un archivo de datos."""


def _c(
    id: str, nombre: str, inicio: str, fin: str, categoria: str = "Académica"
) -> Conferencia:
    return Conferencia.desde_texto(id, nombre, inicio, fin, categoria)


def conferencias_ejemplo() -> list[Conferencia]:
    """Conjunto institucional de 13 actividades usado en la demostración.

    El orden de registro no coincide con el orden cronológico (la conferencia
    C11 aparece al final) para evidenciar la importancia de ordenar por hora de
    inicio. La demanda máxima es de 4 salas simultáneas entre las 09:15 y las
    10:30.
    """

    return [
        _c("C01", "Instalación oficial", "07:00", "08:00", "Institucional"),
        _c(
            "C02",
            "Inteligencia artificial en la educación",
            "08:00",
            "09:30",
            "Conferencia",
        ),
        _c("C03", "Taller de robótica educativa", "08:30", "10:00", "Taller"),
        _c(
            "C04",
            "Seminario de investigación formativa",
            "09:00",
            "10:30",
            "Seminario",
        ),
        _c("C05", "Panel de egresados CECAR", "09:30", "11:00", "Panel"),
        _c("C06", "Taller de emprendimiento", "10:00", "11:30", "Taller"),
        _c(
            "C07",
            "Conferencia de ciberseguridad",
            "11:00",
            "12:30",
            "Conferencia",
        ),
        _c("C08", "Feria de proyectos estudiantiles", "11:30", "13:00", "Feria"),
        _c("C09", "Encuentro de semilleros", "12:00", "13:30", "Encuentro"),
        _c("C10", "Mesa de trabajo de facultades", "13:00", "14:30", "Reunión"),
        _c("C11", "Conversatorio de inclusión", "09:15", "10:45", "Conversatorio"),
        _c("C12", "Clausura del evento", "14:30", "15:30", "Institucional"),
        _c(
            "C13",
            "Reunión de coordinadores académicos",
            "15:00",
            "16:30",
            "Reunión",
        ),
    ]


_NOMBRES_ALEATORIOS = (
    ("Conferencia", "Conferencia de innovación educativa"),
    ("Taller", "Taller de análisis de datos"),
    ("Seminario", "Seminario de investigación aplicada"),
    ("Panel", "Panel de egresados"),
    ("Feria", "Feria de proyectos"),
    ("Reunión", "Reunión de coordinación académica"),
    ("Conversatorio", "Conversatorio de inclusión"),
    ("Institucional", "Acto institucional"),
)


def conferencias_aleatorias(
    cantidad: int = 12,
    semilla: int | None = None,
    desde: int = 7 * 60,
    hasta: int = 18 * 60,
) -> list[Conferencia]:
    """Genera conferencias válidas para probar la simulación.

    Los horarios se generan en intervalos de 15 minutos. Si se especifica una
    semilla, el resultado es reproducible (útil para las pruebas automáticas).
    """

    if cantidad < 0:
        raise ValueError("La cantidad no puede ser negativa.")
    if not (0 <= desde < hasta <= 24 * 60):
        raise ValueError("El rango horario no es válido.")
    generador = random.Random(semilla)
    duraciones = (45, 60, 75, 90, 105, 120)
    conferencias: list[Conferencia] = []
    for indice in range(1, cantidad + 1):
        duracion = generador.choice(duraciones)
        ultimo_inicio = hasta - duracion
        if ultimo_inicio < desde:
            duracion = min(duracion, hasta - desde)
            ultimo_inicio = desde
        inicio = generador.randrange(desde, ultimo_inicio + 1, 15)
        categoria, nombre_base = generador.choice(_NOMBRES_ALEATORIOS)
        conferencias.append(
            Conferencia(
                id=f"C{indice:02d}",
                nombre=f"{nombre_base} {indice}",
                inicio=inicio,
                fin=inicio + duracion,
                categoria=categoria,
            )
        )
    return conferencias



def _normalizar(texto: str) -> str:
    """Convierte un encabezado a minúsculas sin acentos ni espacios extra."""

    descompuesto = unicodedata.normalize("NFKD", str(texto))
    sin_acentos = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return " ".join(sin_acentos.lower().strip().split())


_ALIAS_COLUMNAS: dict[str, set[str]] = {
    "id": {"id", "codigo", "code", "identificador"},
    "nombre": {"nombre", "conferencia", "actividad", "name"},
    "inicio": {"inicio", "hora inicio", "hora_inicio", "start", "desde"},
    "fin": {"fin", "hora fin", "hora_fin", "end", "hasta"},
    "categoria": {"categoria", "category", "tipo", "modalidad"},
}


def _detectar_delimitador(muestra: str) -> str:
    """Elige el separador más probable observando la primera línea con datos."""

    primera_linea = next(
        (linea for linea in muestra.splitlines() if linea.strip()), ""
    )
    return ";" if primera_linea.count(";") >= primera_linea.count(",") else ","


def cargar_csv(ruta: str | Path) -> list[Conferencia]:
    """Lee conferencias desde un archivo CSV.

    Se aceptan encabezados con o sin acentos (``inicio``, ``hora_inicio``,
    ``hora inicio``), separador ``;`` o ``,`` y codificación UTF-8 con o sin
    BOM. Las filas inválidas se reportan con su número de línea.

    Raises:
        ErrorDatos: si el archivo no existe, no tiene las columnas necesarias o
            contiene filas inválidas.
    """

    camino = Path(ruta)
    if not camino.exists():
        raise ErrorDatos(f"No se encontró el archivo:\n{camino}")
    try:
        with camino.open("r", encoding="utf-8-sig", newline="") as archivo:
            muestra = archivo.read(4096)
            archivo.seek(0)
            delimitador = _detectar_delimitador(muestra)
            lector = csv.DictReader(archivo, delimiter=delimitador)
            encabezados = lector.fieldnames or []
            mapa: dict[str, str] = {}
            for encabezado in encabezados:
                normalizado = _normalizar(encabezado)
                for campo, alias in _ALIAS_COLUMNAS.items():
                    if normalizado in alias and campo not in mapa:
                        mapa[campo] = encabezado

            faltantes = [
                campo for campo in ("nombre", "inicio", "fin") if campo not in mapa
            ]
            if faltantes:
                raise ErrorDatos(
                    "El CSV debe incluir las columnas nombre, inicio y fin. "
                    f"Faltan: {', '.join(faltantes)}. "
                    f"Encabezados encontrados: {', '.join(encabezados) or '(ninguno)'}."
                )

            conferencias: list[Conferencia] = []
            errores: list[str] = []
            ids: set[str] = set()
            for numero, fila in enumerate(lector, start=2):
                if not any((valor or "").strip() for valor in fila.values()):
                    continue
                try:
                    nombre = (fila.get(mapa["nombre"]) or "").strip()
                    inicio = (fila.get(mapa["inicio"]) or "").strip()
                    fin = (fila.get(mapa["fin"]) or "").strip()
                    categoria = (
                        (fila.get(mapa["categoria"]) or "").strip()
                        if "categoria" in mapa
                        else "Académica"
                    ) or "Académica"
                    id_texto = (
                        (fila.get(mapa["id"]) or "").strip() if "id" in mapa else ""
                    )
                    if not id_texto:
                        id_texto = f"C{len(conferencias) + 1:02d}"
                    base_id = id_texto
                    sufijo = 2
                    while id_texto in ids:
                        id_texto = f"{base_id}_{sufijo}"
                        sufijo += 1
                    ids.add(id_texto)
                    conferencias.append(
                        Conferencia.desde_texto(
                            id_texto, nombre, inicio, fin, categoria
                        )
                    )
                except (ErrorConferencia, ValueError) as exc:
                    errores.append(f"Línea {numero}: {exc}")
    except OSError as exc:
        raise ErrorDatos(f"No se pudo leer el archivo:\n{camino}\n{exc}") from exc

    if errores:
        detalle = "\n".join(errores[:10])
        if len(errores) > 10:
            detalle += f"\n... y {len(errores) - 10} error(es) más."
        raise ErrorDatos(f"El archivo contiene datos inválidos:\n{detalle}")
    if not conferencias:
        raise ErrorDatos("El archivo no contiene conferencias para cargar.")
    return conferencias


def guardar_conferencias_csv(
    ruta: str | Path, conferencias: Iterable[Conferencia]
) -> Path:
    """Guarda una colección de conferencias en formato CSV."""

    camino = Path(ruta)
    try:
        camino.parent.mkdir(parents=True, exist_ok=True)
        with camino.open("w", encoding="utf-8-sig", newline="") as archivo:
            escritor = csv.writer(archivo, delimiter=";")
            escritor.writerow(["id", "nombre", "inicio", "fin", "categoria"])
            for conferencia in conferencias:
                escritor.writerow(
                    [
                        conferencia.id,
                        conferencia.nombre,
                        conferencia.hora_inicio,
                        conferencia.hora_fin,
                        conferencia.categoria,
                    ]
                )
    except OSError as exc:
        raise ErrorDatos(f"No se pudo guardar el archivo:\n{camino}\n{exc}") from exc
    return camino


def guardar_resultado_csv(ruta: str | Path, resultado: ResultadoAsignacion) -> Path:
    """Exporta la solución (incluida la sala asignada) a un CSV."""

    camino = Path(ruta)
    try:
        camino.parent.mkdir(parents=True, exist_ok=True)
        with camino.open("w", encoding="utf-8-sig", newline="") as archivo:
            escritor = csv.writer(archivo, delimiter=";")
            escritor.writerow(
                [
                    "orden",
                    "id",
                    "conferencia",
                    "categoria",
                    "horario",
                    "inicio",
                    "fin",
                    "duracion_min",
                    "sala",
                ]
            )
            for posicion, asignacion in enumerate(resultado.asignaciones, start=1):
                conferencia = asignacion.conferencia
                escritor.writerow(
                    [
                        posicion,
                        conferencia.id,
                        conferencia.nombre,
                        conferencia.categoria,
                        conferencia.horario,
                        conferencia.hora_inicio,
                        conferencia.hora_fin,
                        conferencia.duracion,
                        asignacion.nombre_sala,
                    ]
                )
    except OSError as exc:
        raise ErrorDatos(f"No se pudo guardar el archivo:\n{camino}\n{exc}") from exc
    return camino

