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
from app.services.avatar_settings import get_avatar_settings
from app.services.audio import asr_transcribe, tts_synthesize
from app.services.knowledge import search_knowledge
from app.services.rooms import get_room
from app.services.spoken_text import sanitize_spoken_text
from app.services.stats import record_event
from app.services.users import get_user_memory_tags, merge_user_memory_tags

logger = logging.getLogger(__name__)

TTS_WARNING = "语音暂时无法播放，已保留文字回答。"


def _analytics_topic(text: str) -> str:
    categories = [
        ("历史文化", ["历史", "玄奘", "文化", "佛教", "故事"]),
        ("景点特色", ["建筑", "特色", "多高", "面积", "材料", "看点"]),
        ("路线推荐", ["路线", "怎么走", "下一站", "少走路"]),
        ("服务设施", ["厕所", "卫生间", "饮水", "休息", "出口"]),
        ("票务与开放", ["门票", "票价", "开放", "几点", "演出"]),
        ("安全协助", ["走失", "走丢", "不舒服", "头晕", "封路"]),
    ]
    for topic, words in categories:
        if any(word in text for word in words):
            return topic
    return "其他咨询"


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


async def _answer_with_llm(
    room_id: str,
    question: str,
    guidance: str = "",
) -> dict | None:
    room = get_room(room_id)
    if room is None:
        logger.warning("AI question: room %s not found", room_id)
        return None

    spot = room.get("currentSpot", "")
    clean_question = question.strip()
    if not clean_question:
        raise AppError(422, "QUESTION_EMPTY", "Question must not be empty")

    # Group Q&A is always backed by the configured real DeepSeek provider.
    # Provider failures must remain visible instead of returning canned text.
    if not settings.deepseek_api_key.strip():
        raise AppError(503, "LLM_NOT_CONFIGURED", "智能问答服务未配置")

    knowledge = search_knowledge(clean_question, 3, spot_id=spot)
    context_text = (
        "\n\n".join(f"[{item['title']}] {item['contentPreview']}" for item in knowledge)
        if knowledge
        else "知识库未检索到与问题直接相关的资料。"
    )
    system_prompt = (
        "你负责灵山胜境的中文导览问答。请像景区讲解员一样直接、友好、简洁地回答游客的问题。"
        "除非游客明确询问系统身份，否则不要主动提及人工智能、模型、算法或服务提供商，也不要使用夸张的科技宣传语。"
        "如果游客询问身份，应如实说明“我是云游智导的导览助手”，不得冒充真人。"
        "不能只回复“继续当前导览”或其他占位话术。景点历史、人物、年代和设施位置"
        "等事实应优先依据知识库；知识库没有依据时要明确说明不确定，不得编造精确事实。"
        "安全、路线和一般游览建议可以依据常识回答，紧急情况建议联系现场工作人员。\n"
        "回答只使用文字和正常的中英文句子标点，不得使用Markdown、星号、井号、下划线或项目符号。\n"
        f"当前景点：{spot or '未指定'}\n"
        f"知识库资料：\n{context_text}"
    )
    if guidance:
        system_prompt += f"\n本次产品安全与隐私指引：{guidance}"

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
            raise AppError(503, "LLM_UNAVAILABLE", "智能问答服务暂时不可用") from exc

    answer = sanitize_spoken_text(response.content or "")
    if not answer:
        raise AppError(503, "LLM_EMPTY_RESPONSE", "智能问答服务没有返回内容")
    return {
        "roomId": room_id,
        "answer": answer,
        "sources": [{"title": item["title"], "chunkId": item["chunkId"]} for item in knowledge],
        "warning": None if knowledge else "知识库没有直接依据，回答已避免编造精确景区事实。",
        "provider": "deepseek",
    }


async def _with_tts(
    answer: str,
    room_id: str | None,
    need_audio: bool,
    voice: str = "guide_female",
) -> tuple[str | None, float, dict, str | None]:
    if not need_audio:
        return None, 0.0, _avatar_state("idle", mouth_open=False), None
    speech_settings = get_avatar_settings()
    tts = await tts_synthesize(
        answer,
        voice=voice,
        speed=float(speech_settings["speed"]),
        room_id=room_id,
    )
    if _tts_failed(tts):
        return None, 0.0, _avatar_state("idle", mouth_open=False), TTS_WARNING
    return (
        tts.get("audioUrl"),
        float(tts.get("duration", 0.0) or 0.0),
        _avatar_state("speaking", mouth_open=True),
        tts.get("warning"),
    )


async def solo_question(
    question: str,
    current_spot_id: str = "",
    need_audio: bool = True,
    user_id: str = "",
    voice: str = "guide_female",
    input_mode: str = "text",
    asr_confidence: float | None = None,
) -> dict:
    """Answer a tourist privately without requiring or notifying a room."""
    started = perf_counter()
    clean_question = question.strip()
    spot = current_spot_id.strip()
    has_knowledge = False
    event_type = "solo_voice_question" if input_mode == "voice" else "solo_question"
    try:
        # Solo mode is explicitly a real-AI flow.  Never let the provider
        # Solo mode always requires a configured real model provider.
        if not settings.deepseek_api_key.strip():
            raise AppError(
                503,
                "LLM_NOT_CONFIGURED",
                "智能问答服务未配置",
            )

        knowledge = search_knowledge(clean_question, 3, spot_id=spot)
        has_knowledge = bool(knowledge)
        if knowledge:
            context_text = "\n\n".join(
                f"[{item['title']}] {item['contentPreview']}" for item in knowledge
            )
        else:
            context_text = "知识库未检索到与问题直接相关的资料。"

        system_prompt = (
            "你负责灵山胜境的独自导览问答。回答要友好、简洁、实用，像景区服务人员一样自然。"
            "除非游客明确询问系统身份，否则不要主动提及人工智能、模型、算法或服务提供商。"
            "如果游客询问身份，应如实说明“我是云游智导的导览助手”，不得冒充真人。"
            "游客当前未加入旅行团；本次对话是私人的，不会广播，也不能通知团长。"
            "景点历史、人物、年代和设施位置等事实应优先依据下方知识库。"
            "知识库没有依据时，要明确说明不确定，不得编造精确事实或实时状态；"
            "路线、安全和一般游览建议可以基于常识回答，并建议游客用“附近设施”"
            "查看实时位置，紧急情况联系现场工作人员。"
            "回答只使用文字和正常的中英文句子标点，不得使用Markdown、星号、井号、下划线或项目符号。\n"
            f"当前景点：{spot or '未指定'}\n"
            f"知识库资料：\n{context_text}"
        )

        llm = get_llm()
        with Timer(logger, f"Solo LLM question '{clean_question[:20]}...'"):
            try:
                response = await llm.chat(
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": clean_question},
                    ],
                    context={"current_spot": spot, "mode": "solo"},
                    timeout=settings.request_timeout,
                )
            except Exception as exc:
                logger.error("Solo LLM question failed: %s", exc)
                raise AppError(
                    503,
                    "LLM_UNAVAILABLE",
                    "智能问答服务暂时不可用",
                ) from exc

        answer = sanitize_spoken_text(response.content or "")
        if not answer:
            raise AppError(503, "LLM_EMPTY_RESPONSE", "智能问答服务没有返回内容")

        audio_url, duration, avatar_state, tts_warning = await _with_tts(
            answer, None, need_audio, voice
        )
        knowledge_warning = None if knowledge else "知识库没有直接依据，回答已避免编造精确景区事实。"
        result = {
            "answer": answer,
            "audioUrl": audio_url,
            "duration": duration,
            "sources": [
                {"title": item["title"], "chunkId": item["chunkId"]}
                for item in knowledge
            ],
            "avatarState": avatar_state,
            "warning": _join_warnings(knowledge_warning, tts_warning),
            "mode": "solo",
            "provider": "deepseek",
        }
        record_event(
            event_type,
            success=True,
            latency_ms=(perf_counter() - started) * 1000,
            payload={
                "userId": user_id,
                "currentSpot": spot,
                "hasKnowledge": has_knowledge,
                "hasAudio": bool(audio_url),
                "provider": "deepseek",
                "topic": _analytics_topic(clean_question),
                "asrConfidence": asr_confidence,
            },
        )
        return result
    except Exception as exc:
        record_event(
            event_type,
            success=False,
            latency_ms=(perf_counter() - started) * 1000,
            payload={
                "userId": user_id,
                "currentSpot": spot,
                "hasKnowledge": has_knowledge,
                "error": str(exc),
            },
        )
        raise


async def public_question(
    room_id: str,
    question: str,
    need_audio: bool = True,
    user_id: str = "",
    voice: str = "guide_female",
    input_mode: str = "text",
    asr_confidence: float | None = None,
) -> dict | None:
    started = perf_counter()
    try:
        room = get_room(room_id)
        if room is None:
            return None
        memory_tags = get_user_memory_tags(user_id) if user_id else {}
        request = algorithm_facade.request(
            room,
            user_id or "guest",
            text=question,
            input_mode=input_mode,
            asr_confidence=asr_confidence,
            memory_tags=memory_tags,
        )
        decision = algorithm_facade.decide(request)
        extracted_tags = algorithm_facade.extract_memory(question)
        if user_id:
            memory_tags = merge_user_memory_tags(user_id, extracted_tags)

        private = None
        guidance = ""
        if decision.nextAction in {
            "private_assistant",
            "human_takeover",
            "ask_authorization_then_notify_leader",
        }:
            private = algorithm_facade.private_answer(request)
            guidance = (
                "该问题包含私人需求或安全风险，不要在公共频道暴露隐私。"
                "请给出可执行且谨慎的帮助建议。产品规则建议：" + private.answer
            )
        elif decision.nextAction == "no_action":
            guidance = "即使问题很简短，也要针对问题自然回答，不能返回固定的继续导览话术。"

        qa_result = await _answer_with_llm(room_id, question, guidance=guidance)
        if qa_result is None:
            return None
        answer = qa_result["answer"]
        sources = qa_result.get("sources", [])
        warning = qa_result.get("warning")

        audio_url, duration, avatar_state, tts_warning = await _with_tts(
            answer, room_id, need_audio, voice
        )
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
            "provider": "deepseek",
            "_replyChannel": decision.channel,
            "_decision": decision.model_dump(),
            "_stateUpdate": state_update,
            "_events": events,
            "_memoryTags": memory_tags,
        }
        event_type = "public_voice_question" if input_mode == "voice" else "public_question"
        record_event(
            event_type,
            success=True,
            latency_ms=(perf_counter() - started) * 1000,
            payload={
                "roomId": room_id,
                "decision": decision.decision,
                "replyChannel": decision.channel,
                "hasAudio": bool(audio_url),
                "algorithm": "unified",
                "provider": "deepseek",
                "question": question if input_mode == "text" and decision.channel == "public" else "",
                "asrText": question if input_mode == "voice" and decision.channel == "public" else "",
                "asrConfidence": asr_confidence,
                "topic": _analytics_topic(question),
            },
        )
        return result
    except Exception as exc:
        record_event(
            "public_voice_question" if input_mode == "voice" else "public_question", success=False,
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
    voice: str = "guide_female",
) -> dict | None:
    started = perf_counter()
    warning = None if settings.audio_provider_enabled else "语音识别服务未配置。"
    try:
        room = get_room(room_id)
        if room is None:
            return None
        if not settings.enable_asr:
            raise AppError(503, "ASR_DISABLED", "语音识别服务未启用")
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
        guidance = ""
        if decision.nextAction in {
            "private_assistant",
            "human_takeover",
            "ask_authorization_then_notify_leader",
        }:
            private = algorithm_facade.private_answer(request)
            guidance = (
                "该语音问题包含私人需求或安全风险，不要在公共频道暴露隐私。"
                "请给出可执行且谨慎的帮助建议。产品规则建议：" + private.answer
            )
        elif decision.nextAction == "no_action":
            guidance = "即使问题很简短，也要针对问题自然回答，不能返回固定的继续导览话术。"

        qa_result = await _answer_with_llm(room_id, asr_text, guidance=guidance)
        if qa_result is None:
            return None
        answer = qa_result["answer"]
        sources = qa_result.get("sources", [])
        qa_warning = qa_result.get("warning")

        answer_audio_url, answer_duration, avatar_state, tts_warning = await _with_tts(
            answer, room_id, True, voice
        )
        state_update = (
            algorithm_facade.resume_after_answer(request, answer)
            if decision.needInterrupt
            else {"shouldResume": False, "resumeSegmentId": request.state.currentSegmentId, "resumeText": ""}
        )
        resume_text = state_update.get("resumeText", "")
        resume_audio_url = None
        resume_duration = 0.0
        if resume_text:
            resume_tts = await tts_synthesize(resume_text, voice=voice, room_id=room_id)
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
            "provider": "deepseek",
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
                "asrText": asr_text if decision.channel == "public" else "",
                "topic": _analytics_topic(asr_text),
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
