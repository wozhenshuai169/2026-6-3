"""ScenicRAG — 基于知识库的公共知识问答（Mock）。"""


def answer(roomId: str, userId: str, question: str, currentSpot: str = "", context: dict = None) -> dict:
    _ = (roomId, userId, context)
    return {
        "answer": f"关于「{question}」的解答：当前位置 {currentSpot or '景区'}，这里是模拟 RAG 回答。",
        "sources": ["景区百科", "历史资料"],
        "confidence": 0.85,
        "stateUpdate": {},
    }
