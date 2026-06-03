"""AI 问答服务 —— 通过 LLM Provider 生成回答。

- public_question: 文本问答（LLM 生成或 Mock 降级）
- public_voice_question: 完整语音问答链路（ASR → 决策 → LLM → TTS → 续讲）

对齐 src/ai_algorithm_service/orchestrator.py 的编排逻辑：
- ASR 置信度 < 0.6 → ask_clarification
- 公共频道私人问题 → suggest_private_channel 事件
"""

from app.services.rooms import get_room
from app.services.audio import asr_transcribe, tts_synthesize
from app.providers.factory import get_llm

# 私人需求关键词（对齐 decision.py private_keywords）
_PRIVATE_KEYWORDS = [
    "厕所", "洗手间", "休息", "走不动", "喝", "水", "饿", "累",
    "离队", "先走", "不跟团", "自己走", "提前走",
]


def _is_private_need(text: str) -> bool:
    """检测文本是否包含私人需求关键词。"""
    return any(kw in text for kw in _PRIVATE_KEYWORDS)


async def public_question(room_id: str, question: str) -> dict | None:
    """公共文本问答：调用 LLM 生成回答。"""
    room = get_room(room_id)
    if room is None:
        return None

    spot = room.get("currentSpot", "")

    # 构建 LLM 对话消息
    system_prompt = (
        "你是一个专业的景区AI导游，名叫「小导」，负责为游客解答问题。"
        "请用友好、亲切的中文回答。如果问题与景区无关，请礼貌地引导游客关注景区相关内容。"
        f"当前游客所在景点：{spot or '景区入口'}。"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    llm = get_llm()
    response = await llm.chat(messages, context={"current_spot": spot})
    return {"roomId": room_id, "answer": response.content}


async def public_voice_question(
    room_id: str,
    user_id: str,
    channel: str,
    audio_url: str,
    audio_format: str | None = None,
    text_hint: str | None = None,
) -> dict | None:
    """语音问答完整链路：ASR → 决策 → LLM回答 → TTS → 续讲

    对齐 VoiceAdapter + TourAIOrchestrator 的编排逻辑。
    """
    # Step 1: ASR 语音识别
    asr_result = asr_transcribe(
        room_id, user_id, channel, audio_url,
        audio_format=audio_format,
        text_hint=text_hint,
    )
    if asr_result is None:
        return None

    asr_text = asr_result["text"]
    confidence = asr_result.get("confidence", 0.0)
    events = []

    # Step 2: 低置信度 → 追问澄清（对齐 decision.py ask_clarification）
    if confidence < 0.6 and not text_hint:
        return {
            "asrText": asr_text or "（无法识别）",
            "decision": "ask_clarification",
            "answer": "我没有听清，可以再说一遍或改用文字输入吗？",
            "audioUrl": "",
            "resumeText": "",
            "resumeAudioUrl": "",
            "sources": [],
            "events": [],
        }

    # Step 3: 介入决策
    if channel == "public":
        decision = "interrupt_and_answer"
    else:
        decision = "private_reply"

    # Step 4: 公共频道私人问题 → 建议转私人频道（对齐 suggest_private_channel）
    if channel == "public" and _is_private_need(asr_text):
        events.append({
            "type": "suggest_private_channel",
            "payload": {"reason": "该问题属于私人需求，不适合公共播报"},
        })
        decision = "private_reply"

    # Step 5: LLM 问答
    qa_result = await public_question(room_id, asr_text)
    if qa_result is None:
        return None
    answer = qa_result["answer"]

    # Step 6: 答案 TTS
    answer_tts = tts_synthesize(answer)
    answer_audio_url = answer_tts["audioUrl"]

    # Step 7: 续讲文本生成（对齐 explanation.py _bridge + _answer_summary）
    room = get_room(room_id)
    spot = room.get("currentSpot", "")
    if spot:
        # 提取答案摘要（前 38 字），拼接过渡语
        answer_summary = answer[:38] + "……" if len(answer) > 38 else answer
        llm = get_llm()
        resume_response = await llm.chat(
            messages=[
                {"role": "system", "content": (
                    "你是一个景区导游。刚刚被打断回答了一个问题，现在需要自然过渡回到讲解。"
                    "参考答案摘要和当前景点，生成一句自然的过渡语。"
                )},
                {"role": "user", "content": (
                    f"答案摘要：{answer_summary}\n"
                    f"当前景点：{spot}\n"
                    f"游客问题：{asr_text}\n"
                    "请生成一句自然的过渡语，承上启下回到{spot}的讲解。"
                )},
            ],
            max_tokens=200,
        )
        resume_text = resume_response.content
    else:
        resume_text = "我们继续当前的导览。"

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
        "events": events,
    }
