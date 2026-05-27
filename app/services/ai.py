from app.services.rooms import get_room


def public_question(room_id: str, question: str) -> dict | None:
    room = get_room(room_id)
    if room is None:
        return None
    spot = room.get("currentSpot", "")
    answer = f"关于「{question}」的解答：当前位于 {spot or '起点'}，这里是模拟答案，后续将接入真实 AI。"
    return {"roomId": room_id, "answer": answer}
