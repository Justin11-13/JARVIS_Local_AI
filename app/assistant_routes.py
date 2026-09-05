"""Memory review and Codex REST/SSE surface for the loopback desktop client."""
import asyncio
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.coding_service import TERMINAL


class CodingRequest(BaseModel):
    project: str = Field(min_length=1, max_length=180)
    prompt: str = Field(min_length=1, max_length=20000)
    resume_id: str | None = None


class ApprovalRequest(BaseModel):
    request_id: str
    decision: str


class InputRequest(BaseModel):
    request_id: str
    answers: dict[str, str]


class ReviewRequest(BaseModel):
    status: str


class PreviewRequest(BaseModel):
    vault_id: str
    relative_path: str = ''


class ProjectRequest(BaseModel):
    project: str = Field(default='', max_length=180)


def routes(runtime, projects):
    def local_request(request: Request):
        # Desktop HTTP has no Origin; browser-originated mutation is not authorized.
        if request.method not in {'GET', 'HEAD', 'OPTIONS'} and request.headers.get('origin'):
            raise HTTPException(403, 'Use the local JARVIS desktop client for this action')

    router = APIRouter(dependencies=[Depends(local_request)])
    store = runtime.memory.store

    def attempt(call):
        try:
            return call()
        except (ValueError, OSError, RuntimeError) as error:
            raise HTTPException(400, str(error)) from error

    def project_path(name):
        records = projects()
        if name not in records:
            raise ValueError('Choose a registered project')
        item = records[name]
        return item['path'] if isinstance(item, dict) else item

    @router.get('/api/assistant/state')
    def state():
        return {'conversation': store.conversation_info(runtime.memory.conversation_id),
                'extraction': store.state('extraction', {'status': 'idle'}),
                'projects': list(projects()), 'trust_gate': {'available': False, 'reason': 'Authorized voice verification is not configured'}}

    @router.get('/api/memory')
    def memory_items():
        return {'items': sorted(store.items(), key=lambda item: item['updated_at'], reverse=True)}

    @router.post('/api/memory/extract')
    def extract():
        return {'queued': runtime.memories.trigger(force=True)}

    @router.post('/api/conversation/end')
    def end():
        runtime.memories.trigger(force=True)
        runtime.memory.clear()
        return {'conversation_id': runtime.memory.conversation_id}

    @router.post('/api/conversation/project')
    def set_project(request: ProjectRequest):
        if request.project:
            attempt(lambda: project_path(request.project))
        runtime.memories.trigger(force=True)
        runtime.memory.set_project(request.project)
        return {'conversation_id': runtime.memory.conversation_id}

    @router.get('/api/conversations')
    def conversations():
        with store.connect() as db:
            return {'conversations': [dict(row) for row in db.execute('SELECT * FROM conversations ORDER BY created_at DESC LIMIT 100')]}

    @router.get('/api/conversations/{identifier}')
    def conversation(identifier: str, after: int = 0):
        return {'conversation': store.conversation_info(identifier), 'turns': store.turns(identifier, 100, after, oldest=True)}

    @router.post('/api/conversations/{identifier}/resume')
    def resume_conversation(identifier: str):
        runtime.memories.trigger(force=True)
        attempt(lambda: runtime.memory.resume(identifier))
        return {'conversation_id': runtime.memory.conversation_id}

    @router.post('/api/memory/{identifier}/review')
    def review(identifier: str, request: ReviewRequest):
        return attempt(lambda: runtime.memories.review(identifier, request.status))

    @router.post('/api/memory/{identifier}/preview')
    def preview(identifier: str, request: PreviewRequest):
        return attempt(lambda: runtime.memories.preview(identifier, request.vault_id, request.relative_path))

    @router.post('/api/memory/publish/{token}')
    def publish(token: str):
        # This POST is explicit approval of the exact server-stored merge preview.
        return attempt(lambda: runtime.memories.publish(token))

    @router.get('/api/coding/tasks')
    def tasks():
        return {'tasks': store.tasks()}

    @router.post('/api/coding/tasks')
    def create(request: CodingRequest):
        return attempt(lambda: runtime.coding.create(request.project, project_path(request.project), request.prompt, request.resume_id))

    @router.get('/tasks/{identifier}')
    def task(identifier: str):
        result = store.task(identifier)
        if not result:
            raise HTTPException(404, 'Task not found')
        return result

    @router.get('/tasks/{identifier}/events')
    async def events(identifier: str, request: Request, after: int = 0, last_event_id: str | None = Header(default=None)):
        task(identifier)
        try:
            cursor = max(0, int(last_event_id) if last_event_id else after)
        except ValueError:
            raise HTTPException(400, 'Invalid event cursor')

        async def stream():
            nonlocal cursor
            while not await request.is_disconnected():
                batch = await asyncio.to_thread(store.events, identifier, cursor)
                for event in batch:
                    cursor = event['id']
                    yield f"id: {cursor}\nevent: {event['type']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                snapshot = await asyncio.to_thread(store.task, identifier)
                if not batch and snapshot['status'] in TERMINAL:
                    return
                if not batch:
                    yield ': heartbeat\n\n'
                await asyncio.sleep(.5)
        return StreamingResponse(stream(), media_type='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

    @router.post('/tasks/{identifier}/approve')
    def approve(identifier: str, request: ApprovalRequest):
        attempt(lambda: runtime.coding.answer(identifier, request.request_id, decision=request.decision))
        return task(identifier)

    @router.post('/tasks/{identifier}/input')
    def provide_input(identifier: str, request: InputRequest):
        attempt(lambda: runtime.coding.answer(identifier, request.request_id, answers=request.answers))
        return task(identifier)

    @router.post('/tasks/{identifier}/cancel')
    def cancel(identifier: str):
        task(identifier)
        return attempt(lambda: runtime.coding.cancel(identifier))

    @router.delete('/api/coding/grants')
    def revoke_grants():
        with store.connect() as db:
            db.execute("DELETE FROM state WHERE key LIKE 'grant:%'")
        return {'revoked': True}

    return router
