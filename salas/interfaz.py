"""Interfaz gráfica de la asignación de salas (Tkinter, biblioteca estándar).

La ventana principal integra:

* Registro, edición, importación y exportación de conferencias.
* Línea de tiempo por salas con ejecución paso a paso y reproducción automática.
* Panel de estadísticas, comparación de criterios y explicación del diseño voraz.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, font as tkfont, messagebox, ttk

from .datos import (
    RUTA_DATOS,
    ErrorDatos,
    cargar_csv,
    conferencias_aleatorias,
    conferencias_ejemplo,
    guardar_resultado_csv,
)
from .modelo import (
    CRITERIOS,
    Conferencia,
    ErrorConferencia,
    ResultadoAsignacion,
    ResumenEstrategia,
    asignar_salas,
    comparar_estrategias,
    hhmm_a_minutos,
    minutos_a_hhmm,
    nombre_criterio,
    validar_asignacion,
)

FUENTE = "Segoe UI"

COLOR_FONDO = "#EEF2F7"
COLOR_PANEL = "#FFFFFF"
COLOR_BORDE = "#D4DEE9"
AZUL = "#0B3C5D"
AZUL_MEDIO = "#1F6FB2"
AZUL_CLARO = "#E8F1FA"
VERDE = "#2E9E5B"
VERDE_CLARO = "#E5F5EC"
NARANJA = "#E8A33D"
ROJO = "#D9534F"
ROJO_CLARO = "#FDECEC"
GRIS = "#6B7C8F"
GRIS_CLARO = "#F4F7FA"
TEXTO = "#1B2A38"
AMARILLO = "#F2B705"

PALETA_CATEGORIAS: dict[str, str] = {
    "Institucional": "#1F6FB2",
    "Conferencia": "#2E9E5B",
    "Taller": "#E8A33D",
    "Seminario": "#7A5AF8",
    "Panel": "#0F9B8E",
    "Feria": "#D9534F",
    "Reunión": "#8A6D3B",
    "Encuentro": "#C2569B",
    "Conversatorio": "#4263EB",
    "Académica": "#5C6B7A",
}
PALETA_RESPALDO = (
    "#3B82C4",
    "#2E9E5B",
    "#D9822B",
    "#7A5AF8",
    "#0F9B8E",
    "#C2569B",
    "#8A6D3B",
    "#D9534F",
)


def color_categoria(categoria: str) -> str:
    """Devuelve un color estable para cada categoría."""

    if categoria in PALETA_CATEGORIAS:
        return PALETA_CATEGORIAS[categoria]
    indice = sum(ord(caracter) for caracter in categoria) % len(PALETA_RESPALDO)
    return PALETA_RESPALDO[indice]


def color_texto_contraste(fondo: str) -> str:
    """Elige texto claro u oscuro según la luminancia del color de fondo."""

    try:
        rojo = int(fondo[1:3], 16)
        verde = int(fondo[3:5], 16)
        azul = int(fondo[5:7], 16)
    except (ValueError, IndexError):
        return "#FFFFFF"
    luminancia = 0.299 * rojo + 0.587 * verde + 0.114 * azul
    return "#10202F" if luminancia > 165 else "#FFFFFF"


class AplicacionSalas(tk.Tk):
    """Ventana principal del sistema de planificación de salas."""

    def __init__(self) -> None:
        super().__init__()
        self.conferencias: list[Conferencia] = conferencias_ejemplo()
        self.resultado: ResultadoAsignacion | None = None
        self.comparaciones: tuple[ResumenEstrategia, ...] = ()
        self.indice_paso: int = -1
        self.id_edicion: str | None = None
        self.margen_actual: int = 0
        self.reproduciendo: bool = False
        self._after_reproduccion: str | None = None
        self._actualizando_escala: bool = False
        self._mapa_arbol: dict[str, str] = {}
        self._ancho_canvas: int = 0
        self._parametros_actuales: tuple[str, int] = ("inicio", 0)

        self._crear_variables()
        self._configurar_ventana()
        self._configurar_estilos()
        self._construir_interfaz()
        self._configurar_atajos()
        self._recalcular("Datos de ejemplo cargados: 13 actividades académicas.")

    # ------------------------------------------------------------------
    # Configuración general
    # ------------------------------------------------------------------
    def _crear_variables(self) -> None:
        self.var_nombre = tk.StringVar()
        self.var_inicio = tk.StringVar(value="08:00")
        self.var_fin = tk.StringVar(value="09:00")
        self.var_categoria = tk.StringVar(value="Conferencia")
        self.var_margen = tk.StringVar(value="0")
        self.var_criterio = tk.StringVar(value=nombre_criterio("inicio"))
        self.var_cantidad = tk.IntVar(value=15)
        self.var_escala = tk.DoubleVar(value=0)
        self.var_velocidad = tk.DoubleVar(value=5)
        self.var_estado = tk.StringVar(value="Listo.")
        self.var_conteo = tk.StringVar(value="13 actividades")

    def _configurar_ventana(self) -> None:
        self.title("CECAR · Asignación de salas · Algoritmo voraz")
        self.geometry("1500x940")
        self.minsize(1220, 800)
        self.configure(bg=COLOR_FONDO)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.protocol("WM_DELETE_WINDOW", self._cerrar)

        for nombre in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            try:
                tkfont.nametofont(nombre).configure(family=FUENTE, size=10)
            except tk.TclError:
                pass
        self.fuente_base = tkfont.Font(family=FUENTE, size=10)
        self.fuente_pequena = tkfont.Font(family=FUENTE, size=8)
        self.fuente_negrita = tkfont.Font(family=FUENTE, size=10, weight="bold")
        self.fuente_titulo = tkfont.Font(family=FUENTE, size=20, weight="bold")
        self.fuente_valor = tkfont.Font(family=FUENTE, size=19, weight="bold")

    def _configurar_estilos(self) -> None:
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure(".", font=self.fuente_base)
        estilo.configure("TFrame", background=COLOR_FONDO)
        estilo.configure("Panel.TFrame", background=COLOR_PANEL)
        estilo.configure("TLabel", background=COLOR_FONDO, foreground=TEXTO)
        estilo.configure("Panel.TLabel", background=COLOR_PANEL, foreground=TEXTO)
        estilo.configure("Suave.TLabel", background=COLOR_PANEL, foreground=GRIS)
        estilo.configure(
            "Seccion.TLabel",
            background=COLOR_PANEL,
            foreground=AZUL,
            font=(FUENTE, 9, "bold"),
        )
        estilo.configure(
            "TButton",
            padding=(10, 6),
            background="#E6EDF5",
            foreground=TEXTO,
            borderwidth=1,
            focusthickness=0,
        )
        estilo.map(
            "TButton",
            background=[("active", "#D5E2EF"), ("disabled", "#F0F3F7")],
            foreground=[("disabled", "#9AA8B6")],
        )
        estilo.configure(
            "Accent.TButton",
            background=AZUL_MEDIO,
            foreground="#FFFFFF",
            font=(FUENTE, 10, "bold"),
            padding=(12, 7),
        )
        estilo.map(
            "Accent.TButton",
            background=[("active", AZUL), ("disabled", "#A9B8C6")],
            foreground=[("disabled", "#F2F5F8")],
        )
        estilo.configure(
            "Peligro.TButton",
            background="#FBE4E3",
            foreground="#9B2C28",
            padding=(10, 6),
        )
        estilo.map("Peligro.TButton", background=[("active", "#F5CFCD")])
        estilo.configure(
            "Treeview",
            background=COLOR_PANEL,
            fieldbackground=COLOR_PANEL,
            foreground=TEXTO,
            rowheight=25,
            borderwidth=0,
        )
        estilo.configure(
            "Treeview.Heading",
            background="#E4EBF3",
            foreground=AZUL,
            font=(FUENTE, 9, "bold"),
            padding=(6, 5),
        )
        estilo.map(
            "Treeview",
            background=[("selected", AZUL_MEDIO)],
            foreground=[("selected", "#FFFFFF")],
        )
        estilo.configure(
            "TLabelframe",
            background=COLOR_PANEL,
            bordercolor=COLOR_BORDE,
            relief="solid",
            borderwidth=1,
        )
        estilo.configure(
            "TLabelframe.Label",
            background=COLOR_PANEL,
            foreground=AZUL,
            font=(FUENTE, 10, "bold"),
        )
        estilo.configure(
            "TNotebook",
            background=COLOR_PANEL,
            borderwidth=0,
            tabmargins=(0, 4, 0, 0),
        )
        estilo.configure(
            "TNotebook.Tab",
            background="#E4EBF3",
            foreground=GRIS,
            padding=(16, 7),
            font=(FUENTE, 9, "bold"),
        )
        estilo.map(
            "TNotebook.Tab",
            background=[("selected", COLOR_PANEL)],
            foreground=[("selected", AZUL_MEDIO)],
        )
        estilo.configure("TSeparator", background=COLOR_BORDE)



    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _construir_interfaz(self) -> None:
        self._construir_encabezado()
        self._construir_barra_herramientas()
        self.cuerpo = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        self.cuerpo.grid(row=2, column=0, sticky="nsew", padx=16, pady=(10, 8))
        panel_izq = ttk.Frame(self.cuerpo, style="Panel.TFrame", padding=12)
        panel_der = ttk.Frame(self.cuerpo, style="Panel.TFrame", padding=12)
        panel_izq.configure(width=440)
        self.cuerpo.add(panel_izq, weight=0)
        self.cuerpo.add(panel_der, weight=1)
        self._construir_panel_izquierdo(panel_izq)
        self._construir_panel_derecho(panel_der)
        self._construir_barra_estado()
        self.after(220, self._ajustar_sash)

    def _ajustar_sash(self) -> None:
        try:
            self.cuerpo.sashpos(0, 440)
        except tk.TclError:
            pass

    def _construir_encabezado(self) -> None:
        cabecera = tk.Frame(self, bg=AZUL, height=94)
        cabecera.grid(row=0, column=0, sticky="ew")
        cabecera.grid_propagate(False)
        cabecera.grid_columnconfigure(0, weight=1)

        texto = tk.Frame(cabecera, bg=AZUL)
        texto.grid(row=0, column=0, sticky="w", padx=24, pady=12)
        tk.Label(
            texto,
            text="CECAR · PROGRAMA DE INGENIERÍA DE SISTEMAS",
            bg=AZUL,
            fg="#9FC7E8",
            font=(FUENTE, 8, "bold"),
        ).pack(anchor="w")
        tk.Label(
            texto,
            text="Asignación óptima de salas para eventos académicos",
            bg=AZUL,
            fg="#FFFFFF",
            font=self.fuente_titulo,
        ).pack(anchor="w", pady=(1, 0))
        tk.Label(
            texto,
            text="Escenario 5 · Algoritmo voraz por hora de inicio · Estructura de Datos y Análisis de Algoritmos",
            bg=AZUL,
            fg="#B9D4EA",
            font=(FUENTE, 9),
        ).pack(anchor="w")

        distintivo = tk.Frame(cabecera, bg=AZUL)
        distintivo.grid(row=0, column=1, sticky="e", padx=24)
        tk.Label(
            distintivo,
            text="MÍNIMO DE SALAS = MÁXIMO DE SIMULTÁNEAS",
            bg="#164C71",
            fg="#CFE7F8",
            font=(FUENTE, 8, "bold"),
            padx=14,
            pady=7,
        ).pack(anchor="e")
        tk.Label(
            distintivo,
            text="Complejidad O(n log n) · Datos propios · Sin dependencias",
            bg=AZUL,
            fg="#8FB9D8",
            font=(FUENTE, 8),
        ).pack(anchor="e", pady=(5, 0))

    def _construir_barra_herramientas(self) -> None:
        barra = tk.Frame(
            self, bg=COLOR_PANEL, highlightbackground=COLOR_BORDE, highlightthickness=1
        )
        barra.grid(row=1, column=0, sticky="ew")
        interior = ttk.Frame(barra, style="Panel.TFrame", padding=(16, 9))
        interior.pack(fill="x")

        izquierda = ttk.Frame(interior, style="Panel.TFrame")
        izquierda.pack(side="left")
        self._boton(izquierda, "Cargar ejemplo", self._cargar_ejemplo).pack(side="left")
        self._boton(izquierda, "Importar CSV", self._importar_csv).pack(
            side="left", padx=(6, 0)
        )
        self._boton(izquierda, "Exportar CSV", self._exportar_csv).pack(
            side="left", padx=(6, 0)
        )
        ttk.Separator(izquierda, orient="vertical").pack(
            side="left", fill="y", padx=12, pady=2
        )
        ttk.Label(izquierda, text="Aleatorias:", style="Suave.TLabel").pack(
            side="left", padx=(0, 5)
        )
        ttk.Spinbox(
            izquierda,
            from_=3,
            to=200,
            increment=1,
            width=5,
            textvariable=self.var_cantidad,
        ).pack(side="left")
        self._boton(izquierda, "Generar", self._generar_aleatorio).pack(
            side="left", padx=(6, 0)
        )

        derecha = ttk.Frame(interior, style="Panel.TFrame")
        derecha.pack(side="right")
        ttk.Label(
            derecha, text="Margen entre actividades (min):", style="Suave.TLabel"
        ).pack(side="left", padx=(0, 5))
        self.spin_margen = ttk.Spinbox(
            derecha,
            from_=0,
            to=240,
            increment=5,
            width=5,
            textvariable=self.var_margen,
            command=self._cambiar_parametros,
        )
        self.spin_margen.pack(side="left")
        self.spin_margen.bind("<Return>", self._cambiar_parametros)
        self.spin_margen.bind("<FocusOut>", self._cambiar_parametros)
        ttk.Separator(derecha, orient="vertical").pack(
            side="left", fill="y", padx=12, pady=2
        )
        ttk.Label(derecha, text="Criterio voraz:", style="Suave.TLabel").pack(
            side="left", padx=(0, 5)
        )
        etiquetas = [nombre for nombre, _ in CRITERIOS.values()]
        self.combo_criterio = ttk.Combobox(
            derecha,
            textvariable=self.var_criterio,
            values=etiquetas,
            state="readonly",
            width=24,
        )
        self.combo_criterio.pack(side="left")
        self.combo_criterio.bind("<<ComboboxSelected>>", self._cambiar_parametros)

    def _boton(
        self, padre: tk.Misc, texto: str, comando, estilo: str = "TButton"
    ) -> ttk.Button:
        return ttk.Button(padre, text=texto, command=comando, style=estilo)


    def _construir_panel_izquierdo(self, padre: ttk.Frame) -> None:
        padre.grid_columnconfigure(0, weight=1)
        padre.grid_rowconfigure(4, weight=1)

        encabezado = ttk.Frame(padre, style="Panel.TFrame")
        encabezado.grid(row=0, column=0, sticky="ew")
        ttk.Label(
            encabezado, text="CONFERENCIAS REGISTRADAS", style="Seccion.TLabel"
        ).pack(side="left")
        ttk.Label(encabezado, textvariable=self.var_conteo, style="Suave.TLabel").pack(
            side="right"
        )

        formulario = ttk.Labelframe(
            padre, text=" Registrar / editar actividad ", padding=(10, 8)
        )
        formulario.grid(row=1, column=0, sticky="ew", pady=(8, 4))
        formulario.grid_columnconfigure(1, weight=1)
        formulario.grid_columnconfigure(3, weight=1)

        ttk.Label(formulario, text="Nombre", style="Panel.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        self.entry_nombre = ttk.Entry(formulario, textvariable=self.var_nombre)
        self.entry_nombre.grid(
            row=0, column=1, columnspan=3, sticky="ew", padx=(8, 0), pady=(0, 4)
        )

        ttk.Label(formulario, text="Inicio", style="Panel.TLabel").grid(
            row=1, column=0, sticky="w", pady=4
        )
        self.entry_inicio = ttk.Entry(formulario, textvariable=self.var_inicio, width=8)
        self.entry_inicio.grid(row=1, column=1, sticky="w", padx=(8, 12), pady=4)
        ttk.Label(formulario, text="Fin", style="Panel.TLabel").grid(
            row=1, column=2, sticky="w", pady=4
        )
        self.entry_fin = ttk.Entry(formulario, textvariable=self.var_fin, width=8)
        self.entry_fin.grid(row=1, column=3, sticky="w", padx=(8, 0), pady=4)

        ttk.Label(formulario, text="Categoría", style="Panel.TLabel").grid(
            row=2, column=0, sticky="w", pady=4
        )
        self.combo_categoria = ttk.Combobox(
            formulario,
            textvariable=self.var_categoria,
            values=list(PALETA_CATEGORIAS.keys()),
            width=18,
        )
        self.combo_categoria.grid(
            row=2, column=1, columnspan=3, sticky="ew", padx=(8, 0), pady=4
        )

        ttk.Label(
            formulario,
            text="Formato de hora HH:MM (00:00 a 24:00). El fin debe ser mayor que el inicio.",
            style="Suave.TLabel",
            wraplength=330,
            justify="left",
        ).grid(row=3, column=0, columnspan=4, sticky="w", pady=(2, 6))

        acciones = ttk.Frame(formulario, style="Panel.TFrame")
        acciones.grid(row=4, column=0, columnspan=4, sticky="ew")
        self.btn_agregar = ttk.Button(
            acciones,
            text="Agregar",
            style="Accent.TButton",
            command=self._agregar_conferencia,
        )
        self.btn_agregar.pack(side="left")
        self.btn_guardar = ttk.Button(
            acciones,
            text="Guardar cambios",
            command=self._guardar_cambios,
            state="disabled",
        )
        self.btn_guardar.pack(side="left", padx=(6, 0))
        ttk.Button(
            acciones, text="Limpiar", command=self._limpiar_formulario
        ).pack(side="left", padx=(6, 0))

        for campo in (self.entry_nombre, self.entry_inicio, self.entry_fin):
            campo.bind("<Return>", self._confirmar_formulario)
            campo.bind("<Escape>", lambda _evento: self._limpiar_formulario())
        self.combo_categoria.bind("<Return>", self._confirmar_formulario)

        marco_arbol = ttk.Frame(padre, style="Panel.TFrame")
        marco_arbol.grid(row=4, column=0, sticky="nsew", pady=(10, 6))
        marco_arbol.grid_rowconfigure(0, weight=1)
        marco_arbol.grid_columnconfigure(0, weight=1)
        self.arbol = ttk.Treeview(
            marco_arbol,
            columns=("numero", "horario", "nombre"),
            show="headings",
            selectmode="browse",
        )
        self.arbol.heading("numero", text="#")
        self.arbol.heading("horario", text="Horario")
        self.arbol.heading("nombre", text="Conferencia")
        self.arbol.column("numero", width=34, anchor="center", stretch=False)
        self.arbol.column("horario", width=104, anchor="center", stretch=False)
        self.arbol.column("nombre", width=262, anchor="w", stretch=True)
        self.arbol.tag_configure("par", background="#F7FAFD")
        self.arbol.tag_configure("impar", background=COLOR_PANEL)
        barra_arbol = ttk.Scrollbar(
            marco_arbol, orient="vertical", command=self.arbol.yview
        )
        self.arbol.configure(yscrollcommand=barra_arbol.set)
        self.arbol.grid(row=0, column=0, sticky="nsew")
        barra_arbol.grid(row=0, column=1, sticky="ns")
        self.arbol.bind("<<TreeviewSelect>>", self._seleccionar_conferencia)
        self.arbol.bind("<Delete>", lambda _evento: self._eliminar_seleccionada())

        pie = ttk.Frame(padre, style="Panel.TFrame")
        pie.grid(row=5, column=0, sticky="ew")
        ttk.Button(
            pie,
            text="Eliminar seleccionada",
            style="Peligro.TButton",
            command=self._eliminar_seleccionada,
        ).pack(side="left")
        ttk.Button(
            pie,
            text="Eliminar todas",
            style="Peligro.TButton",
            command=self._eliminar_todas,
        ).pack(side="left", padx=(6, 0))
        self.arbol.bind("<Double-1>", lambda _evento: self.entry_nombre.focus_set())

    def _construir_panel_derecho(self, padre: ttk.Frame) -> None:
        padre.grid_columnconfigure(0, weight=1)
        padre.grid_rowconfigure(1, weight=1)
        self._construir_estadisticas(padre)
        self._construir_linea_tiempo(padre)
        self._construir_notebook(padre)

    def _construir_estadisticas(self, padre: ttk.Frame) -> None:
        marco = ttk.Frame(padre, style="Panel.TFrame")
        marco.grid(row=0, column=0, sticky="ew")
        definiciones = (
            ("salas", "SALAS UTILIZADAS", AZUL_MEDIO),
            ("demanda", "DEMANDA MÁXIMA", ROJO),
            ("actividades", "ACTIVIDADES", VERDE),
            ("tiempo", "TIEMPO DE CÁLCULO", "#5C6B7A"),
        )
        self.tarjetas: dict[str, tuple[tk.Label, tk.Label]] = {}
        for columna, (clave, titulo, color) in enumerate(definiciones):
            marco.grid_columnconfigure(columna, weight=1, uniform="tarjeta")
            self.tarjetas[clave] = self._crear_tarjeta(marco, titulo, color, columna)

    def _crear_tarjeta(
        self, padre: ttk.Frame, titulo: str, color: str, columna: int
    ) -> tuple[tk.Label, tk.Label]:
        tarjeta = tk.Frame(
            padre,
            bg=COLOR_PANEL,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1,
            bd=0,
        )
        tarjeta.grid(
            row=0,
            column=columna,
            sticky="nsew",
            padx=(0 if columna == 0 else 8, 0),
        )
        franja = tk.Frame(tarjeta, bg=color, width=5)
        franja.pack(side="left", fill="y")
        franja.pack_propagate(False)
        contenido = tk.Frame(tarjeta, bg=COLOR_PANEL)
        contenido.pack(side="left", fill="both", expand=True, padx=12, pady=9)
        tk.Label(
            contenido,
            text=titulo,
            bg=COLOR_PANEL,
            fg=GRIS,
            font=(FUENTE, 8, "bold"),
            anchor="w",
        ).pack(fill="x")
        valor = tk.Label(
            contenido,
            text="—",
            bg=COLOR_PANEL,
            fg=color,
            font=self.fuente_valor,
            anchor="w",
        )
        valor.pack(fill="x")
        detalle = tk.Label(
            contenido,
            text="Sin datos",
            bg=COLOR_PANEL,
            fg=GRIS,
            font=(FUENTE, 8),
            anchor="w",
        )
        detalle.pack(fill="x")
        return valor, detalle

    def _construir_linea_tiempo(self, padre: ttk.Frame) -> None:
        marco = tk.Frame(
            padre,
            bg=COLOR_PANEL,
            highlightbackground=COLOR_BORDE,
            highlightthickness=1,
            bd=0,
        )
        marco.grid(row=1, column=0, sticky="nsew", pady=(10, 8))
        marco.grid_rowconfigure(1, weight=1)
        marco.grid_columnconfigure(0, weight=1)

        cabecera = tk.Frame(marco, bg=COLOR_PANEL)
        cabecera.grid(row=0, column=0, sticky="ew", padx=12, pady=(9, 4))
        cabecera.grid_columnconfigure(0, weight=1)
        tk.Label(
            cabecera,
            text="Línea de tiempo por sala",
            bg=COLOR_PANEL,
            fg=AZUL,
            font=(FUENTE, 11, "bold"),
        ).grid(row=0, column=0, sticky="w")
        self.frame_leyenda = tk.Frame(cabecera, bg=COLOR_PANEL)
        self.frame_leyenda.grid(row=0, column=1, sticky="e")

        contenedor = tk.Frame(marco, bg=COLOR_PANEL)
        contenedor.grid(row=1, column=0, sticky="nsew", padx=(8, 4))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        self.canvas_tiempo = tk.Canvas(
            contenedor, bg="#FCFDFE", highlightthickness=0, bd=0, height=250
        )
        self.scroll_y = ttk.Scrollbar(
            contenedor, orient="vertical", command=self.canvas_tiempo.yview
        )
        self.scroll_x = ttk.Scrollbar(
            contenedor, orient="horizontal", command=self.canvas_tiempo.xview
        )
        self.canvas_tiempo.configure(
            yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set
        )
        self.canvas_tiempo.grid(row=0, column=0, sticky="nsew")
        self.scroll_y.grid(row=0, column=1, sticky="ns")
        self.scroll_x.grid(row=1, column=0, sticky="ew")
        self.canvas_tiempo.bind("<Configure>", self._al_redimensionar_canvas)
        self.canvas_tiempo.bind("<MouseWheel>", self._desplazar_vertical)
        self.canvas_tiempo.bind("<Shift-MouseWheel>", self._desplazar_horizontal)
        self.canvas_tiempo.bind("<Left>", lambda _e: self._paso_anterior())
        self.canvas_tiempo.bind("<Right>", lambda _e: self._paso_siguiente())
        self.canvas_tiempo.bind("<space>", lambda _e: self._alternar_reproduccion())
        self.canvas_tiempo.configure(takefocus=True)
        self._construir_controles(marco)

    def _construir_controles(self, marco: tk.Frame) -> None:
        controles = tk.Frame(
            marco, bg="#F7FAFD", highlightbackground=COLOR_BORDE, highlightthickness=1
        )
        controles.grid(row=2, column=0, sticky="ew")
        controles.grid_columnconfigure(1, weight=1)
        fila = tk.Frame(controles, bg="#F7FAFD")
        fila.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(8, 2))
        self.btn_inicio = ttk.Button(
            fila, text="Inicio", command=self._ir_inicio, width=8
        )
        self.btn_inicio.pack(side="left")
        self.btn_anterior = ttk.Button(
            fila, text="Anterior", command=self._paso_anterior, width=9
        )
        self.btn_anterior.pack(side="left", padx=(5, 0))
        self.btn_play = ttk.Button(
            fila,
            text="Reproducir",
            style="Accent.TButton",
            command=self._alternar_reproduccion,
            width=11,
        )
        self.btn_play.pack(side="left", padx=(5, 0))
        self.btn_siguiente = ttk.Button(
            fila, text="Siguiente", command=self._paso_siguiente, width=9
        )
        self.btn_siguiente.pack(side="left", padx=(5, 0))
        self.btn_final = ttk.Button(
            fila, text="Final", command=self._ir_final, width=7
        )
        self.btn_final.pack(side="left", padx=(5, 0))

        velocidad = tk.Frame(fila, bg="#F7FAFD")
        velocidad.pack(side="right")
        tk.Label(
            velocidad,
            text="Velocidad",
            bg="#F7FAFD",
            fg=GRIS,
            font=(FUENTE, 8, "bold"),
        ).pack(side="left", padx=(0, 4))
        ttk.Scale(
            velocidad,
            from_=1,
            to=10,
            orient="horizontal",
            variable=self.var_velocidad,
            length=92,
        ).pack(side="left")

        self.var_paso_label = tk.StringVar(value="Paso 0 de 0")
        self.var_escala.set(0)
        self.scale_paso = ttk.Scale(
            controles,
            from_=0,
            to=1,
            orient="horizontal",
            variable=self.var_escala,
            command=self._cambiar_paso_escala,
        )
        self.scale_paso.grid(row=1, column=0, sticky="ew", padx=(12, 8), pady=2)
        tk.Label(
            controles,
            textvariable=self.var_paso_label,
            bg="#F7FAFD",
            fg=AZUL,
            font=(FUENTE, 9, "bold"),
            width=22,
            anchor="e",
        ).grid(row=1, column=1, sticky="e", padx=(0, 12))

        self.lbl_explicacion = tk.Label(
            controles,
            text="Carga o registra actividades para comenzar.",
            bg=AZUL_CLARO,
            fg=TEXTO,
            font=(FUENTE, 9),
            anchor="w",
            justify="left",
            padx=12,
            pady=7,
            wraplength=900,
        )
        self.lbl_explicacion.grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(2, 8)
        )
        controles.bind("<Configure>", self._ajustar_wraplength)

    def _construir_notebook(self, padre: ttk.Frame) -> None:
        self.notebook = ttk.Notebook(padre, height=190)
        self.notebook.grid(row=2, column=0, sticky="ew")
        self._construir_pestana_asignaciones()
        self._construir_pestana_comparacion()
        self._construir_pestana_analisis()

    def _construir_pestana_asignaciones(self) -> None:
        pestana = ttk.Frame(self.notebook, style="Panel.TFrame", padding=(10, 8))
        pestana.grid_rowconfigure(0, weight=1)
        pestana.grid_columnconfigure(0, weight=1)
        self.notebook.add(pestana, text="  Asignación paso a paso  ")
        self.tabla_asignaciones = ttk.Treeview(
            pestana,
            columns=("paso", "conferencia", "categoria", "horario", "sala", "estado"),
            show="headings",
            selectmode="browse",
            height=6,
        )
        titulos = (
            ("paso", "#", 44, "center"),
            ("conferencia", "Conferencia", 330, "w"),
            ("categoria", "Categoría", 120, "w"),
            ("horario", "Horario", 120, "center"),
            ("sala", "Sala", 90, "center"),
            ("estado", "Estado", 100, "center"),
        )
        for clave, titulo, ancho, alineacion in titulos:
            self.tabla_asignaciones.heading(clave, text=titulo)
            self.tabla_asignaciones.column(
                clave, width=ancho, anchor=alineacion, stretch=(clave == "conferencia")
            )
        self.tabla_asignaciones.tag_configure(
            "pendiente", foreground="#93A2B1", background="#FBFCFE"
        )
        self.tabla_asignaciones.tag_configure("asignada", background=COLOR_PANEL)
        self.tabla_asignaciones.tag_configure("actual", background="#FFF6D9")
        barra = ttk.Scrollbar(
            pestana, orient="vertical", command=self.tabla_asignaciones.yview
        )
        self.tabla_asignaciones.configure(yscrollcommand=barra.set)
        self.tabla_asignaciones.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")

    def _construir_pestana_comparacion(self) -> None:
        pestana = ttk.Frame(self.notebook, style="Panel.TFrame", padding=(10, 8))
        pestana.grid_rowconfigure(0, weight=1)
        pestana.grid_columnconfigure(0, weight=1)
        pestana.grid_columnconfigure(1, weight=1)
        self.notebook.add(pestana, text="  Comparación de criterios  ")

        tabla_marco = ttk.Frame(pestana, style="Panel.TFrame")
        tabla_marco.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tabla_marco.grid_rowconfigure(0, weight=1)
        tabla_marco.grid_columnconfigure(0, weight=1)
        self.tabla_comparacion = ttk.Treeview(
            tabla_marco,
            columns=("estrategia", "salas", "optima", "tiempo"),
            show="headings",
            selectmode="browse",
            height=6,
        )
        for clave, titulo, ancho, alineacion in (
            ("estrategia", "Orden de selección", 235, "w"),
            ("salas", "Salas", 58, "center"),
            ("optima", "¿Óptima?", 70, "center"),
            ("tiempo", "Tiempo (ms)", 85, "center"),
        ):
            self.tabla_comparacion.heading(clave, text=titulo)
            self.tabla_comparacion.column(
                clave, width=ancho, anchor=alineacion, stretch=(clave == "estrategia")
            )
        self.tabla_comparacion.tag_configure("optima", background=VERDE_CLARO)
        self.tabla_comparacion.tag_configure("suboptima", background="#FFF4E2")
        self.tabla_comparacion.tag_configure("actual", background=AZUL_CLARO)
        barra = ttk.Scrollbar(
            tabla_marco, orient="vertical", command=self.tabla_comparacion.yview
        )
        self.tabla_comparacion.configure(yscrollcommand=barra.set)
        self.tabla_comparacion.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")

        self.canvas_comparacion = tk.Canvas(
            pestana,
            bg=COLOR_PANEL,
            highlightthickness=1,
            highlightbackground=COLOR_BORDE,
            height=190,
        )
        self.canvas_comparacion.grid(row=0, column=1, sticky="nsew")
        self.canvas_comparacion.bind("<Configure>", self._dibujar_comparacion)

    def _construir_pestana_analisis(self) -> None:
        pestana = ttk.Frame(self.notebook, style="Panel.TFrame", padding=(8, 6))
        pestana.grid_rowconfigure(0, weight=1)
        pestana.grid_columnconfigure(0, weight=1)
        self.notebook.add(pestana, text="  Diseño, análisis y bitácora  ")
        self.texto_analisis = tk.Text(
            pestana,
            wrap="word",
            bg=COLOR_PANEL,
            fg=TEXTO,
            relief="flat",
            bd=0,
            font=(FUENTE, 9),
            padx=10,
            pady=6,
            spacing1=1,
            spacing3=2,
            height=7,
        )
        barra = ttk.Scrollbar(
            pestana, orient="vertical", command=self.texto_analisis.yview
        )
        self.texto_analisis.configure(yscrollcommand=barra.set)
        self.texto_analisis.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")
        self.texto_analisis.tag_configure(
            "titulo", font=(FUENTE, 10, "bold"), foreground=AZUL, spacing1=6
        )
        self.texto_analisis.tag_configure(
            "subtitulo", font=(FUENTE, 9, "bold"), foreground=AZUL_MEDIO, spacing1=4
        )
        self.texto_analisis.tag_configure("ok", foreground="#1E7B45")
        self.texto_analisis.tag_configure("alerta", foreground="#A2601A")
        self.texto_analisis.tag_configure("error", foreground="#9B2C28")
        self.texto_analisis.tag_configure("mono", font=("Consolas", 9))
        self.texto_analisis.configure(state="disabled")

    def _construir_barra_estado(self) -> None:
        barra = tk.Frame(self, bg="#DCE5EE", height=28)
        barra.grid(row=3, column=0, sticky="ew")
        barra.grid_propagate(False)
        tk.Label(
            barra,
            textvariable=self.var_estado,
            bg="#DCE5EE",
            fg=AZUL,
            font=(FUENTE, 9),
            anchor="w",
            padx=18,
        ).pack(side="left", fill="y")
        tk.Label(
            barra,
            text="Clic en la línea de tiempo: ← / → paso · Espacio reproducir · Ctrl+O importar · Ctrl+S exportar",
            bg="#DCE5EE",
            fg=GRIS,
            font=(FUENTE, 8),
            anchor="e",
            padx=18,
        ).pack(side="right", fill="y")


    # ------------------------------------------------------------------
    # Parámetros y recálculo
    # ------------------------------------------------------------------
    def _configurar_atajos(self) -> None:
        self.bind_all("<Control-o>", lambda _evento: self._importar_csv())
        self.bind_all("<Control-s>", lambda _evento: self._exportar_csv())
        self.bind_all("<Control-r>", lambda _evento: self._generar_aleatorio())
        self.bind_all("<Control-e>", lambda _evento: self._cargar_ejemplo())

    def _cerrar(self) -> None:
        self._detener_reproduccion()
        self.destroy()

    def _mensaje(self, texto: str) -> None:
        self.var_estado.set(texto)

    def _criterio_actual(self) -> str:
        etiqueta = self.var_criterio.get()
        for clave, (nombre, _funcion) in CRITERIOS.items():
            if nombre == etiqueta:
                return clave
        return "inicio"

    def _margen(self) -> int:
        texto = self.var_margen.get().strip().replace(",", ".")
        try:
            valor = int(round(float(texto)))
        except (TypeError, ValueError):
            valor = self.margen_actual
        valor = max(0, min(240, valor))
        self.margen_actual = valor
        self.var_margen.set(str(valor))
        return valor

    def _cambiar_parametros(self, _evento=None) -> None:
        criterio = self._criterio_actual()
        margen = self._margen()
        if (criterio, margen) == self._parametros_actuales and self.resultado is not None:
            return
        self._recalcular(
            f"Parámetros actualizados: {nombre_criterio(criterio)} · margen {margen} min."
        )

    def _recalcular(self, mensaje: str = "") -> None:
        self._detener_reproduccion()
        criterio = self._criterio_actual()
        margen = self._margen()
        self._parametros_actuales = (criterio, margen)
        if not self.conferencias:
            self.resultado = None
            self.comparaciones = ()
            self.indice_paso = -1
            self._actualizar_todo()
        else:
            try:
                self.resultado = asignar_salas(
                    self.conferencias, criterio=criterio, margen=margen
                )
                self.comparaciones = comparar_estrategias(
                    self.conferencias, margen=margen
                )
            except (ErrorConferencia, ValueError) as exc:
                self.resultado = None
                self.comparaciones = ()
                self.indice_paso = -1
                self._actualizar_todo()
                messagebox.showerror(
                    "No fue posible calcular la asignación", str(exc), parent=self
                )
                self._mensaje("Error en los datos: corrige las actividades marcadas.")
                return
            self.indice_paso = len(self.resultado.pasos) - 1
            self._actualizar_todo()
        if mensaje:
            self._mensaje(mensaje)

    def _actualizar_todo(self) -> None:
        self._actualizar_tabla_conferencias()
        self._actualizar_estadisticas()
        self._actualizar_leyenda()
        self._actualizar_comparacion()
        self._actualizar_analisis()
        self._actualizar_visualizacion()


    # ------------------------------------------------------------------
    # Actualización de datos y paneles
    # ------------------------------------------------------------------
    def _actualizar_tabla_conferencias(self) -> None:
        self.arbol.delete(*self.arbol.get_children())
        self._mapa_arbol.clear()
        total_horas = sum(c.duracion for c in self.conferencias) / 60.0
        prefijo = "1 actividad" if len(self.conferencias) == 1 else f"{len(self.conferencias)} actividades"
        self.var_conteo.set(f"{prefijo} · {total_horas:.1f} h")
        for posicion, conferencia in enumerate(self.conferencias, start=1):
            iid = f"fila{posicion}"
            self._mapa_arbol[iid] = conferencia.id
            self.arbol.insert(
                "",
                "end",
                iid=iid,
                values=(f"{posicion:02d}", conferencia.horario, conferencia.nombre),
                tags=("par" if posicion % 2 else "impar",),
            )

    def _actualizar_estadisticas(self) -> None:
        resultado = self.resultado
        if resultado is None:
            for valor, detalle in self.tarjetas.values():
                valor.configure(text="—")
                detalle.configure(text="Sin datos")
            return
        salas, salas_detalle = self.tarjetas["salas"]
        salas.configure(text=str(resultado.total_salas))
        salas_detalle.configure(
            text=("Solución óptima" if resultado.es_optimo else "Heurística no óptima")
        )
        demanda, demanda_detalle = self.tarjetas["demanda"]
        demanda.configure(text=str(resultado.demanda.cantidad))
        demanda_detalle.configure(text=resultado.demanda.horario)
        actividades, actividades_detalle = self.tarjetas["actividades"]
        actividades.configure(text=str(len(resultado.conferencias)))
        horas = sum(c.duracion for c in resultado.conferencias) / 60.0
        actividades_detalle.configure(text=f"{horas:.1f} h programadas")
        tiempo, tiempo_detalle = self.tarjetas["tiempo"]
        tiempo.configure(text=f"{resultado.tiempo_ms:.2f} ms")
        tiempo_detalle.configure(text="Asignación + demanda")

    def _agregar_leyenda(self, texto: str, color: str, contorno: bool = False) -> None:
        elemento = tk.Frame(self.frame_leyenda, bg=COLOR_PANEL)
        elemento.pack(side="left", padx=(0, 10))
        muestra = tk.Label(
            elemento,
            text="   ",
            bg=COLOR_PANEL if contorno else color,
            highlightbackground=color,
            highlightthickness=2 if contorno else 0,
            bd=0,
        )
        muestra.pack(side="left")
        tk.Label(
            elemento,
            text=texto,
            bg=COLOR_PANEL,
            fg=GRIS,
            font=(FUENTE, 8),
        ).pack(side="left", padx=(4, 0))

    def _actualizar_leyenda(self) -> None:
        for hijo in self.frame_leyenda.winfo_children():
            hijo.destroy()
        self._agregar_leyenda("Color = categoría", "#7A5AF8")
        pico = self.resultado.demanda.cantidad if self.resultado else 0
        self._agregar_leyenda(f"Zona roja = pico ({pico})", ROJO_CLARO)
        self._agregar_leyenda("Borde dorado = paso actual", AMARILLO, contorno=True)
        self._agregar_leyenda("Clic en un bloque = detalle", COLOR_BORDE)

    def _actualizar_comparacion(self) -> None:
        self.tabla_comparacion.delete(*self.tabla_comparacion.get_children())
        actual = self._criterio_actual()
        for indice, resumen in enumerate(self.comparaciones, start=1):
            etiqueta = resumen.nombre + (" ◀" if resumen.clave == actual else "")
            if resumen.clave == actual:
                etiqueta_fila = "actual"
            elif resumen.es_optima:
                etiqueta_fila = "optima"
            else:
                etiqueta_fila = "suboptima"
            self.tabla_comparacion.insert(
                "",
                "end",
                iid=f"comparacion{indice}",
                values=(
                    etiqueta,
                    resumen.salas,
                    "Sí" if resumen.es_optima else "No",
                    f"{resumen.tiempo_ms:.2f}",
                ),
                tags=(etiqueta_fila,),
            )
        self._dibujar_comparacion()


    def _dibujar_comparacion(self, _evento=None) -> None:
        lienzo = self.canvas_comparacion
        lienzo.delete("all")
        ancho = lienzo.winfo_width()
        alto = lienzo.winfo_height()
        if ancho < 80 or alto < 60:
            return
        if not self.comparaciones:
            lienzo.create_text(
                ancho / 2,
                alto / 2,
                text="Sin datos para comparar",
                fill=GRIS,
                font=(FUENTE, 9),
            )
            return
        maximo = max(resumen.salas for resumen in self.comparaciones) or 1
        margen_izq = min(190, max(135, int(ancho * 0.30)))
        margen_der = 48
        disponible = max(40, ancho - margen_izq - margen_der)
        cantidad = len(self.comparaciones)
        alto_fila = min(30.0, max(16.0, (alto - 28) / cantidad))
        actual = self._criterio_actual()
        etiquetas_cortas = {
            "inicio": "Hora de inicio",
            "original": "Orden de registro",
            "duracion": "Duración ascendente",
            "fin": "Fin ascendente",
            "inicio_desc": "Inicio descendente",
        }
        lienzo.create_text(
            margen_izq,
            12,
            text="Salas necesarias según el orden de selección",
            anchor="w",
            fill=AZUL,
            font=(FUENTE, 8, "bold"),
        )
        for indice, resumen in enumerate(self.comparaciones):
            y = 24 + indice * alto_fila
            color = VERDE if resumen.es_optima else NARANJA
            nombre = etiquetas_cortas.get(resumen.clave, resumen.nombre)
            if len(nombre) > 22:
                nombre = nombre[:20] + "…"
            lienzo.create_text(
                margen_izq - 8,
                y + alto_fila / 2,
                text=nombre,
                anchor="e",
                fill=TEXTO,
                font=(FUENTE, 8),
            )
            ancho_barra = max(4.0, disponible * resumen.salas / maximo)
            alto_barra = max(8.0, alto_fila - 8)
            lienzo.create_rectangle(
                margen_izq,
                y + 3,
                margen_izq + ancho_barra,
                y + 3 + alto_barra,
                fill=color,
                outline=AZUL_MEDIO if resumen.clave == actual else "",
                width=2 if resumen.clave == actual else 1,
            )
            lienzo.create_text(
                margen_izq + ancho_barra + 6,
                y + alto_fila / 2,
                text=f"{resumen.salas}",
                anchor="w",
                fill=AZUL if resumen.es_optima else "#A2601A",
                font=(FUENTE, 8, "bold"),
            )

    def _actualizar_analisis(self) -> None:
        self.texto_analisis.configure(state="normal")
        self.texto_analisis.delete("1.0", "end")

        def escribir(texto: str, etiqueta: str | None = None) -> None:
            self.texto_analisis.insert("end", texto, etiqueta or ())

        escribir("DISEÑO DEL ALGORITMO VORAZ (PARTICIÓN DE INTERVALOS)\n", "titulo")
        escribir(
            "Candidatos: las n conferencias, cada una con hora de inicio y fin. "
            "Solución: una asignación (conferencia, sala) sin solapamientos. "
            "Función objetivo: minimizar el número de salas.\n"
        )
        escribir(
            "Selección voraz: tomar la conferencia con menor hora de inicio. "
            "Factibilidad: la sala elegida debe estar libre; con margen m se exige "
            "fin + m ≤ siguiente inicio. Inserción: asignar y actualizar la hora de "
            "liberación. Terminación: cuando no quedan conferencias pendientes.\n"
        )
        escribir(
            "Estructuras: lista de conferencias, ordenamiento estable (Timsort), "
            "cola de prioridad min-heap (heapq) con (hora de liberación, sala) y "
            "diccionario de asignaciones por sala.\n",
            "subtitulo",
        )
        escribir(
            "Complejidad: ordenar cuesta O(n log n); cada conferencia se inserta y "
            "extrae del heap una vez, O(n log n) en total. Memoria: O(n). "
            "El barrido de demanda máxima también es O(n log n).\n"
        )
        escribir(
            "Optimalidad: como cada nueva sala solo se crea cuando todas las "
            "existentes están ocupadas, el número de salas iguala la demanda máxima "
            "simultánea; ninguna solución puede usar menos. El orden por hora de "
            "inicio es, por tanto, óptimo para este problema.\n",
            "ok",
        )

        resultado = self.resultado
        escribir("\nEJECUCIÓN ACTUAL\n", "titulo")
        if resultado is None:
            escribir("No hay conferencias registradas.\n", "alerta")

        else:
            escribir(
                f"Conferencias: {len(resultado.conferencias)} · "
                f"Salas utilizadas: {resultado.total_salas} · "
                f"Demanda máxima: {resultado.demanda.cantidad} "
                f"({resultado.demanda.horario}) · "
                f"Margen: {resultado.margen} min · "
                f"Tiempo: {resultado.tiempo_ms:.3f} ms\n"
            )
            errores = validar_asignacion(resultado)
            if errores:
                escribir("Validación: " + " ".join(errores) + "\n", "error")
            else:
                escribir(
                    "Validación: sin conflictos; todas las conferencias fueron "
                    "asignadas exactamente una vez.\n",
                    "ok",
                )
            if resultado.es_optimo:
                escribir(
                    "Resultado: ÓPTIMO. El número de salas coincide con la demanda "
                    "máxima, que es una cota inferior imposible de mejorar.\n",
                    "ok",
                )
            else:
                escribir(
                    "Resultado: no óptimo. Este criterio de orden produce una "
                    "heurística; el criterio por hora de inicio sí alcanza la cota.\n",
                    "alerta",
                )
            if resultado.demanda.conferencias:
                escribir(
                    "Actividades simultáneas en el pico: "
                    + ", ".join(resultado.demanda.conferencias)
                    + "\n"
                )

            escribir("\nCOMPARACIÓN DE CRITERIOS DE ORDEN\n", "titulo")
            for resumen in self.comparaciones:
                marca = "óptima" if resumen.es_optima else "no óptima"
                escribir(
                    f"- {resumen.nombre}: {resumen.salas} sala(s), "
                    f"{marca}, {resumen.tiempo_ms:.2f} ms\n"
                )

            escribir("\nBITÁCORA DE DECISIONES\n", "titulo")
            for paso in resultado.pasos:
                origen = "reutilizada" if paso.reutilizada else "nueva"
                linea = (
                    f"{paso.numero:02d}. {paso.conferencia.horario} · "
                    f"{paso.conferencia.nombre} → {paso.nombre_sala} ({origen})."
                )
                if paso.solapamientos:
                    linea += " Simultáneas: " + ", ".join(paso.solapamientos) + "."
                escribir(linea + "\n", "mono")

        self.texto_analisis.configure(state="disabled")
        self.texto_analisis.see("1.0")


    # ------------------------------------------------------------------
    # Ejecución paso a paso y reproducción automática
    # ------------------------------------------------------------------
    def _paso_actual(self):
        if self.resultado and 0 <= self.indice_paso < len(self.resultado.pasos):
            return self.resultado.pasos[self.indice_paso]
        return None

    def _actualizar_visualizacion(self) -> None:
        self._actualizar_controles_paso()
        self._actualizar_tabla_asignaciones()
        self._dibujar_linea_tiempo()

    def _actualizar_controles_paso(self) -> None:
        total = len(self.resultado.pasos) if self.resultado else 0
        paso = self._paso_actual()
        if total == 0:
            self.var_paso_label.set("Paso 0 de 0")
        elif paso is None:
            self.var_paso_label.set(f"Paso 0 de {total}")
        else:
            self.var_paso_label.set(f"Paso {paso.numero} de {total}")
        self._actualizando_escala = True
        try:
            self.scale_paso.configure(from_=0, to=max(1, total))
            self.var_escala.set(0 if paso is None else paso.numero)
        finally:
            self._actualizando_escala = False
        al_inicio = paso is None
        al_final = total > 0 and self.indice_paso >= total - 1
        self.btn_inicio.configure(
            state="disabled" if al_inicio or total == 0 else "normal"
        )
        self.btn_anterior.configure(
            state="disabled" if al_inicio or total == 0 else "normal"
        )
        self.btn_siguiente.configure(
            state="disabled" if al_final or total == 0 else "normal"
        )
        self.btn_final.configure(
            state="disabled" if al_final or total == 0 else "normal"
        )
        self.btn_play.configure(state="normal" if total else "disabled")
        self.btn_play.configure(text="Pausar" if self.reproduciendo else "Reproducir")

        if self.resultado is None:
            texto = "Registra actividades o carga el conjunto de ejemplo para comenzar."
        elif paso is None:
            texto = (
                f"Estado inicial: {total} conferencias pendientes y ninguna sala "
                "ocupada. Pulsa «Siguiente» para ejecutar la primera decisión voraz."
            )
        else:
            accion = "reutiliza" if paso.reutilizada else "abre"
            texto = (
                f"Paso {paso.numero} de {total}: «{paso.conferencia.nombre}» "
                f"({paso.conferencia.horario}) {accion} {paso.nombre_sala}."
            )
            if paso.solapamientos:
                texto += (
                    f" Se cruza con {len(paso.solapamientos)} actividad(es) ya "
                    "programada(s) en otras salas."
                )
            else:
                texto += " No se solapa con actividades ya programadas."
            if self.indice_paso >= total - 1:
                demanda = self.resultado.demanda
                texto += (
                    f" Solución completa: {self.resultado.total_salas} sala(s); "
                    f"demanda máxima {demanda.cantidad} ({demanda.horario}). "
                    f"{'Es óptima.' if self.resultado.es_optimo else 'No es óptima.'}"
                )
        self.lbl_explicacion.configure(text=texto)

    def _cambiar_paso_escala(self, valor) -> None:
        if self._actualizando_escala or self.resultado is None:
            return
        total = len(self.resultado.pasos)
        if total == 0:
            return
        posicion = int(round(float(valor)))
        nuevo = -1 if posicion <= 0 else min(total - 1, posicion - 1)
        if nuevo == self.indice_paso:
            return
        self._detener_reproduccion()
        self.indice_paso = nuevo
        self._actualizar_visualizacion()

    def _ir_inicio(self) -> None:
        if self.resultado is None:
            return
        self._detener_reproduccion()
        self.indice_paso = -1
        self._actualizar_visualizacion()
        self._mensaje("Vista inicial: aún no se ha tomado ninguna decisión.")

    def _paso_anterior(self) -> None:
        if self.resultado is None:
            return
        self._detener_reproduccion()
        if self.indice_paso >= 0:
            self.indice_paso -= 1
            self._actualizar_visualizacion()
            self._mensaje(
                "Paso anterior."
                if self.indice_paso >= 0
                else "Vista inicial: aún no se ha tomado ninguna decisión."
            )

    def _paso_siguiente(self) -> None:
        if self.resultado is None:
            return
        self._detener_reproduccion()
        total = len(self.resultado.pasos)
        if self.indice_paso < total - 1:
            self.indice_paso += 1
            self._actualizar_visualizacion()
            self._mensaje(f"Paso {self.indice_paso + 1} de {total} ejecutado.")
        else:
            self._mensaje("La solución ya está completa.")


    def _ir_final(self) -> None:
        if self.resultado is None or not self.resultado.pasos:
            return
        self._detener_reproduccion()
        self.indice_paso = len(self.resultado.pasos) - 1
        self._actualizar_visualizacion()
        self._mensaje(self.resultado.resumen())

    def _alternar_reproduccion(self) -> None:
        if self.reproduciendo:
            self._detener_reproduccion()
            self._mensaje("Reproducción pausada.")
            self._actualizar_controles_paso()
            return
        if self.resultado is None or not self.resultado.pasos:
            return
        if self.indice_paso >= len(self.resultado.pasos) - 1:
            self.indice_paso = -1
            self._actualizar_visualizacion()
        self.reproduciendo = True
        self.btn_play.configure(text="Pausar")
        self._mensaje("Reproducción automática en curso…")
        self._programar_reproduccion()

    def _programar_reproduccion(self) -> None:
        velocidad = max(1.0, min(10.0, float(self.var_velocidad.get())))
        retardo = max(120, int(1400 / velocidad))
        self._after_reproduccion = self.after(retardo, self._siguiente_automatico)

    def _siguiente_automatico(self) -> None:
        self._after_reproduccion = None
        if not self.reproduciendo or self.resultado is None:
            return
        total = len(self.resultado.pasos)
        if self.indice_paso >= total - 1:
            self.reproduciendo = False
            self._actualizar_visualizacion()
            self._mensaje("Reproducción finalizada: solución completa.")
            return
        self.indice_paso += 1
        if self.indice_paso >= total - 1:
            self.reproduciendo = False
        self._actualizar_visualizacion()
        if self.reproduciendo:
            self._programar_reproduccion()
        else:
            self._mensaje("Reproducción finalizada: solución completa.")

    def _detener_reproduccion(self) -> None:
        if self._after_reproduccion is not None:
            try:
                self.after_cancel(self._after_reproduccion)
            except tk.TclError:
                pass
            self._after_reproduccion = None
        if self.reproduciendo:
            self.reproduciendo = False
            if hasattr(self, "btn_play"):
                self.btn_play.configure(text="Reproducir")

    def _desplazar_vertical(self, evento) -> None:
        self.canvas_tiempo.yview_scroll(int(-evento.delta / 120), "units")

    def _desplazar_horizontal(self, evento) -> None:
        self.canvas_tiempo.xview_scroll(int(-evento.delta / 120), "units")

    def _al_redimensionar_canvas(self, evento) -> None:
        if abs(evento.width - self._ancho_canvas) > 16:
            self._ancho_canvas = evento.width
            self._dibujar_linea_tiempo()

    def _ajustar_wraplength(self, evento) -> None:
        objetivo = max(400, evento.width - 40)
        actual = int(self.lbl_explicacion.cget("wraplength"))
        if abs(actual - objetivo) > 8:
            self.lbl_explicacion.configure(wraplength=objetivo)


    # ------------------------------------------------------------------
    # Tabla de asignaciones y línea de tiempo
    # ------------------------------------------------------------------
    def _actualizar_tabla_asignaciones(self) -> None:
        self.tabla_asignaciones.delete(*self.tabla_asignaciones.get_children())
        resultado = self.resultado
        if resultado is None:
            return
        paso = self._paso_actual()
        visibles = self.indice_paso + 1
        for posicion, conferencia in enumerate(resultado.orden, start=1):
            asignacion = resultado.asignacion_de(conferencia.id)
            asignada = posicion <= visibles
            sala = asignacion.nombre_sala if asignada and asignacion else "—"
            estado = "Asignada" if asignada else "Pendiente"
            if paso is not None and conferencia.id == paso.conferencia.id:
                etiqueta = "actual"
            elif asignada:
                etiqueta = "asignada"
            else:
                etiqueta = "pendiente"
            self.tabla_asignaciones.insert(
                "",
                "end",
                iid=f"asignacion{posicion}",
                values=(
                    posicion,
                    conferencia.nombre,
                    conferencia.categoria,
                    conferencia.horario,
                    sala,
                    estado,
                ),
                tags=(etiqueta,),
            )
        if paso is not None:
            try:
                self.tabla_asignaciones.see(f"asignacion{self.indice_paso + 1}")
            except tk.TclError:
                pass

    def _estado_sala(self, sala: int, visibles, paso) -> str:
        if self.resultado is None:
            return "SIN USO"
        if paso is None:
            usada = any(a.sala == sala for a in self.resultado.asignaciones)
            return "LIBRE" if usada else "SIN USO"
        instante = paso.conferencia.inicio
        for asignacion in visibles:
            if asignacion.sala != sala:
                continue
            conferencia = asignacion.conferencia
            if conferencia.inicio <= instante < conferencia.fin + self.resultado.margen:
                return "OCUPADA"
        if any(a.sala == sala for a in visibles):
            return "LIBRE"
        return "SIN USO"

    def _rectangulo_redondeado(
        self, x1: float, y1: float, x2: float, y2: float, radio: float = 6, **opciones
    ) -> int:
        r = max(1.0, min(radio, (x2 - x1) / 2, (y2 - y1) / 2))
        puntos = (
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
        )
        return self.canvas_tiempo.create_polygon(
            puntos, smooth=True, splinesteps=12, **opciones
        )

    @staticmethod
    def _recortar(texto: str, maximo: int) -> str:
        if maximo <= 1:
            return ""
        if len(texto) <= maximo:
            return texto
        return texto[: maximo - 1].rstrip() + "…"

    def _mostrar_detalle(self, conferencia: Conferencia) -> None:
        if self.resultado is None:
            return
        asignacion = self.resultado.asignacion_de(conferencia.id)
        paso = next(
            (
                registro
                for registro in self.resultado.pasos
                if registro.conferencia.id == conferencia.id
            ),
            None,
        )
        partes = [
            conferencia.nombre,
            f"{conferencia.horario} · {conferencia.categoria}",
        ]
        if asignacion is not None:
            partes.append(f"Asignada a {asignacion.nombre_sala}")
        if paso is not None:
            partes.append(
                f"Paso {paso.numero}: "
                + ("sala reutilizada" if paso.reutilizada else "sala nueva")
            )
        self._mensaje(" · ".join(partes))


    def _dibujar_linea_tiempo(self) -> None:
        lienzo = self.canvas_tiempo
        lienzo.delete("all")
        ancho = max(600, lienzo.winfo_width())
        alto = max(200, lienzo.winfo_height())
        resultado = self.resultado
        if resultado is None or not resultado.conferencias:
            lienzo.configure(scrollregion=(0, 0, ancho, alto))
            lienzo.create_text(
                ancho / 2,
                alto / 2,
                text=(
                    "Sin actividades para mostrar.\n"
                    "Registra una conferencia, importa un CSV o carga el ejemplo."
                ),
                fill=GRIS,
                font=(FUENTE, 11),
                justify="center",
            )
            return

        margen_izq = 112
        alto_cabecera = 26
        alto_fila = 42
        alto_bloque = 30
        total_salas = max(1, resultado.total_salas)
        visibles_cantidad = max(
            0, min(self.indice_paso + 1, len(resultado.pasos))
        )
        ids_visibles = {
            registro.conferencia.id
            for registro in resultado.pasos[:visibles_cantidad]
        }
        visibles = [
            asignacion
            for asignacion in resultado.asignaciones
            if asignacion.conferencia.id in ids_visibles
        ]
        paso = self._paso_actual()
        pendientes = [
            conferencia
            for conferencia in resultado.orden
            if conferencia.id not in ids_visibles
        ]
        inicio_eje = max(
            0, (min(c.inicio for c in resultado.conferencias) // 60) * 60 - 15
        )
        fin_eje = min(
            1440,
            ((max(c.fin for c in resultado.conferencias) + 59) // 60) * 60 + 15,
        )
        if fin_eje - inicio_eje < 90:
            fin_eje = min(1440, inicio_eje + 90)
        ancho_util = max(480, ancho - margen_izq - 45)
        px = max(0.45, ancho_util / max(1, fin_eje - inicio_eje))
        ancho_total = margen_izq + int((fin_eje - inicio_eje) * px) + 30
        filas = total_salas + (1 if pendientes else 0)
        alto_total = alto_cabecera + filas * alto_fila + 6
        lienzo.configure(
            scrollregion=(0, 0, max(ancho, ancho_total), max(alto, alto_total))
        )

        def x(minuto: int) -> float:
            return margen_izq + 10 + (minuto - inicio_eje) * px

        # Cabecera y eje de tiempo.
        lienzo.create_rectangle(
            0, 0, ancho_total, alto_cabecera, fill="#EDF3F9", outline=""
        )
        lienzo.create_line(0, alto_cabecera, ancho_total, alto_cabecera, fill=COLOR_BORDE)
        lienzo.create_line(margen_izq, 0, margen_izq, alto_total, fill=COLOR_BORDE)
        lienzo.create_text(
            12,
            alto_cabecera / 2,
            text="SALA",
            anchor="w",
            fill=GRIS,
            font=(FUENTE, 7, "bold"),
        )
        paso_etiqueta = 60
        for candidato in (120, 60, 30, 15, 10, 5):
            if candidato * px >= 58:
                paso_etiqueta = candidato
                break
        primer_tick = ((inicio_eje + paso_etiqueta - 1) // paso_etiqueta) * paso_etiqueta
        for instante in range(primer_tick, fin_eje + 1, paso_etiqueta):
            xp = x(instante)
            lienzo.create_line(
                xp, alto_cabecera - 6, xp, alto_cabecera, fill="#AEBBC8"
            )
            lienzo.create_line(
                xp, alto_cabecera, xp, alto_total - 10, fill="#E7EEF6"
            )
            lienzo.create_text(
                xp,
                alto_cabecera / 2,
                text=minutos_a_hhmm(instante),
                fill=GRIS,
                font=(FUENTE, 7, "bold" if instante % 60 == 0 else "normal"),
            )

        # Filas de salas.
        for indice in range(total_salas):
            y0 = alto_cabecera + indice * alto_fila
            if indice % 2 == 1:
                lienzo.create_rectangle(
                    0, y0, ancho_total, y0 + alto_fila, fill="#FAFCFE", outline=""
                )
            estado = self._estado_sala(indice + 1, visibles, paso)
            color_estado = {
                "OCUPADA": "#B03A36",
                "LIBRE": VERDE,
                "SIN USO": "#9AA8B6",
            }[estado]
            lienzo.create_text(
                12,
                y0 + 14,
                text=f"Sala {indice + 1}",
                anchor="w",
                fill=TEXTO,
                font=(FUENTE, 9, "bold"),
            )
            lienzo.create_text(
                12,
                y0 + 29,
                text=estado,
                anchor="w",
                fill=color_estado,
                font=(FUENTE, 7, "bold"),
            )
        if pendientes:
            y0 = alto_cabecera + total_salas * alto_fila
            lienzo.create_rectangle(
                0, y0, ancho_total, y0 + alto_fila, fill="#F5F7FA", outline=""
            )
            lienzo.create_text(
                12,
                y0 + 14,
                text="PENDIENTES",
                anchor="w",
                fill="#8A6D3B",
                font=(FUENTE, 7, "bold"),
            )
            lienzo.create_text(
                12,
                y0 + 29,
                text=f"{len(pendientes)}",
                anchor="w",
                fill="#8A6D3B",
                font=(FUENTE, 9, "bold"),
            )

        # Zona de demanda máxima.
        demanda = resultado.demanda
        if demanda.inicio is not None and demanda.fin is not None:
            lienzo.create_rectangle(
                x(demanda.inicio),
                alto_cabecera,
                x(demanda.fin),
                alto_total - 10,
                fill=ROJO_CLARO,
                outline="",
            )
        for indice in range(1, filas + 1):
            y = alto_cabecera + indice * alto_fila
            lienzo.create_line(0, y, ancho_total, y, fill="#E3EAF2")


        # Bloques de las conferencias ya asignadas.
        for asignacion in visibles:
            conferencia = asignacion.conferencia
            y0 = alto_cabecera + (asignacion.sala - 1) * alto_fila
            y1 = y0 + (alto_fila - alto_bloque) / 2
            y2 = y1 + alto_bloque
            x1 = x(conferencia.inicio) + 1
            x2 = x(conferencia.fin) - 1
            if x2 - x1 < 4:
                x2 = x1 + 4
            color = color_categoria(conferencia.categoria)
            borde = ""
            grosor = 1
            if paso is not None and conferencia.id == paso.conferencia.id:
                borde = AMARILLO
                grosor = 3
            elif paso is not None and conferencia.id in paso.ids_solapadas:
                borde = ROJO
                grosor = 2
            etiqueta = "bloque_" + "".join(
                caracter if caracter.isalnum() else "_"
                for caracter in conferencia.id
            )
            self._rectangulo_redondeado(
                x1,
                y1,
                x2,
                y2,
                radio=6,
                fill=color,
                outline=borde or color,
                width=grosor,
                tags=(etiqueta,),
            )
            ancho_bloque = x2 - x1
            if ancho_bloque >= 26:
                color_texto = color_texto_contraste(color)
                maximo = max(2, int((ancho_bloque - 10) / 5.1))
                centro = (y1 + y2) / 2 - (6 if ancho_bloque >= 92 else 0)
                lienzo.create_text(
                    x1 + 6,
                    centro,
                    text=self._recortar(conferencia.nombre, maximo),
                    anchor="w",
                    fill=color_texto,
                    font=(FUENTE, 8, "bold"),
                    tags=(etiqueta,),
                )
                if ancho_bloque >= 92:
                    lienzo.create_text(
                        x1 + 6,
                        y2 - 10,
                        text=conferencia.horario,
                        anchor="w",
                        fill=color_texto,
                        font=(FUENTE, 7),
                        tags=(etiqueta,),
                    )
            lienzo.tag_bind(
                etiqueta,
                "<Button-1>",
                lambda _evento, conf=conferencia: self._mostrar_detalle(conf),
            )
            lienzo.tag_bind(
                etiqueta,
                "<Enter>",
                lambda _evento: lienzo.configure(cursor="hand2"),
            )
            lienzo.tag_bind(
                etiqueta,
                "<Leave>",
                lambda _evento: lienzo.configure(cursor=""),
            )

        # Conferencias aún no procesadas.
        if pendientes:
            y0 = alto_cabecera + total_salas * alto_fila
            for posicion, conferencia in enumerate(pendientes):
                x1 = x(conferencia.inicio) + 1
                x2 = max(x1 + 18, x(conferencia.fin) - 1)
                y1 = y0 + 6 + (posicion % 2) * 22
                y2 = y1 + 18
                etiqueta = "pendiente_" + "".join(
                    caracter if caracter.isalnum() else "_"
                    for caracter in conferencia.id
                )
                lienzo.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill="#E1E8F0",
                    outline="#94A3B3",
                    dash=(3, 2),
                    tags=(etiqueta,),
                )
                if x2 - x1 >= 34:
                    lienzo.create_text(
                        x1 + 4,
                        (y1 + y2) / 2,
                        text=self._recortar(
                            conferencia.nombre, max(2, int((x2 - x1 - 8) / 4.6))
                        ),
                        anchor="w",
                        fill="#4A5A6A",
                        font=(FUENTE, 7),
                        tags=(etiqueta,),
                    )
                lienzo.tag_bind(
                    etiqueta,
                    "<Button-1>",
                    lambda _evento, conf=conferencia: self._mostrar_detalle(conf),
                )

        # Marca vertical del paso actual.
        if paso is not None:
            xp = x(paso.conferencia.inicio)
            lienzo.create_line(
                xp,
                alto_cabecera,
                xp,
                alto_total - 10,
                fill=AZUL_MEDIO,
                width=2,
                dash=(6, 4),
            )
            lienzo.create_oval(
                xp - 4,
                alto_cabecera - 4,
                xp + 4,
                alto_cabecera + 4,
                fill=AZUL_MEDIO,
                outline="",
            )


    # ------------------------------------------------------------------
    # Registro y edición de conferencias
    # ------------------------------------------------------------------
    def _siguiente_id(self) -> str:
        existentes = {conferencia.id for conferencia in self.conferencias}
        numero = 1
        while f"C{numero:02d}" in existentes:
            numero += 1
        return f"C{numero:02d}"

    def _conferencia_desde_formulario(self) -> Conferencia:
        nombre = self.var_nombre.get().strip()
        if not nombre:
            raise ErrorConferencia("El nombre de la actividad es obligatorio.")
        inicio = hhmm_a_minutos(self.var_inicio.get())
        fin = hhmm_a_minutos(self.var_fin.get())
        categoria = self.var_categoria.get().strip() or "Académica"
        identificador = self.id_edicion or self._siguiente_id()
        return Conferencia(
            id=identificador,
            nombre=nombre,
            inicio=inicio,
            fin=fin,
            categoria=categoria,
        )

    def _confirmar_formulario(self, _evento=None) -> None:
        if self.id_edicion is None:
            self._agregar_conferencia()
        else:
            self._guardar_cambios()

    def _agregar_conferencia(self) -> None:
        try:
            conferencia = self._conferencia_desde_formulario()
        except (ErrorConferencia, ValueError) as exc:
            messagebox.showerror(
                "Datos de la actividad", str(exc), parent=self
            )
            self._mensaje("No se pudo agregar la actividad: revisa los datos.")
            return
        if any(c.id == conferencia.id for c in self.conferencias):
            messagebox.showerror(
                "Identificador repetido",
                f"Ya existe una actividad con el identificador {conferencia.id}.",
                parent=self,
            )
            return
        self.conferencias.append(conferencia)
        self._limpiar_formulario()
        self._recalcular(
            f"Actividad agregada: {conferencia.nombre} ({conferencia.horario})."
        )

    def _guardar_cambios(self) -> None:
        if self.id_edicion is None:
            return
        try:
            conferencia = self._conferencia_desde_formulario()
        except (ErrorConferencia, ValueError) as exc:
            messagebox.showerror(
                "Datos de la actividad", str(exc), parent=self
            )
            self._mensaje("No se guardaron los cambios: revisa los datos.")
            return
        posicion = next(
            (
                indice
                for indice, actual in enumerate(self.conferencias)
                if actual.id == self.id_edicion
            ),
            None,
        )
        if posicion is None:
            self._limpiar_formulario()
            self._mensaje("La actividad editada ya no existe.")
            return
        anterior = self.conferencias[posicion].nombre
        self.conferencias[posicion] = conferencia
        self._limpiar_formulario()
        self._recalcular(f"Actividad actualizada: {anterior} → {conferencia.nombre}.")

    def _limpiar_formulario(self) -> None:
        self.id_edicion = None
        self.var_nombre.set("")
        self.var_inicio.set("08:00")
        self.var_fin.set("09:00")
        self.var_categoria.set("Conferencia")
        self.btn_agregar.configure(state="normal")
        self.btn_guardar.configure(state="disabled")
        seleccion = self.arbol.selection()
        if seleccion:
            self.arbol.selection_remove(*seleccion)
        self.entry_nombre.focus_set()

    def _seleccionar_conferencia(self, _evento=None) -> None:
        seleccion = self.arbol.selection()
        if not seleccion:
            return
        identificador = self._mapa_arbol.get(seleccion[0])
        conferencia = next(
            (c for c in self.conferencias if c.id == identificador), None
        )
        if conferencia is None:
            return
        self.id_edicion = conferencia.id
        self.var_nombre.set(conferencia.nombre)
        self.var_inicio.set(conferencia.hora_inicio)
        self.var_fin.set(conferencia.hora_fin)
        self.var_categoria.set(conferencia.categoria)
        self.btn_agregar.configure(state="disabled")
        self.btn_guardar.configure(state="normal")
        self._mensaje(
            f"Editando «{conferencia.nombre}». Modifica los campos y pulsa "
            "«Guardar cambios»."
        )


    def _eliminar_seleccionada(self) -> None:
        seleccion = self.arbol.selection()
        if not seleccion:
            self._mensaje("Selecciona una actividad de la lista para eliminarla.")
            return
        identificador = self._mapa_arbol.get(seleccion[0])
        conferencia = next(
            (c for c in self.conferencias if c.id == identificador), None
        )
        if conferencia is None:
            return
        if not messagebox.askyesno(
            "Eliminar actividad",
            f"¿Eliminar «{conferencia.nombre}» ({conferencia.horario})?",
            parent=self,
        ):
            return
        self.conferencias = [
            actual for actual in self.conferencias if actual.id != conferencia.id
        ]
        self._limpiar_formulario()
        self._recalcular(f"Actividad eliminada: {conferencia.nombre}.")

    def _eliminar_todas(self) -> None:
        if not self.conferencias:
            self._mensaje("No hay actividades para eliminar.")
            return
        if not messagebox.askyesno(
            "Eliminar todas las actividades",
            "¿Eliminar todas las conferencias registradas? Esta acción no se "
            "puede deshacer.",
            parent=self,
        ):
            return
        self.conferencias = []
        self._limpiar_formulario()
        self._recalcular("Se eliminaron todas las actividades.")

    # ------------------------------------------------------------------
    # Carga y exportación de archivos
    # ------------------------------------------------------------------
    def _cargar_lista(self, conferencias: list[Conferencia], mensaje: str) -> None:
        self.conferencias = list(conferencias)
        self._limpiar_formulario()
        self._recalcular(mensaje)

    def _cargar_ejemplo(self) -> None:
        self._cargar_lista(
            conferencias_ejemplo(),
            "Conjunto de ejemplo cargado: 13 actividades del evento CECAR.",
        )

    def _generar_aleatorio(self) -> None:
        try:
            cantidad = int(self.var_cantidad.get())
        except (tk.TclError, ValueError):
            messagebox.showerror(
                "Cantidad inválida",
                "Indica un número entero de actividades entre 3 y 200.",
                parent=self,
            )
            return
        if not 3 <= cantidad <= 200:
            messagebox.showerror(
                "Cantidad inválida",
                "La cantidad debe estar entre 3 y 200 actividades.",
                parent=self,
            )
            return
        try:
            nuevas = conferencias_aleatorias(cantidad)
        except (ErrorConferencia, ValueError) as exc:
            messagebox.showerror(
                "No fue posible generar los datos", str(exc), parent=self
            )
            return
        self._cargar_lista(
            nuevas, f"Generadas {cantidad} actividades aleatorias."
        )

    def _importar_csv(self) -> None:
        ruta = filedialog.askopenfilename(
            parent=self,
            title="Importar conferencias desde CSV",
            initialdir=str(RUTA_DATOS),
            filetypes=(("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")),
        )
        if not ruta:
            return
        try:
            conferencias = cargar_csv(ruta)
        except ErrorDatos as exc:
            messagebox.showerror("Error al importar", str(exc), parent=self)
            self._mensaje("La importación falló: revisa el archivo CSV.")
            return
        self._cargar_lista(
            conferencias,
            f"CSV importado: {len(conferencias)} actividades desde {Path(ruta).name}.",
        )

    def _exportar_csv(self) -> None:
        if self.resultado is None:
            messagebox.showwarning(
                "Sin resultados",
                "Genera una asignación antes de exportar. Registra actividades o "
                "carga el conjunto de ejemplo.",
                parent=self,
            )
            return
        ruta = filedialog.asksaveasfilename(
            parent=self,
            title="Exportar asignación de salas",
            initialdir=str(RUTA_DATOS),
            initialfile="asignacion_salas.csv",
            defaultextension=".csv",
            filetypes=(("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")),
        )
        if not ruta:
            return
        try:
            guardado = guardar_resultado_csv(ruta, self.resultado)
        except (ErrorDatos, OSError) as exc:
            messagebox.showerror("Error al exportar", str(exc), parent=self)
            self._mensaje("No se pudo exportar el archivo CSV.")
            return
        self._mensaje(f"Asignación exportada en {guardado}.")
        messagebox.showinfo(
            "Exportación completada",
            f"La asignación se guardó en:\n{guardado}",
            parent=self,
        )

