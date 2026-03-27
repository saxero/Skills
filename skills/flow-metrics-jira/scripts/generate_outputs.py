#!/usr/bin/env python3
"""
generate_outputs.py — Genera dashboard.html y report.html desde el JSON de análisis.
Uso: python3 scripts/generate_outputs.py --data <analysis.json> --output-dir <dir>
"""

import json
import argparse
import os
from datetime import datetime

# ── Helpers ────────────────────────────────────────────────────────────────────

def dot_color(val, thresholds, reverse=False):
    """Devuelve red/amber/green según umbrales [verde_max, amber_max]."""
    lo, hi = thresholds
    if reverse:
        return 'green' if val >= hi else 'amber' if val >= lo else 'red'
    return 'green' if val <= lo else 'amber' if val <= hi else 'red'

def status_color(status):
    colors = {'Closed':'#1D9E75','Done':'#1D9E75','Open':'#EF9F27',
              'New':'#888780','Rejected':'#D85A30','In Progress':'#378ADD'}
    return colors.get(status, '#B4B2A9')

def js_json(obj):
    return json.dumps(obj, ensure_ascii=False)


# ── Dashboard HTML ─────────────────────────────────────────────────────────────

def build_dashboard(data):
    m   = data['meta']
    k   = data['kpis']
    tp  = data['throughput']
    sc  = data['status_counts']
    ao  = data['assignee_open']
    si  = data['scatter_items']
    aw  = data['aging_wip_top8']
    uo  = data['unassigned_open']

    # semáforos
    dot_lt  = dot_color(k['avg_sprint_age'], [5, 10])
    dot_done= dot_color(k['pct_done'], [40, 70], reverse=True)
    dot_wip = dot_color(k['avg_wip_age'], [5, 10])
    dot_lo  = dot_color(k['leftovers_open'], [0, 3])

    # throughput colors
    tp_colors = ['"#EF9F27"' if l == tp['current_period'] else '"#378ADD"'
                 for l in tp['labels']]

    # cliff insight
    if tp['cliff_effect']:
        pct = round(tp['peak_val'] / max(tp['total'], 1) * 100)
        tp_insight = f"<strong>Cliff effect detectado.</strong> El pico de {tp['peak_val']} cierres en {tp['peak_label']} representa el {pct}% del total del sprint. El trabajo no fluye de forma continua."
    else:
        tp_insight = f"Throughput distribuido. Total cerrados: <strong>{tp['total']} ítems</strong>. Pico en {tp['peak_label']} con {tp['peak_val']}."

    # leftover banner
    leftover_html = ''
    if k['leftovers_total'] > 0:
        leftover_html = f"""
        <div style="background:#FAEEDA;border:0.5px solid #FAC775;border-radius:8px;
            padding:.65rem .875rem;font-size:12px;color:#854F0B;margin-bottom:1.25rem;line-height:1.6">
          <strong>{k['leftovers_total']} leftovers del sprint anterior</strong> —
          {k['leftovers_open']} siguen abiertos. Su aging se calcula desde el inicio del sprint
          ({m['sprint_start']}), no desde su fecha de creación original.
        </div>"""

    # unassigned alert
    unassigned_html = ''
    if k['unassigned_open'] > 0:
        unassigned_html = f"""
        <div style="background:#FAECE7;border:0.5px solid #F0997B;border-radius:8px;
            padding:.65rem .875rem;font-size:12px;color:#993C1D;margin-bottom:.75rem;line-height:1.6">
          ⚠ {k['unassigned_open']} ítems abiertos sin asignar — nadie los va a cerrar solo.
        </div>"""

    # aging table rows
    aging_rows = ''
    max_age = max((r['sprint_age'] for r in aw), default=1)
    for r in aw:
        pct = round(r['sprint_age'] / max(max_age, 1) * 100)
        color = '#D85A30' if r['sprint_age'] > 28 else '#EF9F27' if r['sprint_age'] > 14 else '#1D9E75'
        assignee = r['assignee'] if r['assignee'] != 'Sin asignar' else '<em style="color:#aaa">Sin asignar</em>'
        aging_rows += f"""
        <tr>
          <td style="font-size:11px;padding:5px 6px;border-bottom:0.5px solid var(--cb)">{r['issue_key']}</td>
          <td style="padding:5px 6px;border-bottom:0.5px solid var(--cb)">
            <span style="font-size:10px;padding:2px 6px;border-radius:4px;
              background:#E6F1FB;color:#185FA5">{r['issue_type']}</span></td>
          <td style="font-size:11px;padding:5px 6px;border-bottom:0.5px solid var(--cb)">{r['status']}</td>
          <td style="font-size:11px;padding:5px 6px;border-bottom:0.5px solid var(--cb)">{assignee}</td>
          <td style="font-size:11px;padding:5px 6px;border-bottom:0.5px solid var(--cb);font-weight:500">{r['sprint_age']}d</td>
          <td style="padding:5px 6px;border-bottom:0.5px solid var(--cb)">
            <div style="width:70px;height:5px;background:#eee;border-radius:3px">
              <div style="width:{pct}%;height:100%;background:{color};border-radius:3px"></div>
            </div>
          </td>
        </tr>"""

    # assignee load
    assignee_rows = ''
    max_load = max(ao.values()) if ao else 1
    colors_pool = ['#378ADD','#534AB7','#D85A30','#1D9E75','#EF9F27','#B4B2A9']
    for i, (name, count) in enumerate(sorted(ao.items(), key=lambda x: -x[1])):
        pct = round(count / max_load * 100)
        initials = ''.join(w[0].upper() for w in name.split() if len(w) > 1)[:2]
        color = '#B4B2A9' if name == 'Sin asignar' else colors_pool[i % len(colors_pool)]
        bar_color = '#D85A30' if count == max_load and count > 5 else color
        assignee_rows += f"""
        <div style="display:flex;align-items:center;gap:10px;padding:6px 0;
            border-bottom:0.5px solid var(--cb);font-size:12px">
          <div style="width:26px;height:26px;border-radius:50%;background:#E6F1FB;
              display:flex;align-items:center;justify-content:center;
              font-size:10px;font-weight:500;color:#185FA5;flex-shrink:0">{initials}</div>
          <div style="flex:1;color:var(--ct)">{name}</div>
          <div style="width:90px;height:6px;background:var(--cs);border-radius:3px">
            <div style="width:{pct}%;height:100%;background:{bar_color};border-radius:3px"></div>
          </div>
          <div style="font-size:11px;color:var(--cs2);min-width:28px;text-align:right">{count}</div>
        </div>"""

    sc_labels = js_json(list(sc.keys()))
    sc_data   = js_json(list(sc.values()))
    sc_colors = js_json([status_color(s) for s in sc.keys()])
    tp_labels = js_json(tp['labels'])
    tp_data   = js_json(tp['data'])
    tp_colors_str = '[' + ','.join(tp_colors) + ']'
    scatter_json = js_json(si)
    granularity_label = f"{'Diario' if tp['granularity']=='daily' else 'Semanal'} · {m['duration_days']}d"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Flow Metrics — {m['sprint_name']}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
:root {{
  --ct: #1a1a18; --cs: #f1efe8; --cs2: #73726c; --cb: rgba(0,0,0,0.08);
  --cbg: #ffffff; --cr: #8px; --crl: 12px;
}}
@media (prefers-color-scheme: dark) {{
  :root {{ --ct: #e8e6de; --cs: #2c2c2a; --cs2: #8a8880; --cb: rgba(255,255,255,0.08); --cbg: #1a1a18; }}
}}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family: system-ui, -apple-system, sans-serif; background:var(--cs); color:var(--ct); padding:1.5rem; }}
.tabs {{ display:flex; gap:4px; margin-bottom:1.25rem; }}
.tab {{ font-size:12px; padding:5px 14px; border-radius:var(--cr); border:0.5px solid var(--cb);
  background:transparent; cursor:pointer; color:var(--cs2); transition:all .15s; }}
.tab.active {{ background:var(--cbg); color:var(--ct); font-weight:500; }}
.view {{ display:none; }}
.view.active {{ display:block; }}
.section-hdr {{ display:flex; align-items:baseline; gap:8px; margin-bottom:.75rem;
  border-bottom:0.5px solid var(--cb); padding-bottom:.35rem; }}
.stitle {{ font-size:11px; font-weight:500; color:var(--cs2); letter-spacing:.07em; text-transform:uppercase; }}
.ssub {{ font-size:11px; color:var(--cs2); opacity:.7; }}
.kpis {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; margin-bottom:1.25rem; }}
.kpi {{ background:var(--cs); border-radius:var(--cr); padding:11px 13px; position:relative; }}
.kpi-lbl {{ font-size:10px; color:var(--cs2); margin-bottom:4px; text-transform:uppercase; letter-spacing:.06em; }}
.kpi-val {{ font-size:22px; font-weight:500; line-height:1; }}
.kpi-unit {{ font-size:12px; color:var(--cs2); margin-left:2px; }}
.kpi-delta {{ font-size:11px; margin-top:4px; }}
.bad {{ color:#D85A30; }} .good {{ color:#1D9E75; }} .neutral {{ color:var(--cs2); }}
.dot {{ position:absolute; top:9px; right:9px; width:7px; height:7px; border-radius:50%; }}
.dot.red {{ background:#D85A30; }} .dot.amber {{ background:#EF9F27; }} .dot.green {{ background:#1D9E75; }}
.row2 {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:1.25rem; }}
.card {{ background:var(--cbg); border:0.5px solid var(--cb); border-radius:var(--crl); padding:.875rem 1rem; }}
.ctitle {{ font-size:13px; font-weight:500; margin-bottom:2px; }}
.csub {{ font-size:11px; color:var(--cs2); margin-bottom:10px; }}
.legend {{ display:flex; flex-wrap:wrap; gap:10px; margin-bottom:7px; font-size:11px; color:var(--cs2); }}
.legend span {{ display:flex; align-items:center; gap:4px; }}
.ldot {{ width:8px; height:8px; border-radius:2px; display:inline-block; }}
.pill {{ font-size:10px; padding:2px 8px; border-radius:20px; border:0.5px solid var(--cb);
  color:var(--cs2); background:var(--cs); margin-left:auto; }}
.insight {{ margin-top:.75rem; padding:.6rem .875rem; background:var(--cs); border-radius:var(--cr);
  font-size:12px; color:var(--cs2); line-height:1.6; }}
.insight strong {{ color:var(--ct); font-weight:500; }}
.narrative {{ border-left:2.5px solid #378ADD; padding:.7rem 1rem; background:var(--cs);
  border-radius:0 var(--cr) var(--cr) 0; margin-bottom:1.25rem; }}
.narrative .nlbl {{ font-size:10px; font-weight:500; color:#378ADD; margin-bottom:5px;
  text-transform:uppercase; letter-spacing:.07em; }}
.narrative p {{ font-size:13px; line-height:1.6; margin-bottom:5px; }}
.narrative p:last-child {{ margin-bottom:0; }}
.narrative strong {{ font-weight:500; }}
.exec-block {{ border:0.5px solid var(--cb); border-radius:var(--crl); overflow:hidden; margin-bottom:1.25rem; }}
.exec-hdr {{ background:var(--cs); padding:.5rem 1rem; display:flex; align-items:center;
  gap:8px; border-bottom:0.5px solid var(--cb); }}
.exec-hdr-dot {{ width:7px; height:7px; border-radius:50%; background:#378ADD; }}
.exec-lbl {{ font-size:10px; font-weight:500; text-transform:uppercase; letter-spacing:.07em; color:var(--cs2); }}
.exec-body {{ padding:.875rem 1rem; font-size:13px; line-height:1.65; }}
.exec-body strong {{ font-weight:500; }}
.controls {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:.75rem; align-items:center; }}
.ctrl-lbl {{ font-size:11px; color:var(--cs2); text-transform:uppercase; letter-spacing:.06em; margin-right:2px; }}
.fbtn {{ font-size:11px; padding:4px 10px; border-radius:var(--cr); border:0.5px solid var(--cb);
  background:transparent; cursor:pointer; color:var(--cs2); transition:all .15s; }}
.fbtn.active {{ background:var(--cs); color:var(--ct); font-weight:500; }}
.slegend {{ display:flex; flex-wrap:wrap; gap:12px; margin-bottom:.6rem; font-size:11px; color:var(--cs2); }}
.slegend span {{ display:flex; align-items:center; gap:5px; cursor:pointer; user-select:none; }}
.sldot {{ width:9px; height:9px; border-radius:50%; flex-shrink:0; }}
.szones {{ display:flex; gap:16px; margin-top:.5rem; font-size:11px; color:var(--cs2); }}
.szones .z {{ display:flex; align-items:center; gap:5px; }}
.zline {{ width:18px; border-top:1.5px dashed; }}
.ttip {{ position:absolute; pointer-events:none; display:none; background:var(--cbg);
  border:0.5px solid var(--cb); border-radius:var(--cr); padding:8px 12px;
  font-size:12px; color:var(--ct); z-index:10; white-space:nowrap; }}
.ttip-key {{ font-weight:500; margin-bottom:3px; }}
.ttip-row {{ color:var(--cs2); font-size:11px; line-height:1.65; }}
table {{ width:100%; border-collapse:collapse; }}
th {{ font-size:10px; color:var(--cs2); font-weight:500; text-align:left;
  padding:4px 6px; border-bottom:0.5px solid var(--cb); }}
</style>
</head>
<body>

<div style="margin-bottom:1.25rem">
  <div style="font-size:18px;font-weight:500;margin-bottom:4px">{m['sprint_name']}</div>
  <div style="font-size:12px;color:var(--cs2)">{m['sprint_start']} → {m['sprint_end']} · {m['total_items']} ítems · Generado {m['generated_at']}</div>
</div>

<div class="tabs">
  <button class="tab active" onclick="switchTab('team')">Uso interno</button>
  <button class="tab" onclick="switchTab('exec')">Para dirección</button>
</div>

<!-- TEAM VIEW -->
<div id="view-team" class="view active">

  {leftover_html}
  {unassigned_html}

  <div class="section-hdr"><span class="stitle">Métricas clave</span></div>
  <div class="kpis">
    <div class="kpi"><div class="dot {dot_lt}"></div>
      <div class="kpi-lbl">Aging medio (sprint)</div>
      <div><span class="kpi-val">{k['avg_sprint_age']}</span><span class="kpi-unit">días</span></div>
      <div class="kpi-delta neutral">Relativo al inicio del sprint</div></div>
    <div class="kpi"><div class="dot {dot_done}"></div>
      <div class="kpi-lbl">Completados</div>
      <div><span class="kpi-val">{k['total_closed']}</span><span class="kpi-unit">/ {m['total_items']} ({k['pct_done']}%)</span></div>
      <div class="kpi-delta {'good' if k['pct_done']>=70 else 'neutral' if k['pct_done']>=40 else 'bad'}">{'↑ Buen avance' if k['pct_done']>=70 else '→ Avance parcial' if k['pct_done']>=40 else '↓ Sprint en riesgo'}</div></div>
    <div class="kpi"><div class="dot {dot_wip}"></div>
      <div class="kpi-lbl">WIP aging medio</div>
      <div><span class="kpi-val">{k['avg_wip_age']}</span><span class="kpi-unit">días</span></div>
      <div class="kpi-delta {'bad' if k['avg_wip_age']>10 else 'neutral'}">{k['total_open']} ítems abiertos</div></div>
    <div class="kpi"><div class="dot {dot_lo}"></div>
      <div class="kpi-lbl">Leftovers</div>
      <div><span class="kpi-val">{k['leftovers_total']}</span><span class="kpi-unit">/ {m['total_items']} ítems</span></div>
      <div class="kpi-delta {'bad' if k['leftovers_open']>3 else 'neutral' if k['leftovers_open']>0 else 'good'}">{k['leftovers_open']} aún sin cerrar</div></div>
  </div>

  <div class="row2">
    <div class="card">
      <div style="display:flex;align-items:baseline;justify-content:space-between">
        <div><div class="ctitle">Throughput</div><div class="csub">{'Ítems cerrados por día' if tp['granularity']=='daily' else 'Ítems cerrados por semana'}</div></div>
        <span class="pill">{granularity_label}</span>
      </div>
      <div class="legend">
        <span><span class="ldot" style="background:#378ADD"></span>Cerrados</span>
        <span><span class="ldot" style="background:#EF9F27;border-radius:0;width:18px;height:2px;margin-top:3px"></span>Período activo</span>
      </div>
      <div style="position:relative;width:100%;height:150px"><canvas id="chart-tp"></canvas></div>
      <div class="insight">{tp_insight}</div>
    </div>
    <div class="card">
      <div class="ctitle">Estado del sprint</div>
      <div class="csub">Distribución de ítems</div>
      <div style="position:relative;width:100%;height:150px"><canvas id="chart-status"></canvas></div>
    </div>
  </div>

  <div class="card" style="margin-bottom:1.25rem">
    <div class="ctitle">Carga por persona</div>
    <div class="csub" style="margin-bottom:8px">Ítems abiertos actualmente</div>
    {assignee_rows}
  </div>

  <!-- Scatter -->
  <div class="card" style="margin-bottom:1.25rem">
    <div class="ctitle">Aging de ítems — sin estado New</div>
    <div class="csub">Ítems activos (Open, Closed, Rejected) · hover para detalle</div>
    <div class="controls">
      <span class="ctrl-lbl">Color por</span>
      <button class="fbtn active" onclick="setScatterMode('status')">Estado</button>
      <button class="fbtn" onclick="setScatterMode('assignee')">Asignado</button>
      <button class="fbtn" onclick="setScatterMode('type')">Tipo</button>
    </div>
    <div class="slegend" id="scatter-legend"></div>
    <div style="position:relative;width:100%;height:260px">
      <canvas id="scatter-a"></canvas>
      <div class="ttip" id="ttip-a"><div class="ttip-key" id="ttip-a-key"></div><div class="ttip-row" id="ttip-a-row"></div></div>
    </div>
    <div class="szones">
      <div class="z"><div class="zline" style="border-color:#EF9F27"></div><span>Riesgo moderado (14d)</span></div>
      <div class="z"><div class="zline" style="border-color:#D85A30"></div><span>Riesgo alto (28d)</span></div>
    </div>
  </div>

  <!-- Aging WIP table -->
  <div class="card" style="margin-bottom:1.25rem">
    <div class="ctitle">Ítems WIP más antiguos</div>
    <div class="csub" style="margin-bottom:8px">Top 8 por aging sprint-relativo</div>
    <table><thead><tr><th>Ítem</th><th>Tipo</th><th>Estado</th><th>Asignado</th><th>Días</th><th>Aging</th></tr></thead>
    <tbody>{aging_rows}</tbody></table>
  </div>

  <!-- Narrative SM -->
  <div class="section-hdr"><span class="stitle">Análisis del SM</span><span class="ssub">Sin filtros</span></div>
  <div class="narrative">
    <div class="nlbl">Lo que dicen los datos</div>
    <p id="narrative-text">Generando análisis...</p>
  </div>

</div>

<!-- EXEC VIEW -->
<div id="view-exec" class="view">
  <div class="kpis">
    <div class="kpi">
      <div class="kpi-lbl">Avance sprint</div>
      <div><span class="kpi-val">{k['pct_done']}</span><span class="kpi-unit">%</span></div>
      <div class="kpi-delta {'good' if k['pct_done']>=70 else 'bad'}">{k['total_closed']} de {m['total_items']} cerrados</div></div>
    <div class="kpi">
      <div class="kpi-lbl">Riesgo de entrega</div>
      <div><span class="kpi-val" style="font-size:18px">{'Alto' if k['pct_done']<40 or k['avg_wip_age']>10 else 'Medio' if k['pct_done']<70 else 'Bajo'}</span></div>
      <div class="kpi-delta bad">WIP aging {k['avg_wip_age']}d</div></div>
    <div class="kpi">
      <div class="kpi-lbl">Ítems en riesgo</div>
      <div><span class="kpi-val">{sum(1 for r in data['aging_wip_top8'] if r['sprint_age']>14)}</span></div>
      <div class="kpi-delta bad">+14 días sin resolver</div></div>
    <div class="kpi">
      <div class="kpi-lbl">Sin dueño</div>
      <div><span class="kpi-val">{k['unassigned_open']}</span></div>
      <div class="kpi-delta {'bad' if k['unassigned_open']>0 else 'good'}">{'Ítems sin asignar' if k['unassigned_open']>0 else 'Todo asignado'}</div></div>
  </div>

  <div class="exec-block">
    <div class="exec-hdr"><div class="exec-hdr-dot"></div><span class="exec-lbl">Argumento para dirección</span></div>
    <div class="exec-body" id="exec-text">Generando...</div>
  </div>
</div>

<script>
const DATA = {js_json(data)};
const ITEMS = DATA.scatter_items;
const ACTIVE = ITEMS.filter(d => d.status !== 'New');

const palettes = {{
  status:   {{ 'Open':'#EF9F27','Closed':'#1D9E75','Done':'#1D9E75','Rejected':'#D85A30','New':'#888780','In Progress':'#378ADD' }},
  assignee: {{}},
  type:     {{}}
}};
const COLORS = ['#378ADD','#534AB7','#D85A30','#1D9E75','#EF9F27','#1D9E75','#B4B2A9'];
[...new Set(ITEMS.map(d=>d.assignee))].forEach((a,i) => palettes.assignee[a] = a==='Sin asignar'?'#B4B2A9':COLORS[i%COLORS.length]);
[...new Set(ITEMS.map(d=>d.type))].forEach((t,i) => palettes.type[t] = COLORS[i%COLORS.length]);

let scatterMode = 'status';
let scChart;
const isDark = matchMedia('(prefers-color-scheme: dark)').matches;
const gridC = isDark?'rgba(255,255,255,0.07)':'rgba(0,0,0,0.06)';
const labelC = isDark?'#8a8880':'#73726c';

function switchTab(t) {{
  document.querySelectorAll('.tab').forEach(b => b.classList.toggle('active', b.textContent.trim()===(t==='team'?'Uso interno':'Para dirección')));
  document.getElementById('view-team').classList.toggle('active', t==='team');
  document.getElementById('view-exec').classList.toggle('active', t!=='team');
}}

function waitCanvas(id, fn, r=25) {{
  const el = document.getElementById(id);
  if (el && el.offsetParent!==null) {{ fn(el); return; }}
  if (r>0) setTimeout(()=>waitCanvas(id,fn,r-1), 80);
}}

// Throughput
waitCanvas('chart-tp', el => {{
  new Chart(el, {{
    type:'bar', data:{{ labels:{tp_labels}, datasets:[{{ data:{tp_data}, backgroundColor:{tp_colors_str}, borderRadius:4, borderSkipped:false }}] }},
    options:{{ responsive:true, maintainAspectRatio:false, plugins:{{ legend:{{display:false}}, tooltip:{{bodyFont:{{size:11}},titleFont:{{size:11}}}} }},
      scales:{{ x:{{grid:{{display:false}}, ticks:{{color:labelC, font:{{size:{'9' if tp['granularity']=='daily' else '10'}}}, maxRotation:{'45' if tp['granularity']=='daily' else '0'}, autoSkip:{'true' if tp['granularity']=='daily' else 'false'}}}}},
        y:{{grid:{{color:gridC}}, ticks:{{color:labelC,font:{{size:10}},stepSize:1}}, beginAtZero:true}} }} }} }});
}});

// Status donut
waitCanvas('chart-status', el => {{
  new Chart(el, {{
    type:'doughnut',
    data:{{ labels:{sc_labels}, datasets:[{{ data:{sc_data}, backgroundColor:{sc_colors}, borderWidth:0, hoverOffset:4 }}] }},
    options:{{ responsive:true, maintainAspectRatio:false, cutout:'60%',
      plugins:{{ legend:{{display:true, position:'right', labels:{{font:{{size:10}},color:labelC,boxWidth:8,padding:8}}}}, tooltip:{{bodyFont:{{size:11}}}} }} }} }});
}});

// Scatter
const zonesPlugin = {{ id:'zones', beforeDraw({{ctx,scales:{{x,y}}}}) {{
  const x14=x.getPixelForValue(14), x28=x.getPixelForValue(28), x40=x.getPixelForValue(40);
  const top=y.top, bottom=y.bottom;
  ctx.save();
  ctx.fillStyle=isDark?'rgba(239,159,39,0.07)':'rgba(239,159,39,0.06)';
  ctx.fillRect(x14,top,x28-x14,bottom-top);
  ctx.fillStyle=isDark?'rgba(216,90,48,0.09)':'rgba(216,90,48,0.07)';
  ctx.fillRect(x28,top,x40-x28,bottom-top);
  ctx.strokeStyle='#EF9F27'; ctx.setLineDash([4,4]); ctx.lineWidth=1;
  ctx.beginPath(); ctx.moveTo(x14,top); ctx.lineTo(x14,bottom); ctx.stroke();
  ctx.strokeStyle='#D85A30';
  ctx.beginPath(); ctx.moveTo(x28,top); ctx.lineTo(x28,bottom); ctx.stroke();
  ctx.setLineDash([]); ctx.restore();
}} }};

function buildScatterDatasets(items, mode) {{
  const groups = {{}};
  items.forEach((d,i) => {{
    const k = mode==='status'?d.status:mode==='assignee'?d.assignee:d.type;
    if (!groups[k]) groups[k]=[];
    groups[k].push({{ x:d.age_days, y:Math.sin(i*137.508)*0.42, _d:d }});
  }});
  return Object.entries(groups).map(([label,pts]) => {{
    const c = (palettes[mode][label]||'#B4B2A9');
    return {{ label, data:pts, backgroundColor:c+'bb', borderColor:c, borderWidth:1.5, pointRadius:7, pointHoverRadius:10 }};
  }});
}}

function buildScatterLegend(items, mode) {{
  const leg = document.getElementById('scatter-legend');
  const present = [...new Set(items.map(d => mode==='status'?d.status:mode==='assignee'?d.assignee:d.type))];
  leg.innerHTML = present.map(k => {{
    const c = palettes[mode][k]||'#B4B2A9';
    return `<span onclick="toggleScatterSeries('${{k}}')"><span class="sldot" style="background:${{c}}"></span>${{k}}</span>`;
  }}).join('');
}}

function toggleScatterSeries(label) {{
  scChart.data.datasets.forEach((ds,i) => {{ if(ds.label===label) scChart.getDatasetMeta(i).hidden=!scChart.getDatasetMeta(i).hidden; }});
  scChart.update();
}}

function setScatterMode(m) {{
  scatterMode = m;
  document.querySelectorAll('.fbtn').forEach(b => b.classList.toggle('active', b.textContent.trim()===(m==='status'?'Estado':m==='assignee'?'Asignado':'Tipo')));
  scChart.data.datasets = buildScatterDatasets(ACTIVE, m);
  scChart.update();
  buildScatterLegend(ACTIVE, m);
}}

waitCanvas('scatter-a', el => {{
  scChart = new Chart(el, {{
    type:'scatter', data:{{ datasets: buildScatterDatasets(ACTIVE, scatterMode) }},
    options:{{ responsive:true, maintainAspectRatio:false, animation:{{duration:250}},
      plugins:{{ legend:{{display:false}}, tooltip:{{enabled:false}} }},
      scales:{{ x:{{ title:{{display:true,text:'Edad del ítem (días, relativa al sprint)',color:labelC,font:{{size:11}}}},
        min:-1, max:Math.max(...ACTIVE.map(d=>d.age_days))+3,
        grid:{{color:gridC}}, ticks:{{color:labelC,font:{{size:10}},stepSize:7}} }},
        y:{{ display:false, min:-1.3, max:1.3 }} }} }},
    plugins:[zonesPlugin]
  }});
  buildScatterLegend(ACTIVE, scatterMode);

  const tip = document.getElementById('ttip-a');
  el.addEventListener('mousemove', evt => {{
    const pts = scChart.getElementsAtEventForMode(evt,'nearest',{{intersect:true}},false);
    if (!pts.length) {{ tip.style.display='none'; return; }}
    const d = scChart.data.datasets[pts[0].datasetIndex].data[pts[0].index]._d;
    document.getElementById('ttip-a-key').textContent = d.key;
    document.getElementById('ttip-a-row').innerHTML = `${{d.type}} · ${{d.status}}<br>Asignado: ${{d.assignee}}<br>Edad en sprint: <strong>${{d.age_days}} días</strong>${{d.is_leftover?' · <em>leftover</em>':''}}`;
    const wrap = el.parentElement.getBoundingClientRect();
    let left = evt.clientX-wrap.left+14;
    if(left+230>wrap.width) left=evt.clientX-wrap.left-240;
    tip.style.left=left+'px'; tip.style.top=(evt.clientY-wrap.top-10)+'px'; tip.style.display='block';
  }});
  el.addEventListener('mouseleave', ()=>{{ tip.style.display='none'; }});
}});

// Narrative generation
function buildNarrative(data) {{
  const k = data.kpis, tp = data.throughput, m = data.meta;
  const unassigned = k.unassigned_open;
  const cliff = tp.cliff_effect;
  const topPerson = Object.entries(data.assignee_open).sort((a,b)=>b[1]-a[1])[0];
  let txt = '';
  if (k.pct_done < 40) txt += `El sprint tiene un <strong>riesgo de entrega alto</strong> — solo el ${{k.pct_done}}% completado. `;
  else txt += `El sprint lleva un ${{k.pct_done}}% completado. `;
  if (cliff) txt += `El throughput muestra <strong>cliff effect</strong>: el ${{Math.round(tp.peak_val/Math.max(tp.total,1)*100)}}% de los cierres ocurrió en el período ${{tp.peak_label}}. El trabajo se acumula y se resuelve en ráfaga. `;
  if (unassigned > 0) txt += `<strong>${{unassigned}} ítems abiertos sin asignado</strong> — nadie los va a cerrar solo. Requieren owner inmediato. `;
  if (topPerson && topPerson[1] > Object.values(data.assignee_open).reduce((a,b)=>a+b,0)*0.4)
    txt += `<strong>${{topPerson[0]}}</strong> acumula ${{topPerson[1]}} de los ${{k.total_open}} ítems abiertos — revisar distribución o posible bloqueo. `;
  if (k.leftovers_open > 0) txt += `Hay ${{k.leftovers_open}} leftovers del sprint anterior sin cerrar — están consumiendo capacidad de este sprint. `;
  return txt || 'Sin alertas críticas detectadas en este sprint.';
}}

function buildExec(data) {{
  const k = data.kpis, tp = data.throughput, m = data.meta;
  const risk = k.pct_done<40||k.avg_wip_age>10?'alto':k.pct_done<70?'medio':'bajo';
  return `El Sprint <strong>${{m.sprint_name}}</strong> tiene un riesgo de entrega <strong>${{risk}}</strong>.
  El equipo lleva el ${{k.pct_done}}% del trabajo cerrado con un aging medio de ${{k.avg_wip_age}} días en los ítems abiertos.<br><br>
  ${{tp.cliff_effect?`El patrón de entrega muestra trabajo acumulado que se resuelve en ráfaga al final del sprint — no es predecible ni sostenible a largo plazo.<br><br>`:`El throughput es razonablemente distribuido a lo largo del sprint.<br><br>`}}
  ${{k.unassigned_open>0?`Acción inmediata recomendada: asignar los <strong>${{k.unassigned_open}} ítems sin responsable</strong> antes de fin de jornada. Sin dueño no hay entrega.`:`Todos los ítems activos tienen responsable asignado.`}}`;
}}

document.getElementById('narrative-text').innerHTML = buildNarrative(DATA);
document.getElementById('exec-text').innerHTML = buildExec(DATA);
</script>
</body>
</html>"""


# ── Report HTML (imprimible como PDF) ─────────────────────────────────────────

def build_report(data):
    m  = data['meta']
    k  = data['kpis']
    tp = data['throughput']
    sc = data['status_counts']

    sc_labels = js_json(list(sc.keys()))
    sc_data   = js_json(list(sc.values()))
    sc_colors = js_json([status_color(s) for s in sc.keys()])
    tp_labels = js_json(tp['labels'])
    tp_data   = js_json(tp['data'])
    tp_colors = '[' + ','.join(['"#EF9F27"' if l == tp['current_period'] else '"#378ADD"' for l in tp['labels']]) + ']'

    risk = 'Alto' if k['pct_done'] < 40 or k['avg_wip_age'] > 10 else 'Medio' if k['pct_done'] < 70 else 'Bajo'
    risk_color = '#D85A30' if risk == 'Alto' else '#EF9F27' if risk == 'Medio' else '#1D9E75'

    if tp['cliff_effect']:
        pct = round(tp['peak_val'] / max(tp['total'], 1) * 100)
        exec_txt = f"""El sprint lleva el {k['pct_done']}% completado con {k['total_closed']} de {m['total_items']} ítems cerrados.
        El patrón de throughput muestra cliff effect: el {pct}% de los cierres se concentró en {tp['peak_label']}.
        El trabajo se acumula durante el sprint y se resuelve en ráfaga al final — señal de WIP alto o falta de foco continuo."""
    else:
        exec_txt = f"""El sprint lleva el {k['pct_done']}% completado con {k['total_closed']} de {m['total_items']} ítems cerrados.
        El throughput se distribuye de forma razonable a lo largo del sprint.
        El WIP aging medio es de {k['avg_wip_age']} días — {'por encima del umbral recomendado, revisar bloqueos.' if k['avg_wip_age'] > 10 else 'dentro de rangos aceptables.'}"""

    if k['unassigned_open'] > 0:
        exec_txt += f" Acción recomendada: asignar los {k['unassigned_open']} ítems sin responsable."

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Informe Sprint — {m['sprint_name']}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family: system-ui, -apple-system, sans-serif; color:#1a1a18; background:#fff; padding:2rem 2.5rem; max-width:900px; margin:0 auto; }}
.print-hint {{ background:#E6F1FB; border:0.5px solid #B5D4F4; border-radius:8px; padding:.6rem 1rem;
  font-size:12px; color:#185FA5; margin-bottom:1.5rem; display:flex; align-items:center; gap:8px; }}
.header {{ border-bottom:2px solid #1a1a18; padding-bottom:.75rem; margin-bottom:1.5rem; display:flex; justify-content:space-between; align-items:flex-end; }}
.sprint-name {{ font-size:20px; font-weight:500; }}
.sprint-meta {{ font-size:11px; color:#73726c; text-align:right; line-height:1.6; }}
.kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:1.5rem; }}
.kpi {{ border:0.5px solid #D3D1C7; border-radius:8px; padding:12px 14px; }}
.kpi-lbl {{ font-size:10px; color:#73726c; text-transform:uppercase; letter-spacing:.06em; margin-bottom:4px; }}
.kpi-val {{ font-size:24px; font-weight:500; line-height:1; }}
.kpi-unit {{ font-size:12px; color:#73726c; margin-left:2px; }}
.kpi-delta {{ font-size:11px; margin-top:4px; color:#73726c; }}
.charts-row {{ display:grid; grid-template-columns:3fr 2fr; gap:16px; margin-bottom:1.5rem; }}
.chart-card {{ border:0.5px solid #D3D1C7; border-radius:8px; padding:.875rem 1rem; }}
.ctitle {{ font-size:12px; font-weight:500; margin-bottom:2px; }}
.csub {{ font-size:10px; color:#73726c; margin-bottom:10px; }}
.exec-block {{ border:0.5px solid #D3D1C7; border-radius:8px; overflow:hidden; margin-bottom:1.5rem; }}
.exec-hdr {{ background:#F1EFE8; padding:.5rem 1rem; font-size:10px; font-weight:500;
  text-transform:uppercase; letter-spacing:.07em; color:#73726c;
  border-bottom:0.5px solid #D3D1C7; display:flex; align-items:center; gap:8px; }}
.exec-body {{ padding:.875rem 1rem; font-size:13px; line-height:1.7; color:#1a1a18; }}
.risk-badge {{ display:inline-block; font-size:11px; font-weight:500; padding:3px 10px;
  border-radius:20px; color:#fff; margin-left:8px; }}
.footer {{ border-top:0.5px solid #D3D1C7; padding-top:.75rem; font-size:10px; color:#73726c;
  display:flex; justify-content:space-between; }}
@media print {{
  .print-hint {{ display:none; }}
  body {{ padding:1rem 1.5rem; }}
}}
</style>
</head>
<body>

<div class="print-hint">
  🖨 Para exportar como PDF: <strong>Ctrl+P</strong> (Windows/Linux) o <strong>Cmd+P</strong> (Mac) → Guardar como PDF
</div>

<div class="header">
  <div>
    <div class="sprint-name">{m['sprint_name']}</div>
    <div style="font-size:12px;color:#73726c;margin-top:3px">{m['sprint_start']} → {m['sprint_end']} · {m['duration_days']} días</div>
  </div>
  <div class="sprint-meta">
    {m['total_items']} ítems en el sprint<br>
    Riesgo de entrega: <span class="risk-badge" style="background:{risk_color}">{risk}</span><br>
    Generado el {m['generated_at']}
  </div>
</div>

<div class="kpis">
  <div class="kpi">
    <div class="kpi-lbl">Completados</div>
    <div><span class="kpi-val">{k['total_closed']}</span><span class="kpi-unit">/ {m['total_items']}</span></div>
    <div class="kpi-delta">{k['pct_done']}% del sprint</div>
  </div>
  <div class="kpi">
    <div class="kpi-lbl">WIP aging medio</div>
    <div><span class="kpi-val">{k['avg_wip_age']}</span><span class="kpi-unit">días</span></div>
    <div class="kpi-delta">{k['total_open']} ítems abiertos</div>
  </div>
  <div class="kpi">
    <div class="kpi-lbl">Leftovers</div>
    <div><span class="kpi-val">{k['leftovers_total']}</span><span class="kpi-unit">ítems</span></div>
    <div class="kpi-delta">{k['leftovers_open']} sin cerrar</div>
  </div>
  <div class="kpi">
    <div class="kpi-lbl">Sin asignar</div>
    <div><span class="kpi-val">{k['unassigned_open']}</span><span class="kpi-unit">abiertos</span></div>
    <div class="kpi-delta">{'Requieren owner' if k['unassigned_open']>0 else 'Todo asignado'}</div>
  </div>
</div>

<div class="charts-row">
  <div class="chart-card">
    <div class="ctitle">Throughput</div>
    <div class="csub">{'Por día' if tp['granularity']=='daily' else 'Por semana'} · período activo en naranja</div>
    <div style="position:relative;width:100%;height:140px"><canvas id="rpt-tp"></canvas></div>
  </div>
  <div class="chart-card">
    <div class="ctitle">Estado</div>
    <div class="csub">Distribución de ítems</div>
    <div style="position:relative;width:100%;height:140px"><canvas id="rpt-status"></canvas></div>
  </div>
</div>

<div class="exec-block">
  <div class="exec-hdr"><span style="width:7px;height:7px;border-radius:50%;background:#378ADD;display:inline-block"></span>Resumen ejecutivo</div>
  <div class="exec-body">{exec_txt}</div>
</div>

<div class="footer">
  <span>Flow Metrics Skill · Sprint ERNI — generado automáticamente desde CSV de Jira</span>
  <span>Cycle time como proxy vía campo Updated · Para análisis completo usar API de Jira</span>
</div>

<script>
const isDark = false;
const labelC = '#73726c';
const gridC = 'rgba(0,0,0,0.06)';

function waitCanvas(id, fn, r=25) {{
  const el = document.getElementById(id);
  if (el) {{ fn(el); return; }}
  if (r>0) setTimeout(()=>waitCanvas(id,fn,r-1), 80);
}}

waitCanvas('rpt-tp', el => {{
  new Chart(el, {{
    type:'bar', data:{{ labels:{tp_labels}, datasets:[{{ data:{tp_data}, backgroundColor:{tp_colors}, borderRadius:3, borderSkipped:false }}] }},
    options:{{ responsive:true, maintainAspectRatio:false,
      plugins:{{ legend:{{display:false}}, tooltip:{{bodyFont:{{size:10}},titleFont:{{size:10}}}} }},
      scales:{{ x:{{ grid:{{display:false}}, ticks:{{color:labelC,font:{{size:9}},maxRotation:45}} }},
        y:{{ grid:{{color:gridC}}, ticks:{{color:labelC,font:{{size:9}},stepSize:1}}, beginAtZero:true }} }} }} }});
}});

waitCanvas('rpt-status', el => {{
  new Chart(el, {{
    type:'doughnut', data:{{ labels:{sc_labels}, datasets:[{{ data:{sc_data}, backgroundColor:{sc_colors}, borderWidth:0, hoverOffset:3 }}] }},
    options:{{ responsive:true, maintainAspectRatio:false, cutout:'58%',
      plugins:{{ legend:{{display:true,position:'right',labels:{{font:{{size:9}},color:labelC,boxWidth:7,padding:6}}}}, tooltip:{{bodyFont:{{size:10}}}} }} }} }});
}});
</script>
</body>
</html>"""


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Genera dashboard.html y report.html')
    parser.add_argument('--data', required=True, help='JSON de análisis (salida de analyze_csv.py)')
    parser.add_argument('--output-dir', default='.', help='Directorio de salida')
    args = parser.parse_args()

    with open(args.data, encoding='utf-8') as f:
        data = json.load(f)

    os.makedirs(args.output_dir, exist_ok=True)

    dashboard_path = os.path.join(args.output_dir, 'dashboard.html')
    report_path    = os.path.join(args.output_dir, 'report.html')

    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(build_dashboard(data))
    print(f"Dashboard: {dashboard_path}")

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(build_report(data))
    print(f"Report:    {report_path}")


if __name__ == '__main__':
    main()
