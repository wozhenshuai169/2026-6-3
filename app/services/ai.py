"""AI orchestration for public text and voice questions."""

import logging
from time import perf_counter

from app.core.config import settings
from app.core.logging import Timer
from app.providers.factory import get_llm
from app.services.audio import asr_transcribe, tts_synthesize
from app.services.rooms import get_room
from app.services.stats import record_event

logger = logging.getLogger(__name__)

TTS_WARNING = "TTS failed, text answer returned only."
DEFAULT_SOURCES = [{"title": "主展厅历史资料", "chunkId": "chunk_001"}]
PRIVATE_KEYWORDS = [
    "厕所",
    "洗手间",
    "休息",
    "走不动",
    "喝水",
    "迷路",
    "离队",
    "自己走",
    "提前走",
]


def _is_private_need(text: str) -> bool:
    return any(keyword in text for keyword in PRIVATE_KEYWORDS)


def _avatar_state(status: str, action: str = "answer", mouth_open: bool | None = None) -> dict:
    speaking = status == "speaking"
    return {
        "status": status,
        "emotion": "friendly",
        "action": action,
        "mouthOpen": speaking if mouth_open is None else mouth_open,
    }


def _tts_failed(result: dict) -> bool:
    return not result.get("success", True) or not result.get("audioUrl")


async def _answer_with_llm(room_id: str, question: str) -> dict | None:
    room = get_room(room_id)
    if room is None:
        logger.warning("AI question: room %s not found", room_id)
        return None

    spot = room.get("currentSpot", "")
    clean_question = question.strip()
    if not clean_question:
        return {"roomId": room_id, "answer": "您好，请问有什么可以帮您的？", "source": "fallback"}

    system_prompt = (
        "你是一个专业的景区AI导游，名叫小导。请用友好、亲切的中文回答。"
        "如果问题与景区无关，请礼貌引导游客关注景区相关内容。"
        f"当前游客所在景点：{spot or '景区入口'}。"
    )

    llm = get_llm()
    with Timer(logger, f"LLM question '{clean_question[:20]}...'"):
        try:
            response = await llm.chat(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": clean_question},
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

    answer = (response.content or "").strip()
    if not answer:
        answer = "这是一个很好的问题，不过我需要更多信息来准确回答，您可以换个方式描述吗？"

    return {"roomId": room_id, "answer": answer, "source": "llm"}


async def public_question(room_id: str, question: str, need_audio: bool = True) -> dict | None:
    started = perf_counter()
    try:
        qa_result = await _answer_with_llm(room_id, question)
        if qa_result is None:
            record_event(
                "public_question",
                success=False,
                latency_ms=(perf_counter() - started) * 1000,
                payload={"roomId": room_id, "question": question, "error": "room_not_found"},
            )
            return None

        answer = qa_result["answer"]
        audio_url = None
        duration = 0.0
        warning = None
        avatar_state = _avatar_state("idle", mouth_open=False)

        if need_audio:
            tts = await tts_synthesize(answer, room_id=room_id)
            if _tts_failed(tts):
                warning = TTS_WARNING
            else:
                audio_url = tts.get("audioUrl")
                duration = float(tts.get("duration", 0.0) or 0.0)
                avatar_state = _avatar_state("speaking", mouth_open=True)

        result = {
            "roomId": room_id,
            "answer": answer,
            "audioUrl": audio_url,
            "duration": duration,
            "sources": DEFAULT_SOURCES,
            "avatarState": avatar_state,
            "warning": warning,
        }
        record_event(
            "public_question",
            success=True,
            latency_ms=(perf_counter() - started) * 1000,
            payload={"roomId": room_id, "question": question, "hasAudio": bool(audio_url)},
        )
        return result
    except Exception as e:
        record_event(
            "public_question",
            success=False,
            latency_ms=(perf_counter() - started) * 1000,
            payload={"roomId": room_id, "question": question, "error": str(e)},
        )
        raise


async def _resume_after_answer(room_id: str, answer: str) -> str:
    room = get_room(room_id)
    spot = room.get("currentSpot", "") if room else ""
    if not spot:
        return "我们继续当前的导览。"

    answer_summary = answer[:38] + "..." if len(answer) > 38 else answer
    llm = get_llm()
    try:
        response = await llm.chat(
            messages=[
                {
                    "role": "system",
                    "content": "你是景区导游。刚刚回答了一个问题，现在需要自然过渡回讲解，生成一句简短过渡语。",
                },
                {
                    "role": "user",
                    "content": f"答案摘要：{answer_summary}\n当前景点：{spot}\n请生成一句自然过渡语。",
                },
            ],
            max_tokens=200,
            timeout=settings.request_timeout,
        )
        return (response.content or "").strip() or "我们继续当前的导览。"
    except Exception as e:
        logger.error("Resume generation failed: %s", e)
        return "我们继续当前的导览。"


async def public_voice_question(
    room_id: str,
    user_id: str,
    channel: str,
    audio_url: str,
    audio_format: str | None = None,
    text_hint: str | None = None,
) -> dict | None:
    started = perf_counter()
    warning = None
    try:
        if not settings.enable_asr:
            result = {
                "asrText": "",
                "decision": "error",
                "answer": "语音识别功能未开启。",
                "audioUrl": None,
                "duration": 0.0,
                "resumeText": "",
                "resumeAudioUrl": None,
                "resumeDuration": 0.0,
                "sources": [],
                "avatarState": _avatar_state("idle", mouth_open=False),
                "warning": "ASR disabled.",
                "events": [],
            }
            record_event(
                "public_voice_question",
                success=False,
                latency_ms=(perf_counter() - started) * 1000,
                payload={"roomId": room_id, "error": "asr_disabled"},
            )
            return result

        asr_result = await asr_transcribe(
            room_id,
            user_id,
            channel,
            audio_url,
            audio_format=audio_format,
            text_hint=text_hint,
        )
        if asr_result is None:
            record_event(
                "public_voice_question",
                success=False,
                latency_ms=(perf_counter() - started) * 1000,
                payload={"roomId": room_id, "error": "room_not_found"},
            )
            return None

        asr_text = asr_result.get("text", "")
        confidence = float(asr_result.get("confidence", 0.0) or 0.0)
        events: list[dict] = []

        if asr_result.get("error") or (confidence < 0.6 and not text_hint):
            result = {
                "asrText": asr_text or "（无法识别）",
                "decision": "ask_clarification",
                "answer": "我没有听清，可以再说一遍或改用文字输入吗？",
                "audioUrl": None,
                "duration": 0.0,
                "resumeText": "",
                "resumeAudioUrl": None,
                "resumeDuration": 0.0,
                "sources": [],
                "avatarState": _avatar_state("idle", mouth_open=False),
                "warning": None,
                "events": [],
            }
            record_event(
                "public_voice_question",
                success=True,
                latency_ms=(perf_counter() - started) * 1000,
                payload={"roomId": room_id, "asrText": asr_text, "decision": "ask_clarification"},
            )
            return result

        decision = "interrupt_and_answer" if channel == "public" else "private_reply"
        if channel == "public" and _is_private_need(asr_text):
            events.append(
                {
                    "type": "suggest_private_channel",
                    "payload": {"reason": "该问题属于私人需求，不适合公共播报"},
                }
            )
            decision = "private_reply"

        qa_result = await _answer_with_llm(room_id, asr_text)
        if qa_result is None:
            record_event(
                "public_voice_question",
                success=False,
                latency_ms=(perf_counter() - started) * 1000,
                payload={"roomId": room_id, "asrText": asr_text, "error": "room_not_found"},
            )
            return None

        answer = qa_result["answer"]
        answer_audio_url = None
        answer_duration = 0.0
        avatar_state = _avatar_state("idle", mouth_open=False)
        answer_tts = await tts_synthesize(answer, room_id=room_id)
        if _tts_failed(answer_tts):
            warning = TTS_WARNING
        else:
            answer_audio_url = answer_tts.get("audioUrl")
            answer_duration = float(answer_tts.get("duration", 0.0) or 0.0)
            avatar_state = _avatar_state("speaking", mouth_open=True)

        resume_text = await _resume_after_answer(room_id, answer)
        resume_audio_url = None
        resume_duration = 0.0
        if resume_text:
            resume_tts = await tts_synthesize(resume_text, room_id=room_id)
            if not _tts_failed(resume_tts):
                resume_audio_url = resume_tts.get("audioUrl")
                resume_duration = float(resume_tts.get("duration", 0.0) or 0.0)

        result = {
            "asrText": asr_text,
            "decision": decision,
            "answer": answer,
            "audioUrl": answer_audio_url,
            "duration": answer_duration,
            "resumeText": resume_text,
            "resumeAudioUrl": resume_audio_url,
            "resumeDuration": resume_duration,
            "sources": DEFAULT_SOURCES,
            "avatarState": avatar_state,
            "warning": warning,
            "events": events,
        }
        record_event(
            "public_voice_question",
            success=True,
            latency_ms=(perf_counter() - started) * 1000,
            payload={
                "roomId": room_id,
                "asrText": asr_text,
                "decision": decision,
                "hasAudio": bool(answer_audio_url),
            },
        )
        return result
    except Exception as e:
        record_event(
            "public_voice_question",
            success=False,
            latency_ms=(perf_counter() - started) * 1000,
            payload={"roomId": room_id, "error": str(e)},
        )
        raise
