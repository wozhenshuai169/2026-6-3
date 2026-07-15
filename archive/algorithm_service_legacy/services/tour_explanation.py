"""TourExplanation — 讲解生成 + 自然续讲（Mock）。"""


def generate(roomId: str, spotId: str, spotName: str = "", style: str = "standard", context: dict = None) -> dict:
    _ = (roomId, context)
    name = spotName or spotId
    return {
        "explanation": f"欢迎来到{name}！这里是模拟讲解内容，风格：{style}。",
        "continuation": f"接下来我们可以往前走，看看{name}的更多细节…",
        "ttsText": f"欢迎来到{name}！这里是语音播报内容。",
        "stateUpdate": {"currentSpot": spotId},
    }
