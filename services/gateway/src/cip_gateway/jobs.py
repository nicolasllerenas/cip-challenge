import asyncio
from collections.abc import AsyncIterator

from cip_contracts import Draft, EventType, JobEvent

from cip_gateway.store import GatewayStore, Job, JobKind

INTERRUPTED = "El asistente se cerró mientras trabajaba. Vuelve a intentarlo; tu biblioteca está intacta."
CANCELLED = "Cancelaste el trabajo. Puedes volver a pedirlo cuando quieras."
STOPPED = "El trabajo se detuvo inesperadamente."


class JobManager:
    def __init__(self, store: GatewayStore, heartbeat_seconds: float) -> None:
        self._store = store
        self._heartbeat = heartbeat_seconds
        self._tasks: dict[str, asyncio.Task] = {}
        self._signals: dict[str, asyncio.Condition] = {}
        for job_id in store.interrupted_jobs():
            store.append_event(
                job_id, JobEvent(type=EventType.JOB_FAILED, message=INTERRUPTED, data={"code": "interrupted"})
            )

    def start(self, kind: JobKind, subject_id: str, source: AsyncIterator[JobEvent]) -> Job:
        job = self._store.create_job(kind, subject_id)
        self._signals[job.job_id] = asyncio.Condition()
        self._tasks[job.job_id] = asyncio.create_task(self._consume(job.job_id, source))
        return job

    def _persist_draft(self, job_id: str, event: JobEvent) -> JobEvent:
        if event.type != EventType.JOB_COMPLETED or "draft" not in event.data:
            return event
        draft = Draft.model_validate(event.data["draft"])
        self._store.save_draft(job_id, draft)
        return event.model_copy(update={"data": {"draft_id": draft.draft_id, "stats": draft.stats.model_dump()}})

    async def _append(self, job_id: str, event: JobEvent) -> None:
        self._store.append_event(job_id, self._persist_draft(job_id, event))
        signal = self._signals.get(job_id)
        if signal:
            async with signal:
                signal.notify_all()

    def _close(self, job_id: str) -> None:
        self._signals.pop(job_id, None)

    async def _consume(self, job_id: str, source: AsyncIterator[JobEvent]) -> None:
        stopped = JobEvent(type=EventType.JOB_FAILED, message=STOPPED, data={"code": "stopped"})
        try:
            async for event in source:
                await self._append(job_id, event)
                if event.is_terminal:
                    break
            else:
                await self._append(job_id, stopped)
            self._close(job_id)
        except Exception:
            await self._append(job_id, stopped)
            self._close(job_id)
        finally:
            self._tasks.pop(job_id, None)

    async def cancel(self, job_id: str) -> bool:
        task = self._tasks.get(job_id)
        if task is None:
            return False
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        await self._append(job_id, JobEvent(type=EventType.JOB_CANCELLED, message=CANCELLED))
        self._close(job_id)
        return True

    async def subscribe(self, job_id: str, after: int = 0) -> AsyncIterator[JobEvent | None]:
        last = after
        while True:
            signal = self._signals.get(job_id)
            if signal is None:
                for event in self._store.events(job_id, last):
                    yield event
                return
            async with signal:
                pending = self._store.events(job_id, last)
                if not pending:
                    try:
                        await asyncio.wait_for(signal.wait(), self._heartbeat)
                    except TimeoutError:
                        pending = None
            if pending is None:
                yield None
                continue
            for event in pending:
                last = event.seq
                yield event
                if event.is_terminal:
                    return
