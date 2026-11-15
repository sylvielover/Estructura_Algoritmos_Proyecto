"""Paquete del proyecto: asignación de salas mediante un algoritmo voraz.

Escenario 5 del proyecto final de Estructura de Datos y Análisis de Algoritmos
de CECAR: planificación y asignación de salas para eventos académicos.

Módulos
-------
modelo
    Tipos de datos, algoritmo voraz, demanda máxima y comparación de criterios.
datos
    Carga de archivos CSV, conjuntos de ejemplo y exportación de resultados.
interfaz
    Aplicación gráfica construida con Tkinter (incluida en la biblioteca estándar).
"""

from .modelo import (
    CRITERIOS,
    Asignacion,
    Conferencia,
    DemandaPico,
    ErrorConferencia,
    PasoAsignacion,
    ResultadoAsignacion,
    asignar_salas,
    calcular_demanda_maxima,
    comparar_estrategias,
    hhmm_a_minutos,
    minutos_a_hhmm,
    nombre_criterio,
    validar_asignacion,
    validar_conferencias,
)

__all__ = [
    "CRITERIOS",
    "Asignacion",
    "Conferencia",
    "DemandaPico",
    "ErrorConferencia",
    "PasoAsignacion",
    "ResultadoAsignacion",
    "asignar_salas",
    "calcular_demanda_maxima",
    "comparar_estrategias",
    "hhmm_a_minutos",
    "minutos_a_hhmm",
    "nombre_criterio",
    "validar_asignacion",
    "validar_conferencias",
]

__version__ = "1.0.0"
