from __future__ import annotations

import asyncio
from typing import Any

from backend.services.due_diligence_service import screen_sanctions, verify_counterparty
from backend.services.search_service import multi_source_search


def _contains_any(text: str, terms: list[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


class BaseAgent:
    def __init__(self, name: str):
        self.name = name
        self.metrics = {"executions": 0, "errors": 0}

    async def execute_async(self, input_data: dict[str, Any], org_id: str) -> dict[str, Any]:
        raise NotImplementedError

    def execute(self, input_data: dict[str, Any], org_id: str) -> dict[str, Any]:
        raise NotImplementedError

    def _done(self, data: dict[str, Any]) -> dict[str, Any]:
        self.metrics["executions"] += 1
        return data


class ClassifierAgent(BaseAgent):
    def __init__(self):
        super().__init__("classifier")

    async def execute_async(self, input_data: dict[str, Any], org_id: str) -> dict[str, Any]:
        query = str(input_data.get("query") or "")
        intent = "project_execution"
        if _contains_any(query, ["customs", "tariff", "hs code", "海关", "关税", "清关"]):
            intent = "customs_trade_risk"
        elif _contains_any(query, ["video", "youtube", "tiktok", "douyin", "抖音", "视频", "视频号"]):
            intent = "video_media_plan"
        elif _contains_any(query, ["research", "paper", "library", "科研", "论文", "学术", "图书馆"]):
            intent = "research_intelligence"
        elif _contains_any(query, ["investment", "招商", "investor", "developer", "投资", "开发商"]):
            intent = "investment_promotion"
        return self._done(
            {
                "intent": intent,
                "confidence": 0.9,
                "query": query,
                "operating_mode": "vertical_industry_team",
            }
        )


class ExtractorAgent(BaseAgent):
    def __init__(self):
        super().__init__("extractor")

    async def execute_async(self, input_data: dict[str, Any], org_id: str) -> dict[str, Any]:
        query = str(input_data.get("query") or "")
        countries: list[str] = []
        if _contains_any(query, ["kazakhstan", "哈萨克斯坦"]):
            countries.append("Kazakhstan")
        if _contains_any(query, ["indonesia", "印尼", "印度尼西亚"]):
            countries.append("Indonesia")
        if _contains_any(query, ["uzbekistan", "乌兹别克斯坦"]):
            countries.append("Uzbekistan")
        if _contains_any(query, ["central asia", "中亚"]):
            countries.append("Central Asia")
        if not countries:
            countries.append("Kazakhstan")

        risk_terms = [
            term
            for term in [
                "customs",
                "tariff",
                "payment",
                "contract",
                "sanction",
                "export control",
                "海关",
                "关税",
                "付款",
                "合同",
                "制裁",
                "出口管制",
                "报价",
                "承诺",
            ]
            if _contains_any(query, [term])
        ]
        return self._done(
            {
                "countries": countries,
                "keywords": [item for item in query.replace(",", " ").split() if item],
                "risk_terms": risk_terms,
                "entities_required": [
                    "project_owner",
                    "developer",
                    "government_authority",
                    "responsible_person",
                    "customs_authority",
                    "procurement_contact",
                ],
            }
        )


class EvidencePlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__("evidence_planner")

    async def execute_async(self, input_data: dict[str, Any], org_id: str) -> dict[str, Any]:
        query = str(input_data.get("query") or "")
        metadata = input_data.get("metadata") if isinstance(input_data.get("metadata"), dict) else {}
        extracted = input_data.get("prev_task_2", {})
        country = str(metadata.get("country") or (extracted.get("countries") or ["Kazakhstan"])[0])
        return self._done(
            {
                "country": country,
                "required_sources": [
                    "government project page",
                    "official procurement or tender page",
                    "customs authority, tariff, HS code, and import document source",
                    "official owner, developer, investor, or regulator announcement",
                    "academic, patent, library, or standards source for technical feasibility",
                    "reputable media plus social/video signals for attention tracking only",
                ],
                "search_queries": [
                    f'{country} "{query}" official government project owner developer',
                    f'{country} "{query}" tender procurement EPC contractor',
                    f'{country} customs HS code tariff import documents "{query}"',
                    f'{country} investment promotion "{query}" investor developer official',
                    f'{country} "{query}" feasibility study EIA ministry akimat',
                    f'{country} "{query}" YouTube TikTok Douyin Telegram forum public attention',
                ],
                "search_queries_by_category": {
                    "web": f'{country} "{query}" official government procurement regulator',
                    "news": f'{country} "{query}" infrastructure trade project news',
                    "academic": f'{country} "{query}" feasibility study technical research',
                },
                "evidence_rule": "Government, customs, procurement, regulator, and official company pages are required before outreach or feasibility conclusions.",
            }
        )


class RiskGateAgent(BaseAgent):
    def __init__(self):
        super().__init__("risk_gate")

    async def execute_async(self, input_data: dict[str, Any], org_id: str) -> dict[str, Any]:
        extracted = input_data.get("prev_task_2", {})
        evidence_plan = input_data.get("prev_task_3", {})
        evidence_quality = input_data.get("prev_task_7", {})
        sanctions = input_data.get("prev_task_13", {})
        counterparties = input_data.get("prev_task_14", {})
        risk_terms = extracted.get("risk_terms", [])
        sanctions_status = sanctions.get("status")
        counterparty_status = counterparties.get("status")
        due_diligence_review_required = (
            sanctions_status in {"potential_match", "inconclusive", "unavailable"}
            or counterparty_status in {"partial", "unverified", "conflicting", "unavailable"}
        )
        needs_approval = bool(risk_terms) or due_diligence_review_required
        return self._done(
            {
                "needs_human_approval": needs_approval,
                "due_diligence_review_required": due_diligence_review_required,
                "sanctions_status": sanctions_status or "not_requested",
                "counterparty_status": counterparty_status or "not_requested",
                "evidence_review_required": evidence_quality.get("quality_score", 0) < 0.6,
                "evidence_quality_score": evidence_quality.get("quality_score", 0),
                "risk_terms": risk_terms,
                "minimum_evidence": evidence_plan.get("required_sources", [])[:4],
                "blocked_actions": [
                    "external commitment",
                    "formal quotation",
                    "contract or payment approval",
                    "delivery promise",
                    "public publishing",
                    "official social reply",
                ],
                "allowed_actions": [
                    "internal draft",
                    "search plan",
                    "evidence checklist",
                    "project task board",
                    "human approval request",
                ],
            }
        )


class SanctionsScreeningAgent(BaseAgent):
    contract = {
        "when_to_call": "A named counterparty is supplied or sanctions screening is explicitly requested for a high-risk query.",
        "input": "metadata.counterparties[] with name and optional aliases; optional sanctions_screening_required flag.",
        "output": "potential_match, no_match_found, inconclusive, unavailable, or skipped, with per-jurisdiction source status.",
        "acceptance": "no_match_found requires every configured jurisdiction source to be available; unresolved results require human review.",
        "permissions": ["read supplied entity names", "read registered sanctions-list providers"],
    }

    def __init__(self):
        super().__init__("sanctions_screening")

    async def execute_async(self, input_data: dict[str, Any], org_id: str) -> dict[str, Any]:
        del org_id
        metadata = input_data.get("metadata") if isinstance(input_data.get("metadata"), dict) else {}
        extracted = input_data.get("prev_task_2", {})
        parties = metadata.get("counterparties", [])
        if isinstance(parties, dict):
            parties = [parties]
        if not isinstance(parties, list):
            parties = []
        entities = [party for party in parties if isinstance(party, dict)]
        requested = bool(metadata.get("sanctions_screening_required") or extracted.get("risk_terms"))
        if not entities and not requested:
            return self._done({"status": "skipped", "screenings": [], "reason": "No screening trigger or named counterparty was supplied."})
        if not entities:
            return self._done({"status": "inconclusive", "screenings": [], "reason": "Screening was requested but no named entity was supplied."})

        screenings = await asyncio.gather(
            *(asyncio.to_thread(screen_sanctions, entity) for entity in entities)
        )
        statuses = {item["screening_status"] for item in screenings}
        if "potential_match" in statuses:
            status = "potential_match"
        elif statuses == {"no_match_found"}:
            status = "no_match_found"
        else:
            status = "inconclusive"
        return self._done({"status": status, "screenings": screenings})


class CounterpartyVerificationAgent(BaseAgent):
    contract = {
        "when_to_call": "A named counterparty is supplied for project, transaction, or external engagement review.",
        "input": "metadata.counterparties[] with name and country; registration number and aliases are optional.",
        "output": "verified, partial, unverified, conflicting, unavailable, or skipped, with registry evidence references.",
        "acceptance": "verified requires a registered jurisdiction adapter to return legal name, country, registration number, and source.",
        "permissions": ["read supplied entity details", "read registered official company-registry providers"],
    }

    def __init__(self):
        super().__init__("counterparty_verification")

    async def execute_async(self, input_data: dict[str, Any], org_id: str) -> dict[str, Any]:
        del org_id
        metadata = input_data.get("metadata") if isinstance(input_data.get("metadata"), dict) else {}
        parties = metadata.get("counterparties", [])
        if isinstance(parties, dict):
            parties = [parties]
        if not isinstance(parties, list):
            parties = []
        entities = [party for party in parties if isinstance(party, dict)]
        if not entities:
            return self._done({"status": "skipped", "verifications": [], "reason": "No named counterparty was supplied."})

        verifications = await asyncio.gather(
            *(asyncio.to_thread(verify_counterparty, entity) for entity in entities)
        )
        statuses = {item["identity_status"] for item in verifications}
        if "conflicting" in statuses:
            status = "conflicting"
        elif statuses == {"verified"}:
            status = "verified"
        elif statuses == {"unavailable"}:
            status = "unavailable"
        else:
            status = "partial"
        return self._done({"status": status, "verifications": verifications})


class SearchResearchAgent(BaseAgent):
    def __init__(self, category: str):
        super().__init__(f"{category}_researcher")
        self.category = category

    async def execute_async(self, input_data: dict[str, Any], org_id: str) -> dict[str, Any]:
        del org_id
        query = str(input_data.get("query") or "").strip()
        plan = input_data.get("prev_task_3", {})
        queries = [query] if query else []
        by_category = plan.get("search_queries_by_category", {})
        if isinstance(by_category, dict):
            category_query = str(by_category.get(self.category) or "").strip()
            if category_query and category_query not in queries:
                queries.append(category_query)
        planned = plan.get("search_queries", [])
        fallback_index = {"web": 0, "news": 5, "academic": 4}.get(self.category, 0)
        if isinstance(planned, list) and len(planned) > fallback_index:
            fallback = str(planned[fallback_index]).strip()
            if fallback and fallback not in queries:
                queries.append(fallback)

        reports = []
        for search_query in queries[:2]:
            try:
                report = await asyncio.to_thread(multi_source_search, search_query, [self.category])
            except Exception as error:
                report = {
                    "ok": False,
                    "query": search_query,
                    "results": {self.category: []},
                    "total_results": 0,
                    "source_status": {},
                    "status": "error",
                    "error": type(error).__name__,
                }
            reports.append(report)
            if report.get("total_results", 0) >= 3:
                break

        merged: dict[str, dict[str, Any]] = {}
        source_status: dict[str, Any] = {}
        for report in reports:
            for result in report.get("results", {}).get(self.category, []):
                merged.setdefault(result.get("url", ""), result)
            source_status.update(report.get("source_status", {}))

        return self._done({
            "category": self.category,
            "queries_used": [report.get("query") for report in reports],
            "results": {self.category: list(merged.values())},
            "total_results": len(merged),
            "source_status": source_status,
            "iterations": len(reports),
            "status": "complete" if merged else "degraded",
        })


class EvidenceQualityAgent(BaseAgent):
    def __init__(self):
        super().__init__("evidence_quality")

    async def execute_async(self, input_data: dict[str, Any], org_id: str) -> dict[str, Any]:
        del org_id
        categories = ("web", "news", "academic")
        reports = [input_data.get(f"prev_task_{task_id}", {}) for task_id in (4, 5, 6)]
        covered = [report.get("category") for report in reports if report.get("total_results", 0) > 0]
        providers = {
            provider
            for report in reports
            for provider, status in report.get("source_status", {}).items()
            if status.get("status") == "ok"
        }
        source_status = {
            provider: status
            for report in reports
            for provider, status in report.get("source_status", {}).items()
        }
        evidence_count = sum(report.get("total_results", 0) for report in reports)
        score = round(
            0.4 * min(len(covered), len(categories)) / len(categories)
            + 0.3 * min(len(providers), 3) / 3
            + 0.3 * min(evidence_count, 5) / 5,
            3,
        )
        return self._done({
            "quality_score": score,
            "evidence_count": evidence_count,
            "covered_categories": covered,
            "successful_providers": sorted(providers),
            "provider_status": source_status,
            "review_required": score < 0.6,
            "assessment": "preliminary_source_coverage_only; claims require human verification",
        })


class SystemsReasoningAgent(BaseAgent):
    def __init__(self):
        super().__init__("systems_reasoning")

    async def execute_async(self, input_data: dict[str, Any], org_id: str) -> dict[str, Any]:
        del org_id
        query = str(input_data.get("query") or "").strip()
        quality = input_data.get("prev_task_7", {})
        evidence_count = sum(
            report.get("total_results", 0)
            for report in (input_data.get(f"prev_task_{task_id}", {}) for task_id in (4, 5, 6))
        )
        methods = [
            {
                "name": "first_principles",
                "question": "Which constraints are directly evidenced, and which are assumptions?",
            },
            {
                "name": "falsification",
                "question": "What observable evidence would disprove the leading interpretation?",
            },
            {
                "name": "second_order_effects",
                "question": "If the proposed next step succeeds, what new costs, dependencies, or risks follow?",
            },
            {
                "name": "base_rates",
                "question": "What comparable cases or historical rates are needed before estimating likelihood?",
            },
            {
                "name": "reversibility",
                "question": "Which next action is useful, low-cost, and reversible while uncertainty remains?",
            },
        ]
        return self._done({
            "question": query,
            "methods": methods,
            "reasoning_chain": [
                "Separate observations from assumptions.",
                "Generate a competing explanation before choosing an action.",
                "Identify evidence that could falsify each explanation.",
                "Prefer a reversible information-gathering action while uncertainty is high.",
            ],
            "evidence_count": evidence_count,
            "confidence_ceiling": quality.get("quality_score", 0),
            "uncertainty": "Search coverage is not proof of truth or proof of absence.",
            "stop_conditions": [
                "Do not make factual or feasibility claims without primary-source evidence.",
                "Stop automated recommendation when evidence conflicts or risk requires human authority.",
            ],
        })


class AdversarialCriticAgent(BaseAgent):
    def __init__(self):
        super().__init__("adversarial_critic")

    async def execute_async(self, input_data: dict[str, Any], org_id: str) -> dict[str, Any]:
        del org_id
        reasoning = input_data.get("prev_task_9", {})
        quality = input_data.get("prev_task_7", {})
        extracted = input_data.get("prev_task_2", {})
        sanctions = input_data.get("prev_task_13", {})
        counterparties = input_data.get("prev_task_14", {})
        evidence_count = reasoning.get("evidence_count", 0)
        categories = set(quality.get("covered_categories", []))
        challenges = [
            "Which primary government, procurement, regulator, or company source independently supports the key claim?",
            "Could search ranking, language, source access, or recency have hidden contradictory evidence?",
            "What would change the conclusion, and has that disconfirming evidence been searched for?",
        ]
        if evidence_count == 0:
            challenges.insert(0, "No retrieved evidence is available; what basis would justify any substantive conclusion?")
        if len(categories) < 3:
            challenges.append("Research channels are incomplete; do not treat missing coverage as confirming evidence.")
        risks = extracted.get("risk_terms", [])
        if risks:
            challenges.append("Do sanctions, export controls, contract, payment, or customs constraints invalidate the proposed action?")
        if sanctions.get("status") in {"potential_match", "inconclusive", "unavailable"}:
            challenges.append("Sanctions screening is unresolved or incomplete; do not interpret it as clearance.")
        if counterparties.get("status") in {"partial", "unverified", "conflicting", "unavailable"}:
            challenges.append("Counterparty identity is not fully verified by an official registry source.")
        return self._done({
            "contrary_hypotheses": [
                "The apparent opportunity may be outdated, already awarded, or not open to this type of participant.",
                "Available sources may describe interest or announcements rather than an executable project.",
            ],
            "challenge_questions": challenges,
            "known_blind_spots": sorted({"web", "news", "academic"} - categories),
            "absence_of_evidence_warning": "No search result does not establish that a project, risk, or counterexample does not exist.",
            "requires_human_review": (
                bool(risks)
                or evidence_count == 0
                or quality.get("review_required", True)
                or sanctions.get("status") in {"potential_match", "inconclusive", "unavailable"}
                or counterparties.get("status") in {"partial", "unverified", "conflicting", "unavailable"}
            ),
        })


class DecisionJudgeAgent(BaseAgent):
    def __init__(self):
        super().__init__("decision_judge")

    async def execute_async(self, input_data: dict[str, Any], org_id: str) -> dict[str, Any]:
        del org_id
        risk = input_data.get("prev_task_8", {})
        reasoning = input_data.get("prev_task_9", {})
        critic = input_data.get("prev_task_10", {})
        quality = input_data.get("prev_task_7", {})
        score = float(quality.get("quality_score", 0) or 0)
        if risk.get("needs_human_approval"):
            decision = "blocked_pending_human_approval"
        elif critic.get("requires_human_review") or score < 0.6:
            decision = "research_more_before_deciding"
        else:
            decision = "prepare_internal_draft_for_review"

        tasks = []
        if score < 0.6:
            tasks.append({
                "action": "Collect primary government, procurement, and regulator evidence",
                "owner_role": "research_analyst",
                "acceptance_criteria": "At least one dated primary source per material claim, with URL and publication date",
                "priority": "high",
            })
        if critic.get("known_blind_spots"):
            tasks.append({
                "action": "Search missing evidence channels and test the strongest contrary hypothesis",
                "owner_role": "adversarial_reviewer",
                "acceptance_criteria": "Record search coverage, counterevidence, and unresolved uncertainty",
                "priority": "high",
            })
        if risk.get("needs_human_approval") or critic.get("requires_human_review"):
            tasks.append({
                "action": "Review risk checklist and approve, reject, or request revision",
                "owner_role": "authorized_human_owner",
                "acceptance_criteria": "Decision and rationale recorded before any external commitment",
                "priority": "blocking",
            })
        if not tasks:
            tasks.append({
                "action": "Prepare a reversible internal options brief; make no external commitment",
                "owner_role": "project_analyst",
                "acceptance_criteria": "Options, evidence links, second-order risks, and open questions are listed",
                "priority": "normal",
            })

        return self._done({
            "decision": decision,
            "confidence": score,
            "confidence_basis": "Evidence coverage score only; not a calibrated probability of truth.",
            "reasoning_methods": [method["name"] for method in reasoning.get("methods", [])],
            "action_plan": tasks,
            "stop_conditions": reasoning.get("stop_conditions", []),
            "human_approval_required": bool(risk.get("needs_human_approval") or critic.get("requires_human_review")),
            "prohibited_automatic_actions": ["external messages", "quotes", "contracts", "payments", "publishing"],
        })


class SynthesizerAgent(BaseAgent):
    def __init__(self):
        super().__init__("synthesizer")

    async def execute_async(self, input_data: dict[str, Any], org_id: str) -> dict[str, Any]:
        task_ids = (*range(1, 12), 13, 14)
        results = {f"task_{task_id}": input_data.get(f"prev_task_{task_id}", {}) for task_id in task_ids}
        return await self.synthesize(results, str(input_data.get("query") or ""))

    async def synthesize(self, results: dict[str, Any], original_query: str) -> dict[str, Any]:
        classifier = results.get("task_1", {})
        extracted = results.get("task_2", {})
        evidence = results.get("task_3", {})
        research = [results.get(f"task_{task_id}", {}) for task_id in (4, 5, 6)]
        quality = results.get("task_7", {})
        risk = results.get("task_8", {})
        reasoning = results.get("task_9", {})
        critic = results.get("task_10", {})
        decision = results.get("task_11", {})
        sanctions = results.get("task_13", {})
        counterparties = results.get("task_14", {})
        evidence_results: dict[str, list[dict[str, Any]]] = {}
        for result in research:
            for category, items in result.get("results", {}).items():
                evidence_results.setdefault(category, []).extend(items)
        return self._done(
            {
                "title": "v11 industry team orchestration result",
                "query": original_query,
                "intent": classifier.get("intent", "project_execution"),
                "countries": extracted.get("countries", []),
                "evidence_plan": evidence.get("required_sources", []),
                "search_queries": evidence.get("search_queries", []),
                "evidence_results": evidence_results,
                "evidence_quality": quality,
                "risk_gate": risk,
                "sanctions_screening": sanctions,
                "counterparty_verification": counterparties,
                "systems_reasoning": reasoning,
                "adversarial_review": critic,
                "decision": decision,
                "action_plan": decision.get("action_plan", []),
                "status": "research_complete" if quality.get("evidence_count", 0) else "research_degraded",
            }
        )


class AgentPool:
    def __init__(self):
        self.agents: dict[str, BaseAgent] = {}
        self._init_agents()

    def _init_agents(self) -> None:
        self.agents = {
            "classifier": ClassifierAgent(),
            "extractor": ExtractorAgent(),
            "evidence_planner": EvidencePlannerAgent(),
            "web_researcher": SearchResearchAgent("web"),
            "news_researcher": SearchResearchAgent("news"),
            "academic_researcher": SearchResearchAgent("academic"),
            "evidence_quality": EvidenceQualityAgent(),
            "risk_gate": RiskGateAgent(),
            "sanctions_screening": SanctionsScreeningAgent(),
            "counterparty_verification": CounterpartyVerificationAgent(),
            "systems_reasoning": SystemsReasoningAgent(),
            "adversarial_critic": AdversarialCriticAgent(),
            "decision_judge": DecisionJudgeAgent(),
            "synthesizer": SynthesizerAgent(),
        }

    def get_agent(self, agent_type: str) -> BaseAgent | None:
        return self.agents.get(agent_type)

    def get_all_agents(self) -> dict[str, BaseAgent]:
        return self.agents

    def health_check(self) -> dict[str, Any]:
        agents = {
            name: {"executions": agent.metrics["executions"], "errors": agent.metrics["errors"]}
            for name, agent in self.agents.items()
        }
        return {
            "total_agents": len(self.agents),
            "agents": agents,
            "contracts": {
                name: agent.contract
                for name, agent in self.agents.items()
                if hasattr(agent, "contract")
            },
            "status": "healthy" if all(item["errors"] == 0 for item in agents.values()) else "degraded",
            "mode": "v11_vertical_industry_team",
        }
