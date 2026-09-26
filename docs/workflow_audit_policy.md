# Workflow Audit Policy

This document defines the final production-safe operating model for GitHub Actions in this repository.

## Policy Summary

- Production-safe workflows are allowed to run without making the GitHub Actions page appear as a hard failure.
- Advisory-only workflows are treated as audit checkpoints and human-review gates.
- Human approval is required before any release, publishing, payment decision, contract commitment, or public-facing action.

## Classification

### 1. Production-safe mode

These workflows are designed to run as operational checks and report results without turning the pipeline red when the outcome is advisory or non-blocking.

- `.github/workflows/watchdog.yml`
  - Status: advisory-only
  - Purpose: monitor freshness, repository health, and decision backlog
  - Human review: recommended when metrics are stale or abnormal

- `.github/workflows/cloud_acceptance.yml`
  - Status: advisory-only
  - Purpose: aggregate preflight, daily job, watchdog, and acceptance evidence
  - Human review: required before release or public deployment

- `.github/workflows/codex_autonomous_repair.yml`
  - Status: audit-first safety gate
  - Purpose: automatic low-risk code repair and evidence capture
  - Human review: required when the report is `tests_failed`, `health_check_only`, `manual_review_required`, or `repair_rejected`

### 2. Advisory-only workflows

These workflows are designed to record evidence, summarize state, and provide actionable signals for a human owner without being a hard release gate.

- `.github/workflows/international_trade_ops.yml`
  - Purpose: preflight, operations cycle, summaries, and operating state capture
  - Human review: recommended before operational commitment or external communication

- `.github/workflows/owner_decision.yml`
  - Purpose: resolve owner decisions and persist decision evidence
  - Human review: required before any externally visible or materially significant action

### 3. Human-review required before release or decision execution

These jobs must not be treated as automatically actionable. They are only valid if a human reviews the evidence before release, publishing, or outbound execution.

- `Codex Autonomous Repair`
  - Requires human review when repair status is not `repaired` or `healthy`

- `GitHub Cloud Acceptance`
  - Requires human review before any release package or external action

- `Owner Decision Handler`
  - Requires human validation before any major external commitment or implementation step

- `International Trade AI Ops`
  - Requires human review before operational commitments, external announcements, or release actions

## Operational Rule

If a workflow result is any of the following, the GitHub Actions run must be treated as an evidence record for human review, not as an automatic green-light:

- `tests_failed`
- `health_check_only`
- `manual_review_required`
- `repair_rejected`
- `PASS_WITH_WARNINGS`
- missing artifacts or report files

## Acceptance Standard

A workflow is considered compliant when all of the following are true:

- It produces an audit artifact or summary
- It does not create a misleading hard red-screen failure for advisory-only checks
- It uses explicit human-review language in logs and summaries
- It preserves evidence in GitHub Actions artifacts and repository state

## Final Production Guidance

- Do not treat advisory workflows as automatic sign-off.
- Do not publish, promise delivery, or make financial/legal commitments without human approval.
- Use the artifact and report files as the basis for action, not as an automatic release gate.
