from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = ROOT / "data" / "scenic_chunks.json"
NODES_PATH = ROOT / "data" / "path_nodes.json"
EDGES_PATH = ROOT / "data" / "path_edges.json"


FACILITY_NODES = [
    {"nodeId": "fac_rest_entrance", "nodeName": "入口游客休息点", "nodeType": "rest_area", "facilityType": "rest_area", "scenicAreaId": "lingshan_shengjing", "accessible": True, "verificationStatus": "needs_field_verification", "verificationNote": "候选位置，具体位置和开放状态以现场标识为准"},
    {"nodeId": "fac_toilet_jiulong", "nodeName": "九龙灌浴周边卫生间", "nodeType": "facility", "facilityType": "toilet", "scenicAreaId": "lingshan_shengjing", "accessible": True, "verificationStatus": "needs_field_verification", "verificationNote": "候选位置，具体位置和开放状态以现场标识为准"},
    {"nodeId": "fac_rest_buddha", "nodeName": "大佛区域休息点", "nodeType": "rest_area", "facilityType": "rest_area", "scenicAreaId": "lingshan_shengjing", "accessible": True, "verificationStatus": "needs_field_verification", "verificationNote": "候选位置，具体位置和开放状态以现场标识为准"},
    {"nodeId": "fac_service_palace", "nodeName": "梵宫区域游客服务点", "nodeType": "facility", "facilityType": "service_desk", "scenicAreaId": "lingshan_shengjing", "accessible": True, "verificationStatus": "needs_field_verification", "verificationNote": "候选位置，具体位置和开放状态以现场标识为准"},
    {"nodeId": "fac_first_aid_palace", "nodeName": "梵宫区域应急联络点", "nodeType": "facility", "facilityType": "first_aid", "scenicAreaId": "lingshan_shengjing", "accessible": True, "verificationStatus": "needs_field_verification", "verificationNote": "候选位置；紧急情况优先联系现场工作人员或拨打急救电话"},
]

FACILITY_EDGES = [
    {"edgeId": "e21", "fromNodeId": "ls_dazhaobi", "toNodeId": "fac_rest_entrance", "distanceMeters": 80, "walkingMinutes": 2, "difficulty": "low", "accessible": True, "status": "open", "distanceBasis": "facility_area_estimate"},
    {"edgeId": "e22", "fromNodeId": "ls_jiulong", "toNodeId": "fac_toilet_jiulong", "distanceMeters": 120, "walkingMinutes": 2, "difficulty": "low", "accessible": True, "status": "open", "distanceBasis": "facility_area_estimate"},
    {"edgeId": "e23", "fromNodeId": "ls_buddha", "toNodeId": "fac_rest_buddha", "distanceMeters": 140, "walkingMinutes": 3, "difficulty": "low", "accessible": True, "status": "open", "distanceBasis": "facility_area_estimate"},
    {"edgeId": "e24", "fromNodeId": "ls_palace", "toNodeId": "fac_service_palace", "distanceMeters": 100, "walkingMinutes": 2, "difficulty": "low", "accessible": True, "status": "open", "distanceBasis": "facility_area_estimate"},
    {"edgeId": "e25", "fromNodeId": "ls_palace", "toNodeId": "fac_first_aid_palace", "distanceMeters": 120, "walkingMinutes": 2, "difficulty": "low", "accessible": True, "status": "open", "distanceBasis": "facility_area_estimate"},
]


def restore_chunks() -> int:
    original = json.loads(
        subprocess.check_output(
            ["git", "show", "HEAD:data/scenic_chunks.json"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
        )
    )
    current = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    current_by_id = {item["chunkId"]: item for item in current}
    merged = []
    for item in original:
        restored = dict(current_by_id.get(item["chunkId"], item))
        restored.setdefault("sourceTier", "unverified_reference")
        restored.setdefault("verificationStatus", "needs_field_verification")
        merged.append(restored)
    CHUNKS_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(merged)


def merge_by_id(path: Path, additions: list[dict], key: str) -> int:
    items = json.loads(path.read_text(encoding="utf-8"))
    merged = {item[key]: item for item in items}
    for item in additions:
        merged[item[key]] = item
    values = list(merged.values())
    path.write_text(json.dumps(values, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(values)


if __name__ == "__main__":
    print(
        json.dumps(
            {
                "chunks": restore_chunks(),
                "pathNodes": merge_by_id(NODES_PATH, FACILITY_NODES, "nodeId"),
                "pathEdges": merge_by_id(EDGES_PATH, FACILITY_EDGES, "edgeId"),
            },
            ensure_ascii=False,
        )
    )
