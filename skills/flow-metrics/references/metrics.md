# Referencia de métricas de flujo

## Definiciones

### Lead Time
**Qué mide:** Tiempo total desde que nació el ítem hasta que se entregó.
**Fórmula:** `Resolved - Created` (en días)
**Solo para:** ítems con `Resolved` no nulo
**Interpretación:** Refleja la experiencia del stakeholder — cuánto espera
desde que pide algo hasta que lo recibe.

### Aging medio (sprint-relativo)
**Qué mide:** Cuánto tiempo lleva vivo cada ítem dentro del sprint actual.
**Fórmula:**
- Ítems nativos del sprint: `hoy - Created`
- Leftovers (Created < sprint_start): `hoy - sprint_start`
- Ítems cerrados: `Resolved - max(Created, sprint_start)`
**Incluye:** todos los ítems (abiertos y cerrados)
**Interpretación:** Velocidad general del sprint. Número alto = trabajo que
tarda mucho en resolverse, ya sea por volumen, bloqueos o falta de foco.

### WIP Aging medio
**Qué mide:** Cuánto llevan abiertos los ítems que siguen sin cerrarse.
**Fórmula:** `hoy - max(Created, sprint_start)` solo para ítems sin Resolved
**Incluye:** solo ítems abiertos (Status ≠ Closed, Rejected)
**Interpretación:** Riesgo activo. Es el número más accionable — indica
qué conversación hay que tener hoy, no en la retro.

### Diferencia entre Aging medio y WIP Aging medio
- Aging medio: foto del sprint completo (incluye lo ya cerrado)
- WIP Aging: foto del riesgo actual (solo lo que sigue abierto)
Un sprint puede tener buen aging medio si cerró mucho rápido al principio,
pero mal WIP aging si los restantes llevan semanas bloqueados.

### Throughput
**Qué mide:** Cuántos ítems se cierran por período.
**Granularidad:**
- Sprint ≤ 14 días → por día
- Sprint > 14 días → por semana ISO
**Filtro:** solo ítems con `Resolved` dentro de la ventana del sprint
(entre sprint_start y sprint_end)
**Interpretación:** Capacidad de entrega del equipo. Estable = predecible.
Pico al final = cliff effect (ver abajo).

### Cycle Time (aproximación)
**Qué mide:** Tiempo desde que se empieza a trabajar en un ítem hasta
que se cierra. En teoría usa historial de transiciones de estado.
**Proxy con CSV básico:** `Updated - Created` para ítems abiertos
**Limitación:** sin historial de transiciones (requiere API de Jira),
solo podemos aproximar. Marcarlo siempre como "aprox." en el dashboard.

---

## Patrones a detectar

### Cliff Effect
**Señal:** pico de throughput > 2.5x la media del resto de períodos
**Significado:** el trabajo se acumula y se resuelve en ráfaga al final
del sprint, típicamente antes de la review
**Causa raíz habitual:** WIP alto, falta de límites de WIP, presión
implícita de "hay que cerrar antes de la demo"
**Argumento para dirección:** no es problema de capacidad, es problema
de flujo y de cuándo se prioriza cerrar vs. empezar

### WIP fantasma
**Señal:** ítems en estado "In Progress" u "Open" con aging > 14 días
sin movimiento reciente (Updated hace más de 5 días)
**Significado:** trabajo declarado como en curso que nadie está avanzando
**Acción:** revisar en daily y decidir: continuar, bloquear, o devolver
al backlog

### Ítems sin owner
**Señal:** Assignee vacío + Status ≠ New + aging > 7 días
**Significado:** trabajo activo sin responsable — nadie lo va a cerrar
**Gravedad:** alta. En sprints cortos, un ítem sin owner 7 días = riesgo
de no entregarse en el sprint

### Sobrecarga individual
**Señal:** una persona con > 40% de los ítems abiertos del sprint
**Significado:** cuello de botella personal o distribución de trabajo
desequilibrada
**Nota importante:** no es crítica al individuo — es señal de gestión
del sistema. La conversación es con el equipo y con los que priorizan.

### Leftovers problemáticos
**Señal:** leftovers del sprint anterior que siguen sin cerrarse
**Significado:** deuda del sprint anterior que se arrastra y consume
capacidad del sprint actual
**Impacto en métricas:** sin corrección de aging, los leftovers inflan
artificialmente el aging medio — por eso se mide desde sprint_start

---

## Semáforos de KPIs

| Métrica | Verde | Ámbar | Rojo |
|---|---|---|---|
| Aging medio | < 5d | 5-10d | > 10d |
| WIP aging | < 5d | 5-10d | > 10d |
| % completado | ≥ 70% | 40-70% | < 40% |
| Leftovers abiertos | 0 | 1-3 | > 3 |
| Ítems sin asignar | 0 | 1-2 | > 2 |

Estos umbrales son orientativos — ajustar según el contexto del equipo
y la madurez del proceso. Lo importante es la tendencia entre sprints,
no el valor absoluto de un sprint aislado.
