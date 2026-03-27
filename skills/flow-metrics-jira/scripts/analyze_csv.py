#!/usr/bin/env python3
"""
analyze_csv.py — Extrae métricas de flujo de un CSV de Jira.
Uso: python3 scripts/analyze_csv.py <ruta_csv> [--sprint-start YYYY-MM-DD] [--sprint-end YYYY-MM-DD]
Salida: JSON con todas las métricas listo para generate_outputs.py
"""

import sys
import json
import argparse
import pandas as pd
from datetime import datetime, date

DATE_FORMAT = '%d/%b/%y %I:%M %p'

def parse_date(s):
    if pd.isna(s) or s == '':
        return None
    try:
        return datetime.strptime(str(s).strip(), DATE_FORMAT)
    except ValueError:
        return None

def iso_week_label(dt):
    return f"Sem {dt.isocalendar()[1]}"

def analyze(csv_path, sprint_start=None, sprint_end=None):
    df = pd.read_csv(csv_path)

    # -- Campos clave ----------------------------------------------------------
    df['created_dt']  = df['Created'].apply(parse_date)
    df['resolved_dt'] = df['Resolved'].apply(parse_date)
    df['updated_dt']  = df['Updated'].apply(parse_date)
    df['assignee']    = df['Assignee'].fillna('Sin asignar')
    df['status']      = df['Status'].fillna('Unknown')
    df['issue_type']  = df['Issue Type'].fillna('Unknown')
    df['issue_key']   = df['Issue key']

    now = datetime.now()

    # -- Fechas del sprint -----------------------------------------------------
    if sprint_start is None:
        sprint_start = df['created_dt'].min()
        print(f"[AVISO] sprint_start inferido del CSV: {sprint_start.date()}", file=sys.stderr)
    if sprint_end is None:
        sprint_end = now
        print(f"[AVISO] sprint_end inferido como hoy: {sprint_end.date()}", file=sys.stderr)

    sprint_start = datetime.combine(sprint_start, datetime.min.time()) if isinstance(sprint_start, date) else sprint_start
    sprint_end   = datetime.combine(sprint_end,   datetime.min.time()) if isinstance(sprint_end,   date) else sprint_end
    duration_days = (sprint_end - sprint_start).days
    is_short_sprint = duration_days <= 14

    ref_end = min(sprint_end, now)

    # -- Clasificar ítems ------------------------------------------------------
    def sprint_age(row):
        """Aging relativo al sprint (leftovers desde sprint_start)."""
        if row['created_dt'] is None:
            return 0.0
        age_ref = sprint_start if row['created_dt'] < sprint_start else row['created_dt']
        age_end = row['resolved_dt'] if row['resolved_dt'] else ref_end
        return round(max(0, (age_end - age_ref).total_seconds() / 86400), 1)

    df['is_leftover']  = df['created_dt'].apply(lambda d: d < sprint_start if d else False)
    df['sprint_age']   = df.apply(sprint_age, axis=1)
    df['is_closed']    = df['status'].isin(['Closed', 'Done', 'Rejected'])
    df['is_open']      = ~df['is_closed']

    # -- Métricas globales -----------------------------------------------------
    closed   = df[df['is_closed']]
    open_wip = df[df['is_open']]
    leftovers = df[df['is_leftover']]
    leftovers_open = leftovers[leftovers['is_open']]

    lead_times = []
    for _, row in closed.iterrows():
        if row['created_dt'] and row['resolved_dt']:
            lt = (row['resolved_dt'] - row['created_dt']).total_seconds() / 86400
            lead_times.append(round(lt, 1))

    avg_lead_time = round(sum(lead_times) / len(lead_times), 1) if lead_times else 0
    avg_sprint_age = round(df['sprint_age'].mean(), 1) if len(df) else 0
    avg_wip_age    = round(open_wip['sprint_age'].mean(), 1) if len(open_wip) else 0

    # -- Throughput ------------------------------------------------------------
    resolved_in_sprint = df[
        df['resolved_dt'].notna() &
        (df['resolved_dt'] >= sprint_start) &
        (df['resolved_dt'] <= ref_end)
    ]

    if is_short_sprint:
        # Diario
        all_days = pd.date_range(sprint_start, ref_end, freq='D')
        throughput_labels = [d.strftime('%d %b') for d in all_days]
        throughput_data   = []
        for d in all_days:
            ds = d.date()
            count = resolved_in_sprint[resolved_in_sprint['resolved_dt'].apply(
                lambda x: x.date() == ds if x else False
            )].shape[0]
            throughput_data.append(count)
        current_period = ref_end.strftime('%d %b')
    else:
        # Semanal
        week_map = {}
        for _, row in resolved_in_sprint.iterrows():
            wk = iso_week_label(row['resolved_dt'])
            week_map[wk] = week_map.get(wk, 0) + 1

        all_days = pd.date_range(sprint_start, ref_end, freq='D')
        week_order = []
        for d in all_days:
            wk = iso_week_label(d)
            if wk not in week_order:
                week_order.append(wk)

        throughput_labels = week_order
        throughput_data   = [week_map.get(wk, 0) for wk in week_order]
        current_period    = iso_week_label(ref_end)

    # -- Cliff effect ----------------------------------------------------------
    total_tp = sum(throughput_data)
    peak_val = max(throughput_data) if throughput_data else 0
    prev_vals = [v for v in throughput_data[:-1] if v > 0]
    avg_prev  = sum(prev_vals) / len(prev_vals) if prev_vals else 0
    cliff_effect = peak_val > 2.5 * avg_prev if avg_prev > 0 else False
    peak_label = throughput_labels[throughput_data.index(peak_val)] if throughput_data else ''

    # -- Distribución por estado -----------------------------------------------
    status_counts = df['status'].value_counts().to_dict()

    # -- Distribución por tipo -------------------------------------------------
    type_counts = df['issue_type'].value_counts().to_dict()

    # -- Carga por asignado ----------------------------------------------------
    assignee_open = open_wip['assignee'].value_counts().to_dict()

    # -- Aging items para scatter ----------------------------------------------
    scatter_items = []
    for _, row in df.iterrows():
        scatter_items.append({
            'key':       row['issue_key'],
            'type':      row['issue_type'],
            'status':    row['status'],
            'assignee':  row['assignee'],
            'age_days':  row['sprint_age'],
            'is_leftover': bool(row['is_leftover'])
        })

    # -- Ítems más antiguos (WIP) ----------------------------------------------
    aging_wip = open_wip.nlargest(8, 'sprint_age')[
        ['issue_key', 'issue_type', 'status', 'assignee', 'sprint_age']
    ].to_dict('records')

    # -- Sin asignar abiertos --------------------------------------------------
    unassigned_open = open_wip[open_wip['assignee'] == 'Sin asignar']['issue_key'].tolist()

    # -- Nombre del sprint -----------------------------------------------------
    sprint_name = 'Unknown'
    if 'Sprint' in df.columns:
        sprints = df['Sprint'].dropna().value_counts()
        if len(sprints):
            sprint_name = sprints.index[0]

    # -- Output JSON -----------------------------------------------------------
    result = {
        'meta': {
            'sprint_name':     sprint_name,
            'sprint_start':    sprint_start.strftime('%Y-%m-%d'),
            'sprint_end':      sprint_end.strftime('%Y-%m-%d'),
            'duration_days':   duration_days,
            'is_short_sprint': is_short_sprint,
            'total_items':     len(df),
            'generated_at':    now.strftime('%Y-%m-%d %H:%M'),
        },
        'kpis': {
            'avg_lead_time':   avg_lead_time,
            'avg_sprint_age':  avg_sprint_age,
            'avg_wip_age':     avg_wip_age,
            'total_closed':    int(len(closed)),
            'total_open':      int(len(open_wip)),
            'pct_done':        round(len(closed) / max(len(df), 1) * 100),
            'leftovers_total': int(len(leftovers)),
            'leftovers_open':  int(len(leftovers_open)),
            'unassigned_open': len(unassigned_open),
        },
        'throughput': {
            'labels':         throughput_labels,
            'data':           throughput_data,
            'current_period': current_period,
            'granularity':    'daily' if is_short_sprint else 'weekly',
            'cliff_effect':   cliff_effect,
            'peak_val':       peak_val,
            'peak_label':     peak_label,
            'total':          total_tp,
        },
        'status_counts':   status_counts,
        'type_counts':     type_counts,
        'assignee_open':   assignee_open,
        'scatter_items':   scatter_items,
        'aging_wip_top8':  aging_wip,
        'unassigned_open': unassigned_open,
        'lead_times':      lead_times,
    }

    return result


def main():
    parser = argparse.ArgumentParser(description='Analiza CSV de Jira y extrae métricas de flujo')
    parser.add_argument('csv_path', help='Ruta al CSV de Jira')
    parser.add_argument('--sprint-start', help='Inicio del sprint (YYYY-MM-DD)')
    parser.add_argument('--sprint-end',   help='Fin del sprint (YYYY-MM-DD)')
    parser.add_argument('--output', '-o', help='Fichero de salida JSON (por defecto: stdout)')
    args = parser.parse_args()

    sprint_start = datetime.strptime(args.sprint_start, '%Y-%m-%d') if args.sprint_start else None
    sprint_end   = datetime.strptime(args.sprint_end,   '%Y-%m-%d') if args.sprint_end   else None

    data = analyze(args.csv_path, sprint_start, sprint_end)

    output = json.dumps(data, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Análisis guardado en {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
