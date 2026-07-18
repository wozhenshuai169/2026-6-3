from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = ROOT / "data" / "scenic_chunks.json"
NODES_PATH = ROOT / "data" / "path_nodes.json"
EDGES_PATH = ROOT / "data" / "path_edges.json"
OFFICIAL_SOURCE = "灵山胜境官网景点介绍（https://www.lingshan.com.cn/index.html）"
OFFICIAL_PROFILE_SOURCE = "灵山胜境官网景区简介（https://www.lingshan.com.cn/web/shelp/1.html）"
PACK_SOURCE = "示范景区公开资料包（无来源标注，仅作待核验参考）"
POLICY_SOURCE = "项目内置导览安全规则"


OFFICIAL_CONTENT = {
    "ls_001": (
        "灵山胜境位于江苏无锡马山，北倚灵山、南面太湖，是国家5A级旅游景区。"
        "景区以佛教文化景观为核心，主要包括灵山大佛、祥符禅寺、九龙灌浴、灵山梵宫和五印坛城。"
    ),
    "ls_009": (
        "九龙灌浴是大型音乐喷泉动态群雕，以动态表演再现佛陀释迦牟尼诞生的故事；"
        "中央鎏金太子佛像高7.2米。具体演出安排属于动态信息，应以游览当日现场公告为准。"
    ),
    "ls_010": (
        "九龙灌浴演出时刻可能因日期、天气和运营安排变化。程序不播报资料包中的固定时刻，"
        "游客应在入园后查看当日公告、官方服务入口或咨询现场工作人员。"
    ),
    "ls_014": (
        "灵山胜境官网介绍祥符禅寺始建于唐贞观年间，并称其相传为玄奘法师所创、为慈恩宗道场。"
        "该表述属于景区官方历史介绍。"
    ),
    "ls_016": (
        "灵山大佛北倚灵山、南面太湖，佛像高88米，为全青铜铸造的露天释迦牟尼立像，"
        "是灵山胜境的标志性景观。"
    ),
    "ls_019": (
        "灵山梵宫融合中国佛教石窟艺术和传统佛教建筑元素，集中展示佛教艺术珍品与文化遗产；"
        "官网资料记载其总建筑面积为72000平方米。"
    ),
    "ls_021": (
        "《灵山吉祥颂》的场次、入场方式和临时调整属于动态运营信息。程序不采用资料包中的固定时刻，"
        "游客应以游览当日现场公告或工作人员说明为准。"
    ),
    "ls_022": (
        "五印坛城展示藏传佛教文化艺术，汇集彩绘、壁画、木雕和唐卡等传统装饰技艺，"
        "是灵山胜境的主要文化景观之一。"
    ),
}

OFFICIAL_IDS = set(OFFICIAL_CONTENT)
POLICY_IDS = {"ls_028", "ls_029", "ls_030", "ls_031", "ls_032", "ls_033", "ls_034", "ls_035"}


def curate() -> list[dict]:
    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    curated: list[dict] = []
    for chunk in chunks:
        chunk_id = str(chunk.get("chunkId", ""))
        item = dict(chunk)
        if chunk_id in OFFICIAL_IDS:
            item["updatedAt"] = "2026-07-18"
            item["source"] = OFFICIAL_PROFILE_SOURCE if chunk_id in {"ls_001", "ls_022"} else OFFICIAL_SOURCE
            item["sourceTier"] = "official_verified"
            item["verificationStatus"] = "verified"
            item["content"] = OFFICIAL_CONTENT[chunk_id]
        elif chunk_id in POLICY_IDS:
            item["updatedAt"] = "2026-07-18"
            item["source"] = POLICY_SOURCE
            item["sourceTier"] = "safety_policy"
            item["verificationStatus"] = "policy"
        elif chunk_id.startswith("ls_") and chunk_id[3:].isdigit() and int(chunk_id[3:]) <= 35:
            item["updatedAt"] = "2026-07-18"
            item["source"] = PACK_SOURCE
            item["sourceTier"] = "unverified_reference"
            item["verificationStatus"] = "needs_field_verification"
        else:
            item.setdefault("sourceTier", "unverified_reference")
            item.setdefault("verificationStatus", "needs_field_verification")
        curated.append(item)
    return curated


if __name__ == "__main__":
    curated = curate()
    CHUNKS_PATH.write_text(
        json.dumps(curated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    nodes = json.loads(NODES_PATH.read_text(encoding="utf-8"))
    valid_node_ids = {node["nodeId"] for node in nodes}
    edges = json.loads(EDGES_PATH.read_text(encoding="utf-8"))
    edges = [
        edge
        for edge in edges
        if edge.get("fromNodeId") in valid_node_ids and edge.get("toNodeId") in valid_node_ids
    ]
    NODES_PATH.write_text(json.dumps(nodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    EDGES_PATH.write_text(json.dumps(edges, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Curated {len(curated)} chunks, {len(nodes)} path nodes and {len(edges)} path edges.")
