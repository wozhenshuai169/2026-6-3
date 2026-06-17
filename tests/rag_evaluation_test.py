from algorithm_service.services import scenic_rag


def _chunk_ids(result: dict) -> set[str]:
    return {source.split(":", 1)[0] for source in result.get("sources", [])}


def test_rag_citation_hit_rate():
    cases = [
        ("主展厅的历史是什么？", "main_hall", {"chunk_001", "chunk_022"}),
        ("钟楼有什么历史作用？", "bell_tower", {"chunk_005", "chunk_032"}),
        ("游客服务中心能办什么？", "", {"chunk_014"}),
        ("石刻长廊参观时要注意什么？", "stone_gallery", {"chunk_094"}),
    ]

    hits = 0
    for question, current_spot, expected_any in cases:
        result = scenic_rag.answer("room", "user", question, currentSpot=current_spot)
        if _chunk_ids(result) & expected_any:
            hits += 1

    assert hits / len(cases) >= 0.75


def test_rag_refuses_unsupported_question():
    result = scenic_rag.answer("room", "user", "火星基地的门票多少钱？")

    assert result["sources"] == []
    assert result["confidence"] < 0.3
    assert result["stateUpdate"]["rag"]["refused"] is True
    assert "没有查到可靠依据" in result["answer"]


def test_rag_handles_synonym_question():
    result = scenic_rag.answer("room", "user", "洗手间在哪里？")

    assert "chunk_015" in _chunk_ids(result)
    assert result["confidence"] >= 0.6


def test_rag_combines_multiple_chunks():
    result = scenic_rag.answer("room", "user", "钟楼和鼓楼是什么关系，鼓楼里面展示什么？")
    ids = _chunk_ids(result)

    assert "chunk_021" in ids
    assert ids & {"chunk_008", "chunk_009"}
    assert len(result["sources"]) >= 2
