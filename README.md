# Global Intelligence v11 Backend

This directory is the v11 cloud brain. It replaces the earlier `international-trade-ai` working name and is now the backend authority for GitHub Actions, Codespaces-style automation, approval gates, reports, memory, and desktop integration.

## Command Model

- GitHub = 你的云端 AI 总部
- Codex = 24h 自主执行官
- 你 = 只在“重大事项”出现时做决定

## Local Run

```powershell
cd "C:\Users\Surface\Documents\New project\global-intelligence-v11"
python backend\workflows\ensure_labels.py
python backend\workflows\preflight_check.py
python backend\workflows\daily_job.py
python backend\workflows\watchdog.py
python backend\workflows\cloud_acceptance.py
python backend\workflows\prepare_release.py
```

When GitHub Actions runs from `backend`, the same commands are:

```powershell
python workflows/ensure_labels.py
python workflows\prepare_release.py
```

API development:

```powershell
cd "C:\Users\Surface\Documents\New project\global-intelligence-v11"
python backend\api\main.py
```

## Cloud Automation

GitHub Actions use these backend workflows:

- `.github/workflows/cloud_acceptance.yml`
- `.github/workflows/watchdog.yml`
- `.github/workflows/codex_autonomous_repair.yml`
- `.github/workflows/international_trade_ops.yml`
- `.github/workflows/owner_decision.yml`

## Operating Policy

The repository follows an audit-first, non-red-screen operating model.

- Audit first: every workflow writes evidence and summaries before any escalation.
- Non-red-screen failure: advisory and health-check workflows should not masquerade as hard failures; they report warnings and audit notes instead.
- Human approval is the final decision gate: no release, commitment, payment, external execution, or publication proceeds without owner approval.
- Any publishing, pricing, contract, payment, or public-facing action requires explicit human confirmation.

This policy is enforced as a safety rule for all GitHub Actions automation.

Codex/AI may automatically diagnose and repair low-risk framework, code, test, and configuration problems. It must not send external replies, publish content, quote prices, sign contracts, make payment decisions, or promise delivery without human approval.

## Required Evidence

Runtime evidence is written under:

- `backend/reports/`
- `reports/headquarters_status.md`
- `reports/owner_inbox.md`
- `backend/memory/`
- `memory/execution_logs`
- `backend/comm/outbox/`
- `docs/github-deployment-runbook.md`
- GitHub Cloud Acceptance

`backend/memory/audit.log` is append-only evidence. Do not delete, rewrite, or compress historical lines.

## Release Package

```powershell
python backend\workflows\prepare_release.py
```

Output:

- `backend/dist/global-intelligence-v11.zip`
- `backend/dist/release_manifest.json`
