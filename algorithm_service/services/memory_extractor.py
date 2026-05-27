"""MemoryExtractor — 游客记忆标签抽取（Mock）。"""


def extract(userId: str, dialogue: str, context: dict = None) -> dict:
    _ = (userId, dialogue, context)
    return {
        "tags": ["历史爱好者", "拍照达人"],
        "interests": ["古建筑", "明清历史", "摄影"],
        "summary": "该游客对历史建筑表现出浓厚兴趣，喜欢拍照记录。",
    }
