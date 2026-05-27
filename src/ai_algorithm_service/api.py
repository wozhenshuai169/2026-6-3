from __future__ import annotations

import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .evaluation import EvaluationHarness
from .orchestrator import TourAIOrchestrator
from .schemas import AlgorithmRequest


app = FastAPI(title="AI Algorithm Service", version="0.1.0")
orchestrator = TourAIOrchestrator()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ai-algorithm-service"}


@app.post("/v1/decision")
def decide(request: AlgorithmRequest) -> dict:
    return orchestrator.decide(request).model_dump()


@app.post("/v1/orchestrate")
def orchestrate(request: AlgorithmRequest) -> dict:
    return orchestrator.handle(request).model_dump()


@app.post("/v1/rag/query")
def rag_query(request: AlgorithmRequest) -> dict:
    return orchestrator.rag.query(request.text, request.state).model_dump()


@app.post("/v1/private-assistant")
def private_assistant(request: AlgorithmRequest) -> dict:
    return orchestrator.private_assistant.handle(request).model_dump()


@app.post("/v1/vision/recognize")
def vision_recognize(request: AlgorithmRequest) -> dict:
    return orchestrator.vision.recognize(request).model_dump()


@app.post("/v1/routes/recommend")
def route_recommend(request: AlgorithmRequest) -> dict:
    return orchestrator.recommend_routes(request).model_dump()


@app.post("/v1/memory/extract")
def memory_extract(request: AlgorithmRequest) -> dict:
    return orchestrator.extract_memory(request)


@app.post("/v1/evaluation/run")
def evaluation_run() -> dict:
    return EvaluationHarness(orchestrator).run()


@app.websocket("/ws/rooms/{room_id}/stream")
async def room_stream(websocket: WebSocket, room_id: str) -> None:
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            request = AlgorithmRequest(**{**payload, "roomId": room_id})
            response = orchestrator.handle(request)
            await websocket.send_json({"type": "decision", "payload": response.decision.model_dump()})
            if response.answer:
                for index, chunk in enumerate(_chunk_text(response.answer, size=18)):
                    await websocket.send_json({"type": "answer_delta", "index": index, "text": chunk})
                    await asyncio.sleep(0)
                await websocket.send_json(
                    {
                        "type": "answer_done",
                        "payload": {
                            "citations": [citation.model_dump() for citation in response.citations],
                            "stateUpdate": response.stateUpdate,
                        },
                    }
                )
    except WebSocketDisconnect:
        return


def _chunk_text(text: str, size: int) -> list[str]:
    return [text[index : index + size] for index in range(0, len(text), size)]

