"""DecisionRouter — 判断 AI 是否介入、走公共/私人频道、是否打断当前讲解。"""


def evaluate(roomId: str, userId: str, event: str, context: dict = None) -> dict:
    _ = (roomId, userId, context)

    if event == "user_question":
        return {
            "shouldIntervene": True,
            "channel": "public",
            "shouldInterrupt": False,
            "reason": "用户在公共频道提问，AI 应回答",
        }
    elif event == "spot_reached":
        return {
            "shouldIntervene": True,
            "channel": "public",
            "shouldInterrupt": True,
            "reason": "到达新讲解点，应打断当前讲解",
        }
    elif event == "idle_timeout":
        return {
            "shouldIntervene": True,
            "channel": "public",
            "shouldInterrupt": False,
            "reason": "空闲超时，建议续讲或推荐路线",
        }
    elif event == "leader_action":
        return {
            "shouldIntervene": True,
            "channel": "public",
            "shouldInterrupt": True,
            "reason": "团长操作，优先响应",
        }
    else:
        return {
            "shouldIntervene": False,
            "channel": "none",
            "shouldInterrupt": False,
            "reason": "未识别事件类型，不介入",
        }
