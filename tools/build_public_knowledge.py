"""Build curated scenic knowledge from the supplied public data package.

The script deliberately keeps raw tourism behaviour records out of the visitor
Q&A corpus.  It produces only aggregated, non-identifying operational insights
from the Excel file and turns the two Word documents into traceable knowledge
chunks for the Lingshan product knowledge base.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from statistics import mean
from typing import Iterable
from xml.etree import ElementTree as ET
from zipfile import ZipFile


PROJECT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = PROJECT_DIR.parent
DEFAULT_SOURCE = WORKSPACE_DIR / "20260323113204906 (1)" / "示范景区公开资料包"
DEFAULT_DATA = PROJECT_DIR / "data"
W_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
X_NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
ID_RE = re.compile(r"^(LS|NH)-\d{3}$")

SPOT_IDS = {
    "灵山大照壁": "lingshan_dazhaobi",
    "五明桥": "wuming_bridge",
    "佛足坛": "buddha_foot_altar",
    "五智门": "wuzhi_gate",
    "菩提大道": "bodhi_avenue",
    "九龙灌浴": "jiulong_guanyu",
    "降魔浮雕": "demon_relief",
    "阿育王柱": "ashoka_pillar",
    "百子戏弥勒": "baizi_mile",
    "祥符禅寺": "xiangfu_temple",
    "灵山大佛": "lingshan_buddha",
    "佛教文化博览馆": "buddhist_museum",
    "灵山梵宫": "lingshan_palace",
    "五印坛城": "wuyin_mandala",
    "曼飞龙塔": "manfeilong_pagoda",
    "无尽意斋": "wujinyi_house",
}


def docx_paragraphs(path: Path) -> list[str]:
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    paragraphs: list[str] = []
    for node in root.findall(".//w:p", W_NS):
        text = "".join(item.text or "" for item in node.findall(".//w:t", W_NS)).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def chunk_text(text: str, size: int = 900, overlap: int = 100) -> list[str]:
    text = re.sub(r"\\s+", " ", text).strip()
    if len(text) <= size:
        return [text] if text else []
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            boundary = max(text.rfind("。", start, end), text.rfind("；", start, end))
            if boundary > start + size // 2:
                end = boundary + 1
        parts.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(start + 1, end - overlap)
    return parts


def route_ids_by_spot(data_dir: Path) -> dict[str, list[str]]:
    routes = json.loads((data_dir / "routes.json").read_text(encoding="utf-8"))
    result: dict[str, list[str]] = defaultdict(list)
    for route in routes:
        for spot_id in route.get("spotIds", []):
            result[spot_id].append(route["routeId"])
    return dict(result)


def parse_structured_records(path: Path) -> list[dict]:
    paragraphs = docx_paragraphs(path)
    records: list[dict] = []
    for index, value in enumerate(paragraphs):
        if not ID_RE.match(value) or index + 9 >= len(paragraphs):
            continue
        scenic_name = paragraphs[index - 1] if index else ""
        fields = paragraphs[index + 1 : index + 10]
        if len(fields) != 9 or not scenic_name:
            continue
        records.append(
            {
                "rawId": value,
                "scenicName": scenic_name,
                "spotName": fields[0],
                "location": fields[1],
                "parameters": fields[2],
                "function": fields[3],
                "culture": fields[4],
                "detail": fields[5],
                "highlights": fields[6],
                "opening": fields[7],
                "remarks": fields[8],
            }
        )
    return records


def build_structured_chunks(records: Iterable[dict], route_ids: dict[str, list[str]], updated_at: str) -> list[dict]:
    chunks: list[dict] = []
    for record in records:
        raw_id = record["rawId"].lower().replace("-", "_")
        spot_id = SPOT_IDS.get(record["spotName"], f"public_{raw_id}")
        common = {
            "spotId": spot_id,
            "audience": "所有游客",
            "type": "spot",
            "source": "示范景区公开资料包：灵山胜境 景点结构化数据集",
            "updatedAt": updated_at,
            "routeIds": route_ids.get(spot_id, []),
        }
        overview = (
            f"位置：{record['location']} 建筑/景观参数：{record['parameters']} "
            f"核心功能：{record['function']} 文化内涵：{record['culture']}"
        )
        chunks.append(
            {
                **common,
                "chunkId": f"public_{raw_id}_overview",
                "title": f"{record['spotName']}：位置、功能与文化内涵",
                "topic": "culture",
                "content": overview,
            }
        )
        guide = (
            f"详细介绍：{record['detail']} 游玩亮点：{record['highlights']} "
            f"演艺/开放信息：{record['opening']} 备注：{record['remarks']}"
        )
        for part_index, part in enumerate(chunk_text(guide), start=1):
            chunks.append(
                {
                    **common,
                    "chunkId": f"public_{raw_id}_guide_{part_index:02d}",
                    "title": f"{record['spotName']}：游览与体验指南 #{part_index}",
                    "topic": "guide",
                    "content": part,
                }
            )
    return chunks


def build_guide_chunks(path: Path, route_ids: dict[str, list[str]], updated_at: str) -> list[dict]:
    paragraphs = docx_paragraphs(path)
    source = "示范景区公开资料包：灵山胜境：历史、文化、景点特色与个性化游览指南"
    definitions = [
        ("public_guide_history", "灵山胜境历史沿革", "history", "lingshan_shengjing", paragraphs[2:13]),
        ("public_guide_culture", "灵山胜境佛教文化与艺术", "culture", "lingshan_shengjing", paragraphs[14:22]),
        ("public_guide_buddha", "灵山大佛深度讲解", "culture", "lingshan_buddha", paragraphs[23:34]),
        ("public_guide_palace", "灵山梵宫艺术与吉祥颂", "architecture", "lingshan_palace", paragraphs[34:45]),
        ("public_guide_jiulong", "九龙灌浴表演与体验", "culture", "jiulong_guanyu", paragraphs[45:56]),
        ("public_guide_mandala", "五印坛城与藏传佛教体验", "culture", "wuyin_mandala", paragraphs[56:67]),
        ("public_guide_temple", "祥符禅寺历史遗存与体验", "history", "xiangfu_temple", paragraphs[67:81]),
        ("public_guide_history_route", "灵山历史文化深读建议", "route", "lingshan_shengjing", paragraphs[82:95]),
        ("public_guide_nature_route", "灵山自然风光游览建议", "route", "lingshan_shengjing", paragraphs[95:107]),
        ("public_guide_family_route", "灵山亲子游览建议", "route", "lingshan_shengjing", paragraphs[107:119]),
        ("public_guide_practical", "灵山实用游览贴士", "notice", "lingshan_shengjing", paragraphs[119:156]),
    ]
    chunks: list[dict] = []
    for chunk_id, title, topic, spot_id, lines in definitions:
        text = " ".join(lines)
        # Prices, schedules and opening arrangements are inherently time-sensitive.
        if topic == "notice":
            text = f"以下公开资料可能随季节或景区安排变化，请以当日公告、售票页面和现场工作人员说明为准。{text}"
        for index, part in enumerate(chunk_text(text), start=1):
            suffix = "" if index == 1 else f"_{index:02d}"
            chunks.append(
                {
                    "chunkId": f"{chunk_id}{suffix}",
                    "spotId": spot_id,
                    "title": title if index == 1 else f"{title} #{index}",
                    "topic": topic,
                    "audience": "所有游客",
                    "type": "notice" if topic == "notice" else "spot",
                    "source": source,
                    "updatedAt": updated_at,
                    "routeIds": route_ids.get(spot_id, []),
                    "content": part,
                }
            )
    return chunks


def _column_index(reference: str) -> int:
    letters = "".join(character for character in reference if character.isalpha())
    value = 0
    for character in letters:
        value = value * 26 + ord(character.upper()) - 64
    return max(0, value - 1)


def _xlsx_shared_strings(archive: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return ["".join(item.text or "" for item in node.findall(".//x:t", X_NS)) for node in root.findall(".//x:si", X_NS)]


def _first_sheet_path(archive: ZipFile) -> str:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    sheet = workbook.find(".//x:sheets/x:sheet", X_NS)
    if sheet is None:
        raise ValueError("Workbook does not contain a worksheet")
    relation_id = sheet.attrib[f"{{{R_NS}}}id"]
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    for relation in rels:
        if relation.attrib.get("Id") == relation_id:
            return "xl/" + relation.attrib["Target"].lstrip("/")
    raise ValueError("Workbook relationship is missing")


def _xlsx_rows(path: Path):
    with ZipFile(path) as archive:
        shared = _xlsx_shared_strings(archive)
        sheet_path = _first_sheet_path(archive)
        with archive.open(sheet_path) as stream:
            for _, node in ET.iterparse(stream, events=("end",)):
                if node.tag != f"{{{X_NS['x']}}}row":
                    continue
                row: list[str] = []
                for cell in node.findall("x:c", X_NS):
                    column = _column_index(cell.attrib.get("r", "A1"))
                    while len(row) <= column:
                        row.append("")
                    value = cell.findtext("x:v", default="", namespaces=X_NS)
                    if cell.attrib.get("t") == "s" and value:
                        value = shared[int(value)]
                    row[column] = value
                yield row
                node.clear()


def build_behavior_insights(path: Path, updated_at: str) -> dict:
    rows = _xlsx_rows(path)
    headers = next(rows, [])
    index = {name: position for position, name in enumerate(headers)}
    attraction_index = index.get("attraction_name")
    stay_index = index.get("stay_duration")
    rating_index = index.get("rating")
    if attraction_index is None:
        return {"source": path.name, "generatedAt": updated_at, "rowCount": 0, "attractions": []}
    counts: Counter[str] = Counter()
    stays: dict[str, list[float]] = defaultdict(list)
    ratings: dict[str, list[float]] = defaultdict(list)
    row_count = 0
    for row in rows:
        if attraction_index >= len(row) or not row[attraction_index].strip():
            continue
        row_count += 1
        attraction = row[attraction_index].strip()
        counts[attraction] += 1
        for column, target in ((stay_index, stays[attraction]), (rating_index, ratings[attraction])):
            if column is None or column >= len(row):
                continue
            try:
                target.append(float(row[column]))
            except ValueError:
                pass
    attractions = []
    for attraction, count in counts.most_common(30):
        attractions.append(
            {
                "attractionName": attraction,
                "sampleCount": count,
                "averageStayDuration": round(mean(stays[attraction]), 2) if stays[attraction] else None,
                "averageRating": round(mean(ratings[attraction]), 2) if ratings[attraction] else None,
            }
        )
    return {
        "source": path.name,
        "generatedAt": updated_at,
        "rowCount": row_count,
        "privacy": "仅保留景点级聚合统计，不导出游客ID、昵称、年龄或单条消费记录。",
        "attractions": attractions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    args = parser.parse_args()
    source_dir = args.source_dir.resolve()
    data_dir = args.data_dir.resolve()
    structured = next(source_dir.glob("*结构化数据集.docx"), None)
    guide = next(source_dir.glob("*个性化游览指南.docx"), None)
    workbook = next(source_dir.glob("*.xlsx"), None)
    if not structured or not guide or not workbook:
        raise SystemExit("Expected two DOCX files and one XLSX file in the source directory")

    updated_at = date.today().isoformat()
    route_ids = route_ids_by_spot(data_dir)
    existing_path = data_dir / "scenic_chunks.json"
    existing = json.loads(existing_path.read_text(encoding="utf-8"))
    generated = build_structured_chunks(parse_structured_records(structured), route_ids, updated_at)
    generated.extend(build_guide_chunks(guide, route_ids, updated_at))
    generated_ids = {item["chunkId"] for item in generated}
    merged = [item for item in existing if item.get("chunkId") not in generated_ids]
    merged.extend(generated)
    merged.sort(key=lambda item: item["chunkId"])
    existing_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    insights = build_behavior_insights(workbook, updated_at)
    (data_dir / "visitor_behavior_insights.json").write_text(
        json.dumps(insights, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"chunkCount": len(merged), "generatedChunks": len(generated), "behaviorRows": insights["rowCount"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
