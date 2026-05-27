"""PrivateAssistant — 私人导览问题处理（Mock）。"""


def handle(roomId: str, userId: str, question: str, context: dict = None) -> dict:
    _ = (roomId, userId, context)
    return {
        "answer": f"私人回复：关于「{question}」的解答（模拟私人频道回答）。",
        "needLeaderAuth": False,
        "notification": "",
        "stateUpdate": {},
    }
