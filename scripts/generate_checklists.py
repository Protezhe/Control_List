#!/usr/bin/env python3
import csv
import json
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
  --panel: #fff9f2;
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
.toolbar {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 16px;
  border: 2px solid var(--border);
  padding: 12px;
  margin-bottom: 12px;
  background: var(--panel);
}}
.toolbar label {{ font-size: 12px; color: var(--muted); display: block; margin-bottom: 4px; }}
.toolbar select, .toolbar input, .toolbar textarea {{
  width: 100%;
  border: 1px solid var(--line);
  padding: 6px 8px;
  font-family: "PT Serif", "Georgia", serif;
  font-size: 13px;
  background: #fff;
}}
.toolbar .wide {{ grid-column: 1 / -1; }}
.toolbar .actions {{
  display: flex;
  align-items: end;
  gap: 8px;
}}
.toolbar button {{
  border: 2px solid var(--border);
  background: var(--paper);
  padding: 6px 10px;
  cursor: pointer;
  font-size: 12px;
  letter-spacing: 0.4px;
  text-transform: uppercase;
}}
.toolbar button.primary {{
  border-color: var(--accent);
  color: var(--accent);
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
.check-col {{ width: 44px; text-align: center; color: var(--check); }}
.check-col input[type="checkbox"] {{
  width: 16px;
  height: 16px;
}}
.check-col .print-check {{ display: none; }}
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
  .check-col input[type="checkbox"] {{ display: none; }}
  .check-col .print-check {{ display: inline-block; font-size: 16px; }}
  .check-col input[type="checkbox"]:checked + .print-check::after {{ content: "☑"; }}
  .check-col input[type="checkbox"]:not(:checked) + .print-check::after {{ content: "☐"; }}
  .toolbar {{ display: none; }}
  body {{ margin: 12mm; }}
}}
</style>
</head>
<body>
<div class=\"toolbar\" id=\"toolbar\">
  <div>
    <label for=\"sheet\">Лист</label>
    <select id=\"sheet\"></select>
  </div>
  <div>
    <label for=\"engineer\">Инженер</label>
    <select id=\"engineer\"></select>
  </div>
  <div class=\"wide\">
    <label for=\"defects\">Выявленные недостатки</label>
    <textarea id=\"defects\" rows=\"3\" placeholder=\"Опишите выявленные недостатки...\"></textarea>
  </div>
  <div class=\"actions wide\">
    <button id=\"print\" class=\"primary\" type=\"button\">Печать</button>
  </div>
</div>

<div class=\"header\">
  <div class=\"month\" id=\"month\"></div>
  <div class=\"title\" id=\"title\"></div>
  <div class=\"subtitle\">Ежемесячное техническое обслуживание (ТО-1)</div>
</div>

<div class=\"section\">
  <div id=\"engineer-line\">Лица, принимающие участие в техническом обслуживании (ФИО, профессия/должность) - </div>
  <div class=\"signature\"><span class=\"signature-line\"></span> Образец подписи</div>
</div>

<div class=\"section notes\" id=\"warnings\"></div>

<table class=\"checklist\">
  <thead>
    <tr>
      <th class=\"check-col\">Галочка</th>
      <th>Наименование прибора</th>
      <th>Наименование операции по техническому обслуживанию</th>
    </tr>
  </thead>
  <tbody id=\"rows\"></tbody>
</table>

<div class=\"section footer\" id=\"closing\"></div>

<div class=\"defects section\">
  <div><span class=\"stamp\">Выявленные недостатки</span></div>
  <div id=\"defects-lines\"></div>
</div>

<script>
const DATA = {data_json};

function monthYearRu() {{
  const months = ["январь","февраль","март","апрель","май","июнь","июль","август","сентябрь","октябрь","ноябрь","декабрь"];
  const now = new Date();
  return `${{months[now.getMonth()]}} ${{now.getFullYear()}} г.`;
}}

function escapeHtml(s) {{
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}}

function renderDefects(text) {{
  const container = document.getElementById("defects-lines");
  container.innerHTML = "";
  const lines = (text || "").split("\\n").filter(Boolean);
  if (lines.length === 0) {{
    for (let i = 0; i < 3; i++) {{
      const div = document.createElement("div");
      div.className = "defects-line";
      container.appendChild(div);
    }}
    return;
  }}
  lines.forEach(line => {{
    const div = document.createElement("div");
    div.className = "defects-line";
    div.textContent = line;
    container.appendChild(div);
  }});
}}

function renderSheet(sheetId) {{
  const sheet = DATA.sheets.find(s => s.id === sheetId);
  if (!sheet) return;
  document.getElementById("month").textContent = monthYearRu();
  document.getElementById("title").textContent = sheet.title || sheet.id;
  document.getElementById("warnings").innerHTML = (sheet.warnings || []).map(l => `<p>${{escapeHtml(l)}}</p>`).join("");
  document.getElementById("closing").innerHTML = (sheet.closing || []).map(l => `<p>${{escapeHtml(l)}}</p>`).join("");
  const rows = DATA.items.filter(r => r.sheet_id === sheetId);
  document.getElementById("rows").innerHTML = rows.map(r => (
    `<tr>
      <td class="check-col"><input type="checkbox" checked><span class="print-check"></span></td>
      <td>${{escapeHtml(r.device)}}</td>
      <td>${{escapeHtml(r.operation)}}</td>
    </tr>`
  )).join("");
}}

function init() {{
  const sheetSelect = document.getElementById("sheet");
  DATA.sheets.forEach(sheet => {{
    const opt = document.createElement("option");
    opt.value = sheet.id;
    opt.textContent = sheet.title || sheet.id;
    sheetSelect.appendChild(opt);
  }});
  sheetSelect.addEventListener("change", () => renderSheet(sheetSelect.value));

  const engineer = document.getElementById("engineer");
  const engineerLine = document.getElementById("engineer-line");
  (DATA.engineers || []).forEach(name => {{
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    engineer.appendChild(opt);
  }});
  function updateEngineer() {{
    engineerLine.textContent = `Лица, принимающие участие в техническом обслуживании (ФИО, профессия/должность) - ${{engineer.value || \"\"}}`;\n  }}
  engineer.addEventListener("change", updateEngineer);

  const defects = document.getElementById("defects");
  defects.addEventListener("input", () => renderDefects(defects.value));

  document.getElementById("print").addEventListener("click", () => window.print());

  sheetSelect.value = DATA.sheets[0]?.id || \"\";
  renderSheet(sheetSelect.value);
  engineer.value = (DATA.engineers && DATA.engineers[0]) ? DATA.engineers[0] : \"\";
  updateEngineer();
  renderDefects(\"\");
}}

init();
</script>
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


def main():
    meta = load_meta()
    items_by_sheet = load_items()
    Path("out").mkdir(exist_ok=True)

    data = {
        "engineers": meta.get("engineers", []),
        "sheets": meta["sheets"],
        "items": [
            {"sheet_id": sid, "device": row["device"], "operation": row["operation"]}
            for sid, rows in items_by_sheet.items()
            for row in rows
        ],
    }

    html = HTML_TEMPLATE.format(
        title="Контрольные листы",
        data_json=json.dumps(data, ensure_ascii=False),
    )
    out_path = Path("out") / "checklists_ui.html"
    out_path.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
