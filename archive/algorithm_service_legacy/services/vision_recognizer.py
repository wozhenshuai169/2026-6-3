"""VisionRecognizer — 图片识景（Mock）。"""


def recognize(roomId: str, userId: str, imageUrl: str, context: dict = None) -> dict:
    _ = (roomId, userId, imageUrl, context)
    return {
        "sceneName": "太和殿",
        "description": "这是故宫太和殿，俗称金銮殿，是中国现存最大的木结构大殿。",
        "tags": ["古建筑", "故宫", "太和殿", "明清"],
        "stateUpdate": {},
    }
