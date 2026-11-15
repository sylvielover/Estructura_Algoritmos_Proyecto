"""Punto de entrada del Sistema de Asignación de Salas de CECAR.

Ejecuta la aplicación de escritorio desarrollada con Tkinter:

    py main.py
"""

from __future__ import annotations

from salas.interfaz import AplicacionSalas


def main() -> None:
    """Crea la ventana principal y entrega el control al bucle de eventos."""

    aplicacion = AplicacionSalas()
    aplicacion.mainloop()


if __name__ == "__main__":
    main()
