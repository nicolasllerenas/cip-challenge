from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from cip_agents.config import Settings

Effort = Literal["low", "medium", "high", "xhigh", "max"]


class Task(StrEnum):
    PLAN = "planner"
    WRITE = "writer"
    VERIFY = "verifier"
    REPAIR = "repairer"


@dataclass(frozen=True)
class Route:
    model: str
    effort: Effort
    max_tokens: int


class ModelRouter:
    def __init__(self, settings: Settings) -> None:
        fast, strong = settings.model_fast, settings.model_strong
        self._routes = {
            Task.PLAN: Route(fast, "low", 4000),
            Task.VERIFY: Route(fast, "low", 8000),
            Task.WRITE: Route(strong, "high", 16000),
            Task.REPAIR: Route(strong, "medium", 8000),
        }
        self._escalation = Route(strong, "medium", 16000)

    def route(self, task: Task, attempt: int = 0) -> Route:
        return self._routes[task] if attempt == 0 else self._escalation

    def assignments(self) -> dict[str, str]:
        return {task.value: route.model for task, route in self._routes.items()}
