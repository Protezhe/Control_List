#!/usr/bin/env python3
import csv
import json
from datetime import datetime
from pathlib import Path

HTML_TEMPLATE = """<!doctype html>
<html lang=\"ru\">
<head>
<meta charset=\"utf-8\">
<title>{title}</title>
<style>
:root {{
  --paper: #f7f2e9;
  --ink: #1f1a14;
  --muted: #6d6155;
  --accent: #b45d3a;
  --border: #2b241d;
  --line: #c9b9a9;
  --check: #1f1a14;
}}
* {{ box-sizing: border-box; }}
body {{
  font-family: "PT Serif", "Georgia", serif;
  color: var(--ink);
  margin: 26px 34px;
  background:
    radial-gradient(circle at 12px 12px, rgba(180, 93, 58, 0.08) 1px, transparent 1.5px) 0 0 / 12px 12px,
    linear-gradient(0deg, rgba(0,0,0,0.02), rgba(0,0,0,0.02)),
    var(--paper);
}}
.header {{
  border: 2px solid var(--border);
  padding: 10px 12px;
  margin-bottom: 12px;
  background: linear-gradient(0deg, rgba(180, 93, 58, 0.08), rgba(180, 93, 58, 0.04));
}}
.month {{ text-align: right; color: var(--muted); font-size: 12px; letter-spacing: 0.2px; }}
.title {{
  font-weight: 700;
  text-align: center;
  margin: 6px 0 4px;
  font-size: 16px;
}}
.subtitle {{
  text-align: center;
  color: var(--muted);
  font-size: 12px;
  letter-spacing: 0.4px;
}}
.section {{
  border: 1px solid var(--line);
  padding: 10px 12px;
  margin: 10px 0;
  background: rgba(255,255,255,0.6);
}}
.block {{ margin: 6px 0; }}
.signature {{ margin: 6px 0; }}
.signature-line {{ display: inline-block; border-bottom: 1px solid var(--border); min-width: 260px; height: 14px; vertical-align: middle; }}
.notes {{ margin: 8px 0 12px; }}
.notes p {{ margin: 4px 0; }}
.checklist {{ width: 100%; border-collapse: collapse; margin: 8px 0 12px; }}
.checklist th {{
  text-align: left;
  border-bottom: 2px solid var(--border);
  padding: 8px 8px;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
}}
.checklist td {{
  border-bottom: 1px solid var(--line);
  padding: 8px 8px;
  vertical-align: top;
}}
.check-col {{ width: 44px; text-align: center; color: var(--check); font-size: 16px; }}
.footer {{ margin-top: 8px; }}
.footer p {{ margin: 4px 0; }}
.defects {{ margin-top: 10px; }}
.defects-line {{ border-bottom: 1px solid var(--border); height: 16px; margin-top: 6px; }}
.stamp {{
  display: inline-block;
  border: 2px solid var(--accent);
  color: var(--accent);
  padding: 2px 8px;
  font-size: 11px;
  letter-spacing: 0.6px;
  text-transform: uppercase;
}}
@media print {{
  body {{ margin: 12mm; }}
}}
</style>
</head>
<body>
<div class=\"header\">
  <div class=\"month\">{month}</div>
  <div class=\"title\">{title}</div>
  <div class=\"subtitle\">Ежемесячное техническое обслуживание (ТО-1)</div>
</div>

<div class=\"section\">
  <div>Лица, принимающие участие в техническом обслуживании (ФИО, профессия/должность) - Ефремов Евгений Олегович Иженер по обслуживанию ИТ-оборудования, систем освещения и мультимедийного оборудования</div>
  <div class=\"signature\"><span class=\"signature-line\"></span> Образец подписи</div>
</div>

<div class=\"section notes\">
{warnings}
</div>

<table class=\"checklist\">
  <thead>
    <tr>
      <th class=\"check-col\">Галочка</th>
      <th>Наименование прибора</th>
      <th>Наименование операции по техническому обслуживанию</th>
    </tr>
  </thead>
  <tbody>
{rows}
  </tbody>
</table>

<div class=\"section footer\">
{closing}
</div>

<div class=\"defects section\">
  <div><span class=\"stamp\">Выявленные недостатки</span></div>
  <div class=\"defects-line\"></div>
  <div class=\"defects-line\"></div>
  <div class=\"defects-line\"></div>
</div>
</body>
</html>
"""


def load_meta():
    with open("data/checklists_meta.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_items():
    items = {}
    with open("data/checklist_items.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.setdefault(row["sheet_id"], []).append(row)
    return items


def current_month_year_ru():
    months = [
        "январь",
        "февраль",
        "март",
        "апрель",
        "май",
        "июнь",
        "июль",
        "август",
        "сентябрь",
        "октябрь",
        "ноябрь",
        "декабрь",
    ]
    now = datetime.now()
    return f"{months[now.month - 1]} {now.year} г."


def format_paragraphs(lines):
    return "\n".join(f"  <p>{line}</p>" for line in lines if line)


def format_rows(items):
    rows = []
    for item in items:
        rows.append(
            "    <tr>\n"
            "      <td class=\"check-col\">&#x2611;</td>\n"
            f"      <td>{item['device']}</td>\n"
            f"      <td>{item['operation']}</td>\n"
            "    </tr>"
        )
    return "\n".join(rows)


def main():
    meta = load_meta()
    items_by_sheet = load_items()
    Path("out").mkdir(exist_ok=True)

    for sheet in meta["sheets"]:
        sheet_id = sheet["id"]
        html = HTML_TEMPLATE.format(
            month=current_month_year_ru(),
            title=sheet.get("title", sheet_id),
            warnings=format_paragraphs(sheet.get("warnings", [])),
            rows=format_rows(items_by_sheet.get(sheet_id, [])),
            closing=format_paragraphs(sheet.get("closing", [])),
        )
        out_path = Path("out") / f"{sheet_id}.html"
        out_path.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
