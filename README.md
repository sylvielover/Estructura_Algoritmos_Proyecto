# Asignación óptima de salas para eventos académicos

**Proyecto final — Escenario 5**  
Curso: *Estructura de Datos y Análisis de Algoritmos*  
Programa de Ingeniería de Sistemas — CECAR

Aplicación de escritorio en Python/Tkinter que planifica conferencias, seminarios,
talleres y encuentros académicos en el **mínimo número de salas**, evita
solapamientos y permite observar la decisión voraz paso a paso.

![Interfaz principal](docs/capturas/interfaz_principal.png)

## El problema en una frase

Dado un conjunto de actividades con hora de inicio y fin, se busca una
asignación a salas sin conflictos que use la menor cantidad posible de espacios.
El algoritmo ordena por **hora de inicio ascendente** y reutiliza la sala que se
libera más pronto; el número de salas coincide con la **demanda máxima
simultánea**, por lo que la solución es óptima.

## Funcionalidades

- Registro, edición y eliminación de conferencias con validación de horarios.
- Carga del conjunto institucional de ejemplo, generación aleatoria reproducible,
  importación y exportación CSV compatible con Excel.
- Línea de tiempo por sala con colores por categoría, demanda pico, salas
  disponibles/ocupadas y detalle de cada actividad.
- Ejecución **paso a paso**, navegación, control de velocidad y reproducción
  automática de las decisiones voraces.
- Comparación de cinco criterios de ordenamiento (inicio, registro, duración,
  fin e inicio descendente) con indicador de optimalidad.
- Panel de análisis con el diseño del algoritmo, estructuras, complejidad y
  argumento de optimalidad.
- Margen configurable entre actividades de una misma sala (0–240 min).

## Inicio rápido

Requisitos: **Python 3.10 o superior** con Tkinter (incluido en el instalador
oficial de Windows). La aplicación no requiere paquetes externos.

```powershell
# Desde la raíz del proyecto
py main.py
```

La ventana abre con las 13 actividades del evento CECAR y la solución óptima de
4 salas. También puede ejecutarse con doble clic sobre `main.py`.

### Atajos de teclado

| Atajo | Acción |
|---|---|
| `Ctrl+O` | Importar conferencias desde CSV |
| `Ctrl+S` | Exportar la asignación actual a CSV |
| `Ctrl+R` | Generar actividades aleatorias |
| `Ctrl+E` | Cargar el conjunto de ejemplo |
| `←` / `→` | Paso anterior / siguiente |
| `Espacio` | Reproducir o pausar |
| `Supr` | Eliminar la actividad seleccionada |

## Estructura del proyecto

```text
Proyecto_Salas_CECAR/
├── main.py                     # Punto de entrada de la aplicación
├── benchmark.py                # Medición reproducible de tiempo y memoria
├── requirements.txt            # Dependencias para figuras y documentos
├── datos/
│   └── conferencias_ejemplo.csv
├── salas/
│   ├── modelo.py               # Conferencia, algoritmo voraz, demanda y métricas
│   ├── datos.py                # CSV, datos de ejemplo y datos aleatorios
│   └── interfaz.py             # GUI Tkinter, línea de tiempo y comparación
├── tests/
│   └── test_modelo.py          # 29 pruebas unitarias
├── scripts/
│   ├── generar_evidencias.py   # Figuras del informe y la presentación
│   ├── generar_capturas.py     # Capturas de la interfaz
│   ├── smoke_interfaz.py       # Verificación automática de la GUI
│   ├── generar_informe.py      # Genera el informe técnico DOCX
│   └── generar_presentacion.py # Genera la presentación PPTX
└── docs/
    ├── figuras/                # Diagramas, Gantt, comparación y escalamiento
    ├── capturas/               # Capturas de las tres pestañas de la GUI
    ├── resultados_benchmark.csv
    ├── Informe_Tecnico_Escenario5.docx
    └── Presentacion_Escenario5.pptx
```

## Algoritmo

### Esquema voraz

| Componente | Definición en este proyecto |
|---|---|
| Candidatos `C` | Conferencias con identificador, nombre, inicio, fin y categoría |
| Solución `S` | Pares `(conferencia, sala)` sin solapamientos |
| Seleccionar | La conferencia con menor hora de inicio (desempate: fin, id) |
| Factible | La sala elegida está libre: `último_fin + margen ≤ nuevo_inicio` |
| Insertar | Asignar la conferencia a la sala y actualizar su liberación |
| Función objetivo | Minimizar el número de salas utilizadas |
| Terminación | Todas las conferencias fueron asignadas |

### Pseudocódigo

```text
asignar_salas(C, margen):
    ordenar C por (inicio, fin, id) ascendente
    disponibles ← cola de prioridad vacía        # (fin + margen, sala)
    siguiente_sala ← 1
    para cada conferencia c en C:
        si disponibles no está vacía y mínimo.liberación ≤ c.inicio:
            sala ← extraer mínimo                   # reutilizar
        si no:
            sala ← siguiente_sala; siguiente_sala ← siguiente_sala + 1
        asignar c a sala
        insertar (c.fin + margen, sala) en disponibles
    retornar asignaciones, demanda máxima y bitácora
```

### Optimalidad

Sea `D` la máxima cantidad de conferencias simultáneas. Toda solución necesita
al menos `D` salas. Cuando el algoritmo abre una sala nueva para `c`, todas las
salas existentes tienen su última actividad ocupada hasta después de `c.inicio`;
por el orden por inicio, esas actividades se solapan con `c`. En ese instante hay
entonces `S` actividades simultáneas, donde `S` es el número de salas usadas, así
que `S ≤ D`. Como la solución es factible, `S ≥ D`; por tanto `S = D`. El orden
por inicio es esencial: con otro orden el algoritmo puede usar muchas más salas
(en el ejemplo, el orden descendente llega a 13).

### Complejidad

| Etapa | Tiempo | Espacio |
|---|---|---|
| Validación de identificadores | `O(n)` | `O(n)` |
| Ordenamiento estable | `O(n log n)` | `O(n)` |
| Asignación con cola de prioridad | `O(n log n)` | `O(n)` |
| Demanda máxima por barrido | `O(n log n)` | `O(n)` |
| Bitácora didáctica (opcional) | `O(n² log n)` en el peor caso | `O(n²)` |

La aplicación calcula la solución y las métricas en `O(n log n)`. La bitácora
detallada se activa solo para la simulación paso a paso.

## Resultados

Conjunto de ejemplo: **13 actividades**, **4 salas**, demanda máxima **4**
entre **09:15 y 10:30**, solución **óptima**.

| n | Tiempo promedio (ms) | Memoria pico (KiB) | Salas | Demanda |
|---:|---:|---:|---:|---:|
| 10 | 0.061 | 3.5 | 3 | 3 |
| 50 | 0.248 | 9.5 | 14 | 14 |
| 100 | 0.662 | 16.6 | 19 | 19 |
| 250 | 1.394 | 34.8 | 46 | 46 |
| 500 | 3.039 | 66.1 | 86 | 86 |
| 1 000 | 5.669 | 123.8 | 168 | 168 |
| 2 000 | 13.369 | 243.8 | 316 | 316 |
| 4 000 | 27.257 | 563.2 | 612 | 612 |

El ajuste `t = a·n·log₂ n` obtiene `R² = 0.998` y la memoria crece de forma
lineal (≈ 0.138 KiB por conferencia). Todos los casos fueron validados como
óptimos y factibles. Consulte `docs/resultados_benchmark.csv` para los tiempos
mínimos, máximos y número de repeticiones.

### Comparación de criterios

| Orden de selección | Ejemplo (13) | Aleatorio (200) |
|---|---:|---:|
| **Hora de inicio (escenario)** | **4 (óptimo)** | **41 (óptimo)** |
| Orden de registro | 4 (óptimo) | 99 |
| Duración ascendente | 5 | 53 |
| Hora de finalización ascendente | 4 (óptimo) | 48 |
| Hora de inicio descendente | 13 | 200 |


## Pruebas y reproducibilidad

```powershell
# 29 pruebas unitarias del modelo, datos y optimalidad
py -m unittest discover -s tests -v

# Verificación automática de los flujos de la interfaz (28 comprobaciones)
py scripts/smoke_interfaz.py

# Benchmark reproducible con semillas fijas
py benchmark.py

# Figuras y capturas
py scripts/generar_evidencias.py
py scripts/generar_capturas.py
```

Para regenerar el informe y la presentación se necesitan las dependencias de
desarrollo:

```powershell
py -m pip install -r requirements.txt
py scripts/generar_informe.py
py scripts/generar_presentacion.py
```

## Formato CSV

La aplicación acepta separador `;` o `,`, codificación UTF-8 (con o sin BOM) y
encabezados alternativos como `hora_inicio`, `hora fin`, `codigo` o `tipo`. Las
columnas obligatorias son `nombre`, `inicio` y `fin`; `id` y `categoria` son
opcionales. Ejemplo:

```csv
id;nombre;inicio;fin;categoria
C01;Instalación oficial;07:00;08:00;Institucional
C02;Inteligencia artificial en la educación;08:00;09:30;Conferencia
```

Las horas usan `HH:MM` en formato de 24 horas; `24:00` se admite como fin del
día. Si hay identificadores repetidos, la importación los renombra de forma
automática (`C1`, `C1_2`, ...) y reporta errores con el número de línea.

## Decisiones de diseño y limitaciones

- **Salas homogéneas:** no se modelan capacidad, equipamiento ni preferencias;
  cualquier sala puede alojar cualquier actividad.
- **Intervalos semiabiertos:** una actividad que termina a las 10:00 y otra que
  inicia a las 10:00 pueden compartir sala. El margen configurable permite exigir
  una separación adicional.
- **Tiempo en minutos:** la granularidad es de un minuto, suficiente para la
  planificación académica y para mantener el modelo simple.
- **Óptimo para este modelo:** la optimalidad se garantiza para el problema de
  partición de intervalos. Si se agregan restricciones (capacidad, recursos,
  preferencias), el problema cambia y el criterio voraz podría dejar de ser óptimo.
- **Bitácora costosa:** guardar todos los diagnósticos de cada paso incrementa el
  costo; por eso el benchmark y la comparación usan `registrar_pasos=False`.

## Documentos entregables

- [Informe técnico (DOCX)](docs/Informe_Tecnico_Escenario5.docx)
- [Presentación (PPTX)](docs/Presentacion_Escenario5.pptx)
- [Resultados del benchmark](docs/resultados_benchmark.csv)
- [Figuras](docs/figuras)
- [Capturas de la interfaz](docs/capturas)

## Referencias

- Cormen, T. H., Leiserson, C. E., Rivest, R. L. y Stein, C. (2022). *Introduction to Algorithms* (4.ª ed.). MIT Press.
- Kleinberg, J. y Tardos, É. (2006). *Algorithm Design*. Pearson.
- Python Software Foundation. (2026). *Python 3 Documentation*. https://docs.python.org/3/
- Python Software Foundation. (2026). *tkinter — Python interface to Tcl/Tk*. https://docs.python.org/3/library/tkinter.html

