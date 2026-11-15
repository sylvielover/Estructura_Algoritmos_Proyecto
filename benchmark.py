"""Banco de pruebas reproducible para el algoritmo de asignación de salas.

Uso:
    py benchmark.py

Genera ``docs/resultados_benchmark.csv`` con tiempos de ejecución, memoria
pico y calidad de la solución para varios tamaños de entrada. Los datos se
generan con semillas fijas, de modo que los resultados pueden repetirse.
"""

from __future__ import annotations

import csv
import statistics
import time
import tracemalloc
from pathlib import Path

from salas.datos import conferencias_aleatorias
from salas.modelo import asignar_salas, validar_asignacion

RAIZ = Path(__file__).resolve().parent
SALIDA = RAIZ / "docs" / "resultados_benchmark.csv"
TAMANOS = (10, 50, 100, 250, 500, 1000, 2000, 4000)
SEMILLA = 2025


def medir(n: int, repeticiones: int) -> dict[str, object]:
    """Ejecuta la asignación varias veces y resume tiempo, memoria y calidad."""

    conferencias = conferencias_aleatorias(n, semilla=SEMILLA + n)
    tiempos: list[float] = []
    resultado = None

    # Calentamiento para separar el costo de carga de módulos del de medición.
    asignar_salas(conferencias, registrar_pasos=False)
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        resultado = asignar_salas(conferencias, registrar_pasos=False)
        tiempos.append((time.perf_counter() - inicio) * 1000.0)

    # La memoria se mide en una ejecución aparte: tracemalloc ralentiza el
    # intérprete y distorsionaría los tiempos si se activara durante ellas.
    tracemalloc.start()
    try:
        resultado = asignar_salas(conferencias, registrar_pasos=False)
        _, memoria_pico = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    assert resultado is not None
    errores = validar_asignacion(resultado)
    return {
        "n": n,
        "repeticiones": repeticiones,
        "tiempo_promedio_ms": round(statistics.fmean(tiempos), 4),
        "tiempo_min_ms": round(min(tiempos), 4),
        "tiempo_max_ms": round(max(tiempos), 4),
        "memoria_pico_kib": round(memoria_pico / 1024.0, 2),
        "salas": resultado.total_salas,
        "demanda_maxima": resultado.demanda.cantidad,
        "optimo": "Sí" if resultado.es_optimo else "No",
        "validacion": "OK" if not errores else "ERROR",
    }


def main() -> None:
    filas = []
    for n in TAMANOS:
        repeticiones = 7 if n <= 500 else 4 if n <= 2000 else 3
        fila = medir(n, repeticiones)
        filas.append(fila)
        print(
            f"n={fila['n']:>5}  t={fila['tiempo_promedio_ms']:>9.3f} ms  "
            f"mem={fila['memoria_pico_kib']:>8.1f} KiB  "
            f"salas={fila['salas']:>3}  demanda={fila['demanda_maxima']:>3}  "
            f"{fila['optimo']}  {fila['validacion']}"
        )

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=list(filas[0].keys()),
            delimiter=";",
        )
        escritor.writeheader()
        escritor.writerows(filas)

    print(f"\nResultados guardados en: {SALIDA}")
    print("\n| n | Tiempo promedio (ms) | Memoria pico (KiB) | Salas | Demanda |\n")
    print("|---:|---:|---:|---:|---:|")
    for fila in filas:
        print(
            f"| {fila['n']} | {fila['tiempo_promedio_ms']:.3f} | "
            f"{fila['memoria_pico_kib']:.1f} | {fila['salas']} | "
            f"{fila['demanda_maxima']} |"
        )


if __name__ == "__main__":
    main()
