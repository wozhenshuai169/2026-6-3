from app.services.rooms import get_room
from app.services.audio import asr_transcribe, tts_synthesize


def public_question(room_id: str, question: str) -> dict | None:
    room = get_room(room_id)
    if room is None:
        return None
    spot = room.get("currentSpot", "")
    answer = f"关于「{question}」的解答：当前位于 {spot or '起点'}，这里是模拟答案，后续将接入真实 AI。"
    return {"roomId": room_id, "answer": answer}


def public_voice_question(room_id: str, user_id: str, channel: str, audio_url: str) -> dict | None:
    """语音问答完整链路：ASR → 决策 → RAG → TTS → 续讲"""
    # Step 1: ASR 语音识别
    asr_result = asr_transcribe(room_id, user_id, channel, audio_url)
    if asr_result is None:
        return None
    asr_text = asr_result["text"]

    # Step 2: 介入决策（mock：公共频道直接回答）
    decision = "interrupt_and_answer" if channel == "public" else "private_reply"

    # Step 3: RAG 问答（复用现有 public_question）
    qa_result = public_question(room_id, asr_text)
    if qa_result is None:
        return None
    answer = qa_result["answer"]

    # Step 4: 答案 TTS
    answer_tts = tts_synthesize(answer)
    answer_audio_url = answer_tts["audioUrl"]

    # Step 5: 续讲文本生成
    room = get_room(room_id)
    spot = room.get("currentSpot", "")
    resume_text = (
        f"刚才我们讲到了{spot}的历史沿革，接下来继续看屋顶装饰。"
        if spot
        else "我们继续当前的导览。"
    )
    resume_tts = tts_synthesize(resume_text)
    resume_audio_url = resume_tts["audioUrl"]

    return {
        "asrText": asr_text,
        "decision": decision,
        "answer": answer,
        "audioUrl": answer_audio_url,
        "resumeText": resume_text,
        "resumeAudioUrl": resume_audio_url,
        "sources": [
            {"title": "主展厅历史资料", "chunkId": "chunk_001"}
        ],
    }
