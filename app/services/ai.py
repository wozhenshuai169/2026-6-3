"""AI 问答服务 —— LLM + 语音问答完整链路，含异常兜底。"""

import logging

from app.core.config import settings
from app.core.logging import Timer, log_model_call
from app.services.rooms import get_room
from app.services.audio import asr_transcribe, tts_synthesize
from app.providers.factory import get_llm

logger = logging.getLogger(__name__)

_PRIVATE_KEYWORDS = [
    "厕所", "洗手间", "休息", "走不动", "喝", "水", "饿", "累",
    "离队", "先走", "不跟团", "自己走", "提前走",
]


def _is_private_need(text: str) -> bool:
    return any(kw in text for kw in _PRIVATE_KEYWORDS)


async def public_question(room_id: str, question: str) -> dict | None:
    """公共文本问答：调用 LLM 生成回答。"""
    room = get_room(room_id)
    if room is None:
        logger.warning("AI question: room %s not found", room_id)
        return None

    spot = room.get("currentSpot", "")
    if not question.strip():
        return {"roomId": room_id, "answer": "您好！请问有什么可以帮您的？", "source": "fallback"}

    system_prompt = (
        "你是一个专业的景区AI导游，名叫「小导」，负责为游客解答问题。"
        "请用友好、亲切的中文回答。如果问题与景区无关，请礼貌地引导游客关注景区相关内容。"
        f"当前游客所在景点：{spot or '景区入口'}。"
    )

    llm = get_llm()
    with Timer(logger, f"LLM question '{question[:20]}...'"):
        try:
            response = await llm.chat(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                context={"current_spot": spot},
                timeout=settings.request_timeout,
            )
        except Exception as e:
            logger.error("LLM question failed: %s", e)
            return {
                "roomId": room_id,
                "answer": "抱歉，我暂时无法回答您的问题，请稍后再试。",
                "source": "error_fallback",
                "error": str(e),
            }

    # 空回答兜底
    content = (response.content or "").strip()
    if not content:
        logger.warning("LLM returned empty answer for: %s", question[:50])
        content = "这是一个很好的问题！不过我需要更多信息来准确回答，您可以换个方式描述吗？"

    return {"roomId": room_id, "answer": content, "source": "llm"}


async def public_voice_question(
    room_id: str,
    user_id: str,
    channel: str,
    audio_url: str,
    audio_format: str | None = None,
    text_hint: str | None = None,
) -> dict | None:
    """语音问答完整链路：ASR → 决策 → LLM → TTS → 续讲。"""

    # ── Step 1: ASR ─────────────────────────────
    if not settings.enable_asr:
        return {
            "asrText": "", "decision": "error",
            "answer": "语音识别功能未开启。",
            "audioUrl": "", "resumeText": "", "resumeAudioUrl": "",
            "sources": [], "events": [],
        }

    try:
        asr_result = await asr_transcribe(
            room_id, user_id, channel, audio_url,
            audio_format=audio_format, text_hint=text_hint,
        )
    except Exception as e:
        logger.error("ASR failed in voice pipeline: %s", e)
        return {
            "asrText": "", "decision": "error",
            "answer": "语音识别服务异常，请改用文字输入。",
            "audioUrl": "", "resumeText": "", "resumeAudioUrl": "",
            "sources": [], "events": [],
        }

    if asr_result is None:
        return None

    asr_text = asr_result.get("text", "")
    confidence = asr_result.get("confidence", 0.0)
    asr_error = asr_result.get("error", "")
    events = []

    # ── Step 2: 低置信度 / 识别失败 ─────────────
    if asr_error or (confidence < 0.3 and not text_hint):
        logger.info("Voice Q: low confidence=%.2f, asking clarification", confidence)
        return {
            "asrText": asr_text or "（无法识别）",
            "decision": "ask_clarification",
            "answer": "我没有听清，可以再说一遍或改用文字输入吗？",
            "audioUrl": "", "resumeText": "", "resumeAudioUrl": "",
            "sources": [], "events": [],
        }

    if confidence < 0.6 and not text_hint:
        return {
            "asrText": asr_text or "（无法识别）",
            "decision": "ask_clarification",
            "answer": "我没有听清，可以再说一遍或改用文字输入吗？",
            "audioUrl": "", "resumeText": "", "resumeAudioUrl": "",
            "sources": [], "events": [],
        }

    # ── Step 3: 决策 ────────────────────────────
    if channel == "public":
        decision = "interrupt_and_answer"
    else:
        decision = "private_reply"

    if channel == "public" and _is_private_need(asr_text):
        events.append({
            "type": "suggest_private_channel",
            "payload": {"reason": "该问题属于私人需求，不适合公共播报"},
        })
        decision = "private_reply"

    # ── Step 4: LLM 问答 ─────────────────────────
    qa_result = await public_question(room_id, asr_text)
    if qa_result is None:
        return None
    answer = qa_result["answer"]

    # ── Step 5: TTS ─────────────────────────────
    if settings.enable_tts:
        try:
            answer_tts = await tts_synthesize(answer)
            answer_audio_url = answer_tts.get("audioUrl", "")
        except Exception as e:
            logger.error("TTS failed for answer: %s", e)
            answer_audio_url = ""
    else:
        answer_audio_url = ""

    # ── Step 6: 续讲 ────────────────────────────
    room = get_room(room_id)
    spot = room.get("currentSpot", "") if room else ""
    if spot:
        answer_summary = answer[:38] + "……" if len(answer) > 38 else answer
        llm = get_llm()
        try:
            resume_response = await llm.chat(
                messages=[
                    {"role": "system", "content": (
                        "你是一个景区导游。刚刚被打断回答了一个问题，"
                        "现在需要自然过渡回到讲解。生成一句过渡语。"
                    )},
                    {"role": "user", "content": (
                        f"答案摘要：{answer_summary}\n"
                        f"当前景点：{spot}\n"
                        f"请生成一句自然过渡语。"
                    )},
                ],
                max_tokens=200,
                timeout=settings.request_timeout,
            )
            resume_text = resume_response.content
        except Exception as e:
            logger.error("Resume generation failed: %s", e)
            resume_text = "我们继续当前的导览。"
    else:
        resume_text = "我们继续当前的导览。"

    if settings.enable_tts and resume_text:
        try:
            resume_tts = await tts_synthesize(resume_text)
            resume_audio_url = resume_tts.get("audioUrl", "")
        except Exception:
            resume_audio_url = ""
    else:
        resume_audio_url = ""

    logger.info(
        "Voice Q complete: decision=%s asr='%s' answer_len=%d",
        decision, asr_text[:40], len(answer),
    )

    return {
        "asrText": asr_text,
        "decision": decision,
        "answer": answer,
        "audioUrl": answer_audio_url,
        "resumeText": resume_text,
        "resumeAudioUrl": resume_audio_url,
        "sources": [{"title": "主展厅历史资料", "chunkId": "chunk_001"}],
        "events": events,
    }
