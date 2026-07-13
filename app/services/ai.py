"""Product AI flows backed by the shared algorithm core.

Public API response fields remain stable.  Internal ``_`` fields are consumed
by API handlers for persistence decisions and are deliberately omitted by
Pydantic response models.
"""

from __future__ import annotations

import logging
from time import perf_counter

from app.core.config import settings
from app.core.errors import AppError
from app.core.logging import Timer
from app.providers.factory import get_llm
from app.services.algorithm_facade import algorithm_facade
from app.services.audio import asr_transcribe, tts_synthesize
from app.services.knowledge import search_knowledge
from app.services.rooms import get_room
from app.services.stats import record_event
from app.services.users import get_user_memory_tags, merge_user_memory_tags

logger = logging.getLogger(__name__)

TTS_WARNING = "TTS failed, text answer returned only."
NO_KNOWLEDGE_ANSWER = "当前知识库没有查到与该问题直接相关的可靠资料。你可以补充景点名称或向团长确认。"


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


def _join_warnings(*values: str | None) -> str | None:
    warnings = [value for value in values if value]
    return "; ".join(warnings) if warnings else None


def _decision_events(decision, private=None) -> list[dict]:
    events = [{"type": "decision", "payload": decision.model_dump()}]
    if decision.channel == "private":
        events.append(
            {
                "type": "suggest_private_channel",
                "payload": {"reason": "该问题属于私人需求，不适合公共播报"},
            }
        )
    if decision.needLeaderNotify:
        events.append(
            {
                "type": "leader_notify",
                "payload": {
                    "riskLevel": decision.riskLevel,
                    "message": getattr(private, "leaderMessage", None)
                    or "游客请求需要团长确认，请及时处理。",
                },
            }
        )
    return events


async def _answer_with_llm(room_id: str, question: str) -> dict | None:
    room = get_room(room_id)
    if room is None:
        logger.warning("AI question: room %s not found", room_id)
        return None

    spot = room.get("currentSpot", "")
    clean_question = question.strip()
    if not clean_question:
        return {"roomId": room_id, "answer": "您好，请问有什么可以帮您的？", "sources": []}

    # Product answers are grounded in the persisted knowledge base.  A model
    # is not called when retrieval has no evidence to cite.
    knowledge = search_knowledge(clean_question, 3, spot_id=spot)
    if not knowledge:
        return {
            "roomId": room_id,
            "answer": NO_KNOWLEDGE_ANSWER,
            "sources": [],
            "warning": "No matching knowledge-base evidence was found.",
        }

    context_text = "\n\n".join(
        f"[{item['title']}] {item['contentPreview']}" for item in knowledge
    )
    system_prompt = (
        "你是一个专业的景区 AI 导游，名叫小导。请使用友好、简洁的中文回答。"
        "只能依据下方知识库上下文回答景区事实；上下文没有的信息必须明确说不知道，"
        "不能补充未经引用的年代、人物、路线或服务信息。"
        f"当前游客所在景点：{spot or '景区入口'}。\n"
        f"知识库上下文：\n{context_text}"
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
        except Exception as exc:
            logger.error("LLM question failed: %s", exc)
            raise AppError(503, "LLM_UNAVAILABLE", "LLM provider is unavailable") from exc

    answer = (response.content or "").strip()
    if not answer:
        answer = NO_KNOWLEDGE_ANSWER
    return {
        "roomId": room_id,
        "answer": answer,
        "sources": [{"title": item["title"], "chunkId": item["chunkId"]} for item in knowledge],
        "warning": None if settings.llm_enabled else "Mock LLM mode is active.",
    }


async def _with_tts(answer: str, room_id: str, need_audio: bool) -> tuple[str | None, float, dict, str | None]:
    if not need_audio:
        return None, 0.0, _avatar_state("idle", mouth_open=False), None
    tts = await tts_synthesize(answer, room_id=room_id)
    if _tts_failed(tts):
        return None, 0.0, _avatar_state("idle", mouth_open=False), TTS_WARNING
    return (
        tts.get("audioUrl"),
        float(tts.get("duration", 0.0) or 0.0),
        _avatar_state("speaking", mouth_open=True),
        tts.get("warning"),
    )


async def public_question(
    room_id: str,
    question: str,
    need_audio: bool = True,
    user_id: str = "",
) -> dict | None:
    started = perf_counter()
    try:
        room = get_room(room_id)
        if room is None:
            return None
        memory_tags = get_user_memory_tags(user_id) if user_id else {}
        request = algorithm_facade.request(room, user_id or "guest", text=question, memory_tags=memory_tags)
        decision = algorithm_facade.decide(request)
        extracted_tags = algorithm_facade.extract_memory(question)
        if user_id:
            memory_tags = merge_user_memory_tags(user_id, extracted_tags)

        private = None
        if decision.nextAction in {
            "private_assistant",
            "human_takeover",
            "ask_authorization_then_notify_leader",
        }:
            private = algorithm_facade.private_answer(request)
            answer = private.answer
            sources: list[dict] = []
            warning = None
        elif decision.nextAction == "no_action":
            answer = "好的，我们继续当前导览。"
            sources = []
            warning = None
        else:
            qa_result = await _answer_with_llm(room_id, question)
            if qa_result is None:
                return None
            answer = qa_result["answer"]
            sources = qa_result.get("sources", [])
            warning = qa_result.get("warning")

        audio_url, duration, avatar_state, tts_warning = await _with_tts(answer, room_id, need_audio)
        state_update = (
            algorithm_facade.resume_after_answer(request, answer)
            if decision.needInterrupt
            else {"shouldResume": False, "resumeSegmentId": request.state.currentSegmentId, "resumeText": ""}
        )
        events = _decision_events(decision, private)
        result = {
            "roomId": room_id,
            "answer": answer,
            "audioUrl": audio_url,
            "duration": duration,
            "sources": sources,
            "avatarState": avatar_state,
            "warning": _join_warnings(warning, tts_warning),
            "decision": decision.decision,
            "events": events,
            "stateUpdate": state_update,
            "_replyChannel": decision.channel,
            "_decision": decision.model_dump(),
            "_stateUpdate": state_update,
            "_events": events,
            "_memoryTags": memory_tags,
        }
        record_event(
            "public_question",
            success=True,
            latency_ms=(perf_counter() - started) * 1000,
            payload={
                "roomId": room_id,
                "decision": decision.decision,
                "replyChannel": decision.channel,
                "hasAudio": bool(audio_url),
                "algorithm": "unified",
            },
        )
        return result
    except Exception as exc:
        record_event(
            "public_question", success=False,
            latency_ms=(perf_counter() - started) * 1000,
            payload={"roomId": room_id, "error": str(exc)},
        )
        raise


async def public_voice_question(
    room_id: str,
    user_id: str,
    channel: str,
    audio_url: str,
    audio_format: str | None = None,
    text_hint: str | None = None,
) -> dict | None:
    started = perf_counter()
    warning = None if settings.audio_provider_enabled else "Mock audio mode is active."
    try:
        room = get_room(room_id)
        if room is None:
            return None
        if not settings.enable_asr:
            raise AppError(503, "ASR_DISABLED", "ASR is disabled")
        asr_result = await asr_transcribe(
            room_id, user_id, channel, audio_url, audio_format=audio_format, text_hint=text_hint
        )
        if asr_result is None:
            return None

        asr_text = asr_result.get("text", "")
        confidence = float(asr_result.get("confidence", 0.0) or 0.0)
        request = algorithm_facade.request(
            room,
            user_id,
            channel=channel,
            text=asr_text,
            input_mode="voice",
            asr_confidence=confidence,
            memory_tags=get_user_memory_tags(user_id),
        )
        decision = algorithm_facade.decide(request)
        if asr_result.get("error"):
            decision = algorithm_facade.decide(request.model_copy(update={"asrConfidence": 0.0}))

        if decision.nextAction == "ask_clarification":
            result = {
                "asrText": asr_text or "（无法识别）",
                "asrConfidence": confidence,
                "decision": decision.decision,
                "answer": "我没有听清，可以再说一遍或改用文字输入吗？",
                "audioUrl": None,
                "duration": 0.0,
                "resumeText": "",
                "resumeAudioUrl": None,
                "resumeDuration": 0.0,
                "sources": [],
                "avatarState": _avatar_state("idle", mouth_open=False),
                "warning": _join_warnings(warning, asr_result.get("warning")),
                "events": _decision_events(decision),
                "_replyChannel": decision.channel,
                "_decision": decision.model_dump(),
            }
            return result

        extracted_tags = algorithm_facade.extract_memory(asr_text)
        memory_tags = merge_user_memory_tags(user_id, extracted_tags)
        private = None
        if decision.nextAction in {
            "private_assistant",
            "human_takeover",
            "ask_authorization_then_notify_leader",
        }:
            private = algorithm_facade.private_answer(request)
            answer = private.answer
            sources: list[dict] = []
            qa_warning = None
        else:
            qa_result = await _answer_with_llm(room_id, asr_text)
            if qa_result is None:
                return None
            answer = qa_result["answer"]
            sources = qa_result.get("sources", [])
            qa_warning = qa_result.get("warning")

        answer_audio_url, answer_duration, avatar_state, tts_warning = await _with_tts(answer, room_id, True)
        state_update = (
            algorithm_facade.resume_after_answer(request, answer)
            if decision.needInterrupt
            else {"shouldResume": False, "resumeSegmentId": request.state.currentSegmentId, "resumeText": ""}
        )
        resume_text = state_update.get("resumeText", "")
        resume_audio_url = None
        resume_duration = 0.0
        if resume_text:
            resume_tts = await tts_synthesize(resume_text, room_id=room_id)
            if not _tts_failed(resume_tts):
                resume_audio_url = resume_tts.get("audioUrl")
                resume_duration = float(resume_tts.get("duration", 0.0) or 0.0)

        events = _decision_events(decision, private)
        result = {
            "asrText": asr_text,
            "asrConfidence": confidence,
            "decision": decision.decision,
            "answer": answer,
            "audioUrl": answer_audio_url,
            "duration": answer_duration,
            "resumeText": resume_text,
            "resumeAudioUrl": resume_audio_url,
            "resumeDuration": resume_duration,
            "sources": sources,
            "avatarState": avatar_state,
            "warning": _join_warnings(warning, asr_result.get("warning"), qa_warning, tts_warning),
            "events": events,
            "_replyChannel": decision.channel,
            "_decision": decision.model_dump(),
            "_memoryTags": memory_tags,
        }
        record_event(
            "public_voice_question",
            success=True,
            latency_ms=(perf_counter() - started) * 1000,
            payload={
                "roomId": room_id,
                "decision": decision.decision,
                "replyChannel": decision.channel,
                "asrConfidence": confidence,
                "hasAudio": bool(answer_audio_url),
                "algorithm": "unified",
            },
        )
        return result
    except Exception as exc:
        record_event(
            "public_voice_question", success=False,
            latency_ms=(perf_counter() - started) * 1000,
            payload={"roomId": room_id, "error": str(exc)},
        )
        raise
