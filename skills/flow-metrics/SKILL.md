---
name: flow-metrics-scrum
description: >
  Analiza métricas de flujo ágil para Scrum Masters y Product Owners a partir
  de un CSV exportado de Jira. Genera un dashboard HTML interactivo y un PDF
  de una página con KPIs, throughput adaptativo, aging del WIP, scatter de
  ítems, análisis narrativo interno y resumen ejecutivo para dirección.
  Detecta leftovers (tickets del sprint anterior), ajusta el aging relativo
  a las fechas reales del sprint, y elige automáticamente granularidad diaria
  o semanal según la duración del sprint.
  Úsalo siempre que el usuario mencione métricas de sprint, análisis de Jira,
  throughput, cycle time, lead time, aging de tickets, WIP, retrospectiva con
  datos, o cuando suba un CSV de Jira y quiera entender qué está pasando en
  su equipo. También cuando pregunten por el rendimiento del equipo, bloqueos,
  o quieran algo para mostrar a dirección sobre el progreso del sprint.
---

# Flow Metrics — Scrum Master & Product Owner Dashboard

Este skill convierte un CSV de Jira en un análisis accionable con dos outputs:
un **dashboard HTML interactivo** para uso diario y una **página HTML imprimible
como PDF** para compartir con dirección o guardar como histórico de sprint.

## Flujo de trabajo

### 1. Recibir el CSV
El usuario sube un CSV exportado desde Jira (Export → Export Excel CSV all fields).
Lee los campos clave: `Issue key`, `Issue Type`, `Status`, `Assignee`,
`Created`, `Updated`, `Resolved`, `Sprint`, `Status Category`.

Usa el script de análisis para extraer los datos:
```bash
python3 scripts/analyze_csv.py <ruta_del_csv>
```

### 2. Preguntar las fechas del sprint
Antes de calcular cualquier métrica, pregunta **siempre** al usuario:
- Fecha de **inicio** del sprint
- Fecha de **fin** del sprint

Esto es imprescindible porque:
- Los leftovers (tickets creados antes del sprint) deben calcular su aging
  desde el inicio del sprint, no desde su fecha de creación original.
- La duración del sprint determina la granularidad del throughput.

Ejemplo de pregunta al usuario:
> "Para calcular el aging correctamente necesito las fechas del sprint.
> ¿Cuándo empieza y cuándo termina?"

### 3. Detectar leftovers
Un ticket es **leftover** si su fecha `Created` es anterior al inicio del sprint.
Su aging se calcula desde `sprint_start`, no desde `Created`.
Esto evita que inflen artificialmente el aging medio del sprint actual.

### 4. Elegir granularidad del throughput
- Sprint **≤ 14 días** → granularidad **diaria**
- Sprint **> 14 días** → granularidad **semanal** (semana ISO)

El throughput solo cuenta tickets cerrados (`Resolved` no nulo) cuya fecha
de resolución esté dentro de la ventana del sprint.

### 5. Calcular métricas
Ver referencia completa en `references/metrics.md`.

Métricas principales:
- **Lead time medio** — desde `Created` hasta `Resolved` (solo cerrados)
- **Aging medio (sprint-relativo)** — todos los ítems, aging desde sprint_start para leftovers
- **WIP aging medio** — solo ítems abiertos (sin `Resolved`)
- **Throughput** — ítems cerrados por período (día o semana según duración)
- **Cycle time aproximado** — proxy usando `Updated` para ítems abiertos

### 6. Generar los dos outputs
Usa el script generador:
```bash
python3 scripts/generate_outputs.py \
  --data <ruta_json_analisis> \
  --sprint-start <YYYY-MM-DD> \
  --sprint-end <YYYY-MM-DD> \
  --output-dir /mnt/user-data/outputs/
```

Genera:
- `dashboard.html` — interactivo, con tabs interno/dirección, filtros, scatter
- `report.html` — una página, imprimible como PDF desde el navegador

### 7. Análisis narrativo
Además de los gráficos, incluye siempre dos bloques de texto:

**Bloque interno (para el SM):**
- Sin filtros, directo
- Identifica el patrón de problema real (cliff effect, WIP sin owner, sobrecarga)
- Señala los 3 hallazgos más importantes con datos concretos

**Bloque ejecutivo (para dirección):**
- Lenguaje de negocio, sin jerga técnica
- Cifra clave + qué significa + acción recomendada
- Máximo 3 párrafos

---

## Reglas de interpretación

**Cliff effect:** si el pico de throughput supera 2.5x la media del resto
de períodos, es cliff effect. Señalarlo explícitamente — no es un buen sprint,
es trabajo acumulado resuelto en ráfaga al final.

**WIP sin owner:** tickets en estado Open o New sin `Assignee` con más de
7 días de aging dentro del sprint. Son riesgo activo, no trabajo futuro.

**Sobrecarga individual:** si una persona acumula más del 40% de los ítems
abiertos, señalarlo. No como crítica a la persona — como señal de distribución
de trabajo o de bloqueo sistémico.

**Scatter de aging:** el scatter muestra dos vistas:
- Sin estado "New" — ítems activos (en curso o cerrados)
- Con todos los estados — visión completa del sprint
Los ítems "New" se separan porque distorsionan la lectura del trabajo en curso.

---

## Outputs esperados

### dashboard.html
- Tab "Uso interno": KPIs con semáforo, throughput, scatter, aging table, narrativa SM
- Tab "Para dirección": KPIs ejecutivos, burndown acumulado, argumento de negocio
- Banner de leftovers detectados (si los hay)
- Tooltip en hover en scatter
- Filtros por estado / asignado / tipo en scatter
- Formulario de fechas con recálculo en tiempo real

### report.html
- Una sola página, diseño limpio imprimible
- Cabecera con nombre del sprint y fechas
- 4 KPIs en fila
- Throughput + donut de estado lado a lado
- Bloque ejecutivo
- Footer con fecha de generación y nota sobre datos
- Instrucción visible: "Ctrl+P o Cmd+P para exportar a PDF"

---

## Notas para la implementación

- Los campos de fecha en Jira usan formato `dd/Mon/yy h:mm AM/PM`
  (ej: `26/Mar/26 2:31 PM`). Parsear con `%d/%b/%y %I:%M %p`.
- Algunos campos de `Assignee` pueden estar vacíos (NaN). Tratar como "Sin asignar".
- El CSV de Jira tiene 300+ columnas. Solo procesar las relevantes.
- Si el usuario sube dos CSVs, comparar los `Issue key` para detectar cambios
  de estado entre exports (evolución del sprint).

Ver ejemplos de análisis en `references/examples.md`.
