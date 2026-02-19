#!/usr/bin/env python3
import csv
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

VERB_PREFIXES = (
    "Очистка",
    "Проверка",
    "Удаление",
    "Чистка",
    "Осмотр",
    "Продуть",
    "Выполнить",
    "Заменять",
    "На акустических",
    "С внутреннего",
    "Для очистки",
)

SIGNATURE_NOISE = (
    "Лица, принимающие участие",
    "Образец подписи",
    "Ответственный за полноту",
    "и точность заполнения КЛ инженер",
)


def read_docx_paragraphs(path: Path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)
    lines = []
    for p in root.findall(".//w:p", NS):
        runs = [t.text for t in p.findall(".//w:t", NS) if t.text]
        if runs:
            text = "".join(runs)
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                lines.append(text)
    return lines


def is_operation(line: str) -> bool:
    for prefix in VERB_PREFIXES:
        if line.startswith(prefix):
            return True
    return False


def parse_docx(path: Path):
    lines = read_docx_paragraphs(path)

    month = lines[0] if lines else ""
    title = ""
    for line in lines[:5]:
        if "Контрольный лист" in line:
            title = line
            break

    idx_header = next((i for i, l in enumerate(lines) if "Наименование прибора" in l), None)
    idx_sig = None
    if idx_header is not None:
        for i in range(idx_header, min(idx_header + 6, len(lines))):
            if "Подпись" in lines[i]:
                idx_sig = i
                break

    idx_closing = next((i for i, l in enumerate(lines) if "в целом по окончании работ" in l), None)
    idx_defects = next((i for i, l in enumerate(lines) if "Выявленные недостатки" in l), None)

    warnings = []
    if idx_header is not None:
        start_warn = None
        for i, l in enumerate(lines[:idx_header]):
            if "Ответственный" in l:
                start_warn = i + 1
        if start_warn is None:
            start_warn = 0
        for l in lines[start_warn:idx_header]:
            if any(l.startswith(x) for x in SIGNATURE_NOISE):
                continue
            warnings.append(l)

    items_start = (idx_sig + 1) if idx_sig is not None else (idx_header + 1 if idx_header is not None else 0)
    items_end = idx_closing if idx_closing is not None else (idx_defects if idx_defects is not None else len(lines))
    item_lines = lines[items_start:items_end]

    items = []
    device_parts = []
    for line in item_lines:
        if is_operation(line):
            device = " ".join(device_parts).strip()
            if device:
                items.append({"device": device, "operation": line})
            device_parts = []
        else:
            device_parts.append(line)

    closing = []
    if idx_closing is not None and idx_defects is not None:
        closing = lines[idx_closing:idx_defects]

    return {
        "month": month,
        "title": title,
        "warnings": warnings,
        "closing": closing,
        "items": items,
    }


def main():
    docx_files = sorted(Path(".").glob("*.docx"))
    if not docx_files:
        raise SystemExit("No .docx files found in current directory.")

    meta = {"sheets": []}
    rows = []

    for path in docx_files:
        data = parse_docx(path)
        sheet_id = path.stem
        meta["sheets"].append({
            "id": sheet_id,
            "source": path.name,
            "month": data["month"],
            "title": data["title"],
            "warnings": data["warnings"],
            "closing": data["closing"],
        })
        for item in data["items"]:
            rows.append({
                "sheet_id": sheet_id,
                "device": item["device"],
                "operation": item["operation"],
            })

    Path("data").mkdir(exist_ok=True)
    with open("data/checklists_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    with open("data/checklist_items.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["sheet_id", "device", "operation"])
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
