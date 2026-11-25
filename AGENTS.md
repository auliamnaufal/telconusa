# AGENTS.md

Rules for coding agents working in this repository. Humans should read `CONTEXT.md` first; this file is the short operational version.

## Project

TelcoNusa ERP: four tracks (CRM, HRM, SCM, Finance), each owned by a separate team, integrated by REST APIs and signed webhook events. Shared context is in `CONTEXT.md`. Per-track scope, integration status, acceptance criteria and backlog are in `tracks/<track>.md`. Machine-readable contracts are in `contracts/`.

## First steps in any task

1. Find out which track you are working for. If the task does not say, ask. Do not guess.
2. Read `CONTEXT.md`, then `tracks/<track>.md` (its `folders` list is the only code you may change), then the contract files your change touches (`contracts/openapi/<track>.yaml`, `contracts/events/*.schema.json`, `contracts/variable_standards.md`).

## Boundaries

- Edit only the folders listed in your track file. Never edit another track's folders.
- Shared areas need a separate PR approved by all four tracks: `services/shared/`, `contracts/`, `docker-compose.yml`, `.env.example`, `mysql/init/`, `CONTEXT.md`, `AGENTS.md`, `.github/`, `tools/`. Do not change them as a side effect of track work.
- Change a contract before changing code that depends on it. Do not call or publish anything that is not in `contracts/`.
- A status is changed only by the module that owns it. Use `services/shared/transitions.py`.
- Only the Finance track writes the general ledger.
- Never put secrets in the repo. Never add default values for `JWT_SECRET` or `HMAC_WEBHOOK_SECRET`.

## Commands

```bash
tools/setup-env.sh                       # create .env with generated secrets
tools/install-hooks.sh                   # install the commit-msg hook
docker compose up -d --build <svc>...    # run your own services only
docker compose --profile mock up -d      # mock the tracks you are not running
python tools/check_contracts.py          # validate contracts and track files, regenerate tracks/STATUS.md
pytest -q tests                          # shared helper and tooling tests
pytest -q services/<track>-api/tests     # your service tests, if present
```

Point a service at a mock with `<TRACK>_API_URL_INTERNAL=http://mock-<track>:4010`; see `mock/README.md`. Push a sample event with `python tools/send_fixture.py <event.type> --to <base-url>`.

## Working rules

- Follow the conventions in `contracts/variable_standards.md`: snake_case, integer rupiah, ISO 8601 `+07:00`, business codes from sequences (`shared/ids.py`), `X-Correlation-Id` forwarded on every call.
- Publish events through the outbox (`shared/outbox.py`) in the same transaction as the data change. Receive events through `shared/event_receiver.py`, which rejects unsigned events and ignores duplicates.
- Cross-module HTTP calls carry a service token (`shared/service_auth.py`) and every endpoint states `x-auth`, `x-roles` or `x-scope` in the OpenAPI file.
- When you finish something that changes what other tracks can rely on, update `tracks/<track>.md` (status, `since`, `test`, Requests, Decisions) and run `python tools/check_contracts.py`. `LIVE` requires a passing test.
- Keep changes small and in the track's own style. Do not add abstractions, fallbacks that hide failures (`except: pass`), or features that are not in the track's acceptance criteria.

## Git rules: no coding-agent attribution

No coding agent (Claude, Codex, Copilot, Cursor, Gemini, or any other) may ever be the author, co-author or contributor of a git commit, PR, or any other git record.

- Do not add `Co-Authored-By`, `Generated-by`, `Assisted-by`, `Signed-off-by` or similar trailers naming an agent.
- Do not write "generated with", "created with" or similar lines, or robot emoji signatures, in commit messages, PR titles or PR bodies.
- Do not set the git author or committer to an agent identity. Commits are made under the human contributor's own git identity.
- Describe the change itself; do not mention the tooling that produced it.

CI (`tools/check_agent_attribution.py`) and the `commit-msg` hook reject violations. Fix the commit; do not bypass the check.
