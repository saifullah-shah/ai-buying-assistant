# AI Buying Decision Assistant — Project Context Pack

This folder is a starter knowledge base for building the AI Buying Decision Assistant in VS Code with OpenCode, while using ChatGPT for research and review.

## Important status

This is a planning starter pack, not a claim that implementation, data access, market selection, or commercial validation has been completed. The project is intentionally phased. Several choices remain provisional; see `docs/DECISIONS.md`.

## Suggested setup

1. Create/open the project folder in VS Code.
2. Copy these files into the repository before asking OpenCode to implement features.
3. Keep `AGENTS.md` at the repository root and commit it to Git.
4. Tell OpenCode to read `PROJECT_BRIEF.md`, `docs/PROJECT_STATE.md`, `docs/DECISIONS.md`, and the task-specific docs before making changes.
5. At the end of every significant task, ask OpenCode to update `docs/PROJECT_STATE.md`, add any accepted decisions to `docs/DECISIONS.md`, and log verified external research in `docs/RESEARCH_LOG.md`.
6. Commit small, working milestones to Git.

## Use with ChatGPT Free

Create a dedicated ChatGPT Project. Copy the contents of `CHATGPT_PROJECT_INSTRUCTIONS.md` into Project Instructions. Free projects currently allow up to five project files, so prioritize these five:

1. `docs/PROJECT_BRIEF.md` is at the repository root as `PROJECT_BRIEF.md`.
2. `docs/PRODUCT_REQUIREMENTS.md`
3. `docs/DECISIONS.md`
4. `docs/DATA_SOURCE_RESEARCH.md`
5. `docs/PROJECT_STATE.md`

If one has not been updated recently, ask ChatGPT to identify which claims are stale or need re-verification. The repository should remain the source of truth for implementation; ChatGPT project files are a research snapshot and must be refreshed when important decisions change.

## Important working principle

Do not ask either AI to “remember everything.” Store decisions, evidence, active tasks, and verified results in files. Use short, task-specific prompts. Verify code by running it and verify external claims against primary sources.
