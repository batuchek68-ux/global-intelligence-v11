from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from backend.services.audit_service import append_audit
from backend.services.self_improvement_service import record_execution_outcome

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class Task:
    id: str
    name: str
    agent_type: str
    input_data: dict[str, Any]
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)


class OrchestrationEngine:
    """v11 vertical industry team orchestration engine.

    The engine keeps the public API used by FastAPI while routing every query
    through the v11 operating loop: classify, extract, plan evidence, apply the
    risk gate, and synthesize an actionable team response.
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.agents: dict[str, Any] = {}
        self.execution_history: list[dict[str, Any]] = []
        logger.info("Orchestration Engine v11 initialized")

    def register_agent(self, agent_type: str, agent_instance: Any) -> None:
        self.agents[agent_type] = agent_instance
        logger.info("Agent registered: %s", agent_type)

    async def execute_query(
        self,
        query: str,
        org_id: str,
        user_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        execution_id = f"exec_{org_id}_{datetime.now().timestamp()}"
        metadata = metadata or {}

        try:
            task_graph = self._build_task_graph(query, metadata)
            results = await self._execute_task_graph(task_graph, org_id, user_id, execution_id)
            final_result = await self._synthesize_results(results, query)
            self._record_execution(execution_id, org_id, user_id, query, final_result)
            append_audit(
                "V11_CORE_ORCHESTRATION_EXECUTED",
                "DONE",
                f"Executed v11 industry team orchestration for {org_id}; status={final_result.get('status')}.",
                confidence=92,
                risk="LOW",
            )
            return {
                "execution_id": execution_id,
                "status": "success",
                "task_count": len(task_graph),
                "tasks": self._task_summaries(task_graph),
                "result": final_result,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as exc:  # pragma: no cover - defensive envelope
            logger.exception("Query execution failed: %s", exc)
            append_audit(
                "V11_CORE_ORCHESTRATION_FAILED",
                "FAILED",
                str(exc),
                confidence=80,
                risk="MEDIUM",
            )
            return {
                "execution_id": execution_id,
                "status": "failed",
                "error": str(exc),
                "timestamp": datetime.now().isoformat(),
            }

    def _build_task_graph(self, query: str, metadata: dict[str, Any] | None = None) -> list[Task]:
        base_input = {"query": query, "metadata": metadata or {}}
        return [
            Task(
                id="task_1",
                name="industry_intent_classification",
                agent_type="classifier",
                input_data=base_input,
            ),
            Task(
                id="task_2",
                name="entity_and_risk_extraction",
                agent_type="extractor",
                input_data=base_input,
                dependencies=["task_1"],
            ),
            Task(
                id="task_3",
                name="official_evidence_planning",
                agent_type="evidence_planner",
                input_data=base_input,
                dependencies=["task_1", "task_2"],
            ),
            Task(
                id="task_13",
                name="sanctions_screening",
                agent_type="sanctions_screening",
                input_data=base_input,
                dependencies=["task_2"],
            ),
            Task(
                id="task_14",
                name="counterparty_identity_verification",
                agent_type="counterparty_verification",
                input_data=base_input,
                dependencies=["task_2"],
            ),
            Task(
                id="task_4",
                name="web_research",
                agent_type="web_researcher",
                input_data=base_input,
                dependencies=["task_3"],
            ),
            Task(
                id="task_5",
                name="news_research",
                agent_type="news_researcher",
                input_data=base_input,
                dependencies=["task_3"],
            ),
            Task(
                id="task_6",
                name="academic_research",
                agent_type="academic_researcher",
                input_data=base_input,
                dependencies=["task_3"],
            ),
            Task(
                id="task_7",
                name="evidence_quality_assessment",
                agent_type="evidence_quality",
                input_data=base_input,
                dependencies=["task_4", "task_5", "task_6"],
            ),
            Task(
                id="task_8",
                name="approval_risk_gate",
                agent_type="risk_gate",
                input_data=base_input,
                dependencies=["task_2", "task_3", "task_7", "task_13", "task_14"],
            ),
            Task(
                id="task_9",
                name="systems_reasoning_and_method_lenses",
                agent_type="systems_reasoning",
                input_data=base_input,
                dependencies=[f"task_{task_id}" for task_id in range(1, 8)],
            ),
            Task(
                id="task_10",
                name="adversarial_counteranalysis",
                agent_type="adversarial_critic",
                input_data=base_input,
                dependencies=["task_2", "task_7", "task_9", "task_13", "task_14"],
            ),
            Task(
                id="task_11",
                name="decision_and_action_judgment",
                agent_type="decision_judge",
                input_data=base_input,
                dependencies=["task_7", "task_8", "task_9", "task_10"],
            ),
            Task(
                id="task_12",
                name="team_synthesis",
                agent_type="synthesizer",
                input_data=base_input,
                dependencies=[f"task_{task_id}" for task_id in range(1, 12)] + ["task_13", "task_14"],
            ),
        ]

    async def _execute_task_graph(
        self,
        task_graph: list[Task],
        org_id: str,
        user_id: str,
        execution_id: str,
    ) -> dict[str, Any]:
        del user_id, execution_id
        results: dict[str, Any] = {}
        pending = {task.id: task for task in task_graph}

        while pending:
            executable = [
                task
                for task in pending.values()
                if all(dependency in results and "error" not in results[dependency] for dependency in task.dependencies)
            ]
            if not executable:
                blocked = ", ".join(task.name for task in pending.values())
                raise RuntimeError(f"Task graph stalled; blocked tasks: {blocked}")

            task_results = await asyncio.gather(
                *(self._execute_single_task(task, org_id, results) for task in executable)
            )
            for task, result in zip(executable, task_results):
                results[task.id] = result
                pending.pop(task.id, None)

        return results

    async def _execute_single_task(
        self,
        task: Task,
        org_id: str,
        previous_results: dict[str, Any],
    ) -> dict[str, Any]:
        task.status = TaskStatus.RUNNING
        agent = self.agents.get(task.agent_type)
        if not agent:
            task.status = TaskStatus.FAILED
            task.error = f"Agent '{task.agent_type}' not found"
            return {"error": task.error}

        task_input = dict(task.input_data)
        for dependency in task.dependencies:
            task_input[f"prev_{dependency}"] = previous_results.get(dependency, {})

        try:
            if hasattr(agent, "execute_async"):
                result = await agent.execute_async(task_input, org_id)
            else:
                result = agent.execute(task_input, org_id)
            task.status = TaskStatus.COMPLETED
            task.result = result
            logger.info("Task completed: %s", task.name)
            return result
        except Exception as exc:  # pragma: no cover - defensive envelope
            task.status = TaskStatus.FAILED
            task.error = str(exc)
            if hasattr(agent, "metrics"):
                agent.metrics["errors"] += 1
            logger.exception("Task failed: %s", task.name)
            return {"error": str(exc)}

    async def _synthesize_results(self, results: dict[str, Any], original_query: str) -> dict[str, Any]:
        existing = results.get("task_12")
        if isinstance(existing, dict) and "error" not in existing:
            return existing

        synthesizer = self.agents.get("synthesizer")
        if not synthesizer:
            return {
                "status": "team_orchestration_incomplete",
                "query": original_query,
                "raw_results": results,
            }
        return await synthesizer.synthesize(results=results, original_query=original_query)

    def _record_execution(
        self,
        execution_id: str,
        org_id: str,
        user_id: str,
        query: str,
        result: dict[str, Any],
    ) -> None:
        self.execution_history.append(
            {
                "execution_id": execution_id,
                "org_id": org_id,
                "user_id": user_id,
                "query": query,
                "status": result.get("status"),
                "timestamp": datetime.now().isoformat(),
            }
        )
        record_execution_outcome(result)

    @staticmethod
    def _task_summaries(task_graph: list[Task]) -> list[dict[str, Any]]:
        summaries = []
        for task in task_graph:
            result_status = task.result.get("status") if isinstance(task.result, dict) else None
            summaries.append({
                "id": task.id,
                "name": task.name,
                "agent_type": task.agent_type,
                "status": result_status if result_status == "skipped" else task.status.value,
                "result_status": result_status,
                "detail": (
                    task.result.get("reason") or task.result.get("skip_reason")
                    if isinstance(task.result, dict)
                    else task.error
                ),
                "dependencies": task.dependencies,
            })
        return summaries
