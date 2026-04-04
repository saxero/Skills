---
name: flow-metrics-jira
description: >
  Analyzes agile flow metrics for Scrum Masters and Product Owners from a
  Jira CSV export. Generates an interactive HTML dashboard and a printable
  one-page HTML/PDF report with KPIs, adaptive throughput (daily for sprints
  ≤14 days, weekly otherwise), WIP aging scatter, leftover detection,
  sprint-relative aging, and two narrative blocks — one unfiltered for the SM
  and one executive summary for management.

  TRIGGER this skill whenever: the user uploads or mentions a Jira CSV and
  wants to understand how the sprint is going or went; they ask about
  throughput, WIP aging, lead time, cycle time, or sprint health WITH a file
  attached or data to analyze; they want a dashboard or report for the team
  or for management based on Jira data; they say things like "how did the
  sprint go", "analyze the sprint", "show me sprint metrics", "what's blocked",
  "sprint retrospective with data", "team velocity report", or "something to
  show to management about the sprint". Also trigger for "sprint review data",
  "are there leftovers?", "which tickets are aging", "cliff effect".
  Equivalent Spanish triggers: "cómo ha ido el sprint", "analiza el sprint",
  "métricas del equipo", "tickets bloqueados", "retrospectiva con datos".

  DO NOT trigger for: conceptual questions about agile metrics with no file
  ("what is cycle time?"); capacity planning without a CSV; sprint review
  presentation writing with no data file; setting up Jira boards or workflows;
  or CSV files clearly not from Jira (sales, HR, finance data). The key signal
  is a Jira CSV combined with intent to analyze sprint or team flow data.
---

# Flow Metrics — Scrum Master & Product Owner Dashboard

Converts a Jira CSV export into an actionable analysis with two outputs:
an **interactive HTML dashboard** for daily SM use and a **printable HTML/PDF
report** for management or sprint history.

## Workflow

### 1. Read the CSV
Parse the uploaded CSV. Key columns:
`Issue key`, `Issue Type`, `Status`, `Assignee`, `Created`, `Updated`,
`Resolved`, `Sprint`, `Status Category`.

Run the analysis script:
```bash
python3 scripts/analyze_csv.py <csv_path> --sprint-start YYYY-MM-DD --sprint-end YYYY-MM-DD
```

### 2. Ask sprint dates
Always ask before calculating any metric:
- Sprint **start date**
- Sprint **end date**

Keep it short: *"I need the sprint dates to calculate aging correctly. When does it start and end?"*

Reason: leftovers need aging counted from sprint start, not ticket creation;
and sprint duration determines throughput granularity.

If the user doesn't know, infer from the CSV (min `Created` → max `Resolved`)
and flag it: *"Using dates inferred from the CSV — correct them if needed."*

### 3. Detect leftovers
A ticket is a **leftover** if `Created` < `sprint_start`.
Its aging is counted from `sprint_start`, not from `Created`.

### 4. Choose throughput granularity
- Sprint **≤ 14 days** → **daily** granularity
- Sprint **> 14 days** → **weekly** (ISO week)

Only count tickets whose `Resolved` date falls within the sprint window.

### 5. Calculate metrics
See `references/metrics.md` for full definitions. Summary:

| Metric | Formula |
|---|---|
| Lead time | `Resolved − Created` (closed tickets only) |
| Sprint-relative aging | All tickets; leftovers age from `sprint_start` |
| WIP aging | Open tickets only; same sprint-relative rule |
| Throughput | Closed tickets per day or week within sprint window |
| Cycle time (proxy) | `Updated − Created` for open tickets |

### 6. Generate outputs
```bash
python3 scripts/generate_outputs.py \
  --data <analysis.json> \
  --sprint-start YYYY-MM-DD \
  --sprint-end   YYYY-MM-DD \
  --output-dir   /mnt/user-data/outputs/
```

Produces:
- `dashboard.html` — tabs (internal / executive), filters, scatter, aging table
- `report.html` — single printable page for management

### 7. Write the narrative
Two blocks, always included:

**SM block** (internal, no filter):
- Direct, no softening
- Name the actual problem pattern (cliff effect / unowned WIP / individual overload)
- 3 findings with concrete numbers

**Executive block** (for management):
- Business language, no agile jargon
- One key number + what it means + one recommended action
- Max 3 short paragraphs

---

## Interpretation rules

**Cliff effect** — throughput peak > 2.5× average of other periods.
Signal: work accumulated and flushed at sprint end. Not a good sprint.

**Unowned WIP** — Open/New ticket, no `Assignee`, aging > 7 days.
Active risk, not future work. Needs an owner today.

**Individual overload** — one person holds > 40% of open tickets.
Signal of distribution problem or systemic blocker, not personal failure.

**Aging scatter** — two views:
- Without "New" — active work (in progress or closed)
- With all statuses — full sprint picture
New tickets are split out because they distort the in-progress reading.

---

## Output specs

### dashboard.html
- Internal tab: KPI tiles with traffic lights, throughput chart, scatter (dual view),
  aging top-8 table, SM narrative block
- Executive tab: executive KPIs, cumulative burndown, business argument block
- Leftover banner when detected
- Date form with real-time recalculation
- Scatter: hover tooltips, filter by status / assignee / type, risk zone lines at 14d and 28d

### report.html
- Single page, print-optimised
- Header: sprint name + dates
- 4 KPI tiles
- Throughput chart + status donut side by side
- Executive block
- Footer: generation date + data disclaimer
- Print hint visible on screen, hidden on print

---

## Implementation notes

- Jira date format: `dd/Mon/yy h:mm AM/PM` → parse with `%d/%b/%y %I:%M %p`
- Empty `Assignee` → treat as "Sin asignar" / "Unassigned"
- CSV has 300+ columns — only read the relevant ones
- Two CSVs uploaded → compare `Issue key` sets to detect status changes between exports
- See `references/examples.md` for narrative examples and edge case samples
