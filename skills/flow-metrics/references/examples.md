# Ejemplos de análisis y outputs narrativos

## Ejemplo 1 — Sprint con cliff effect

**Datos:**
- Sprint: 14 días
- Throughput: Sem1: 2, 1, 0, 1 / Sem2: 0, 1, 8, 6
- WIP aging medio: 9.2 días
- 3 ítems sin asignar

**Bloque interno (SM):**
> El equipo no tiene problema de capacidad — cerró 19 ítems. El problema
> es cuándo los cierra. El 74% de los cierres ocurrieron en los últimos
> 2 días del sprint. Eso no es delivery continuo, es sprint-end rush.
> Hay 3 ítems sin asignar con más de 7 días de aging — nadie los va a
> cerrar solo. Necesitan owner antes de mañana.

**Bloque ejecutivo (dirección):**
> El sprint entregó el volumen esperado pero con un patrón de riesgo:
> el trabajo se acumula durante dos semanas y se resuelve en ráfaga al
> final. Esto no es predecible ni sostenible. La recomendación es revisar
> cómo se limita el trabajo en paralelo — no más recursos, sino menos
> frentes abiertos a la vez.

---

## Ejemplo 2 — Sprint con leftovers

**Datos:**
- Sprint: 10 Mar → 27 Mar (17 días)
- 28 de 48 ítems creados antes del sprint_start
- Sin corrección: aging medio = 20.5 días
- Con corrección (desde sprint_start): aging medio = 10.6 días

**Banner de leftovers:**
> ⚠ 28 leftovers del sprint anterior — 12 siguen abiertos. Su aging se
> calcula desde el inicio del sprint (10/03), no desde su fecha de
> creación original. Sin esta corrección el aging medio aparecería como
> 20.5 días cuando en realidad son 10.6 días dentro de este sprint.

---

## Ejemplo 3 — Granularidad diaria (sprint corto)

**Datos:**
- Sprint: 2026-03-13 → 2026-03-27 (14 días)
- Throughput diario: 13→0, 14→0, 15→0, 16→1, 17→2, 18→0, 19→0,
  20→1, 21→0, 22→0, 23→2, 24→2, 25→6, 26→3, 27→2

**Nota en el dashboard:**
> Granularidad diaria · Sprint de 14 días

**Insight de throughput:**
> Cliff effect detectado. 11 de los 19 cierres (58%) ocurrieron en los
> últimos 3 días. Los primeros 11 días del sprint cerraron solo 4 ítems.

---

## Ejemplo 4 — Scatter con leftovers visibles

En el scatter de "visión completa", los leftovers aparecen con el
aging relativo al sprint (no al Created). Un ítem creado hace 36 días
pero en un sprint de 17 días aparece como 17 días en el eje X, no 36.

Esto hace el scatter comparable entre sprints — el eje X siempre
representa "días dentro de este sprint", no "días de vida del ticket".

---

## Formato de pregunta de fechas al usuario

Cuando el usuario suba un CSV, preguntar así (conciso, sin explicar
todo el razonamiento):

> "Para calcular el aging correctamente necesito las fechas del sprint.
> ¿Cuándo empieza y cuándo termina?"

Si el usuario no sabe las fechas exactas, usar como proxy:
- sprint_start: fecha mínima de `Created` en el CSV
- sprint_end: fecha de hoy o fecha máxima de `Resolved`
Y avisarlo explícitamente: "Usando fechas inferidas del CSV — puedes
corregirlas si las conoces."
