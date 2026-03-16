# Workflow Context

## Project Overview
- **Tech Stack**: Python, SQL, Bash, n8n, VAPI, Supabase, Lovable, Git
- **Framework**: WAT Framework (Workflows, Agents, Tools)

## Key Commands
- **Install**: `pip install -r requirements.txt`
- **Run**: `python main.py`
- **Test**: `pytest tests/ -v`
- **Format**: `ruff format src/`
- **Check**: `ruff check src/` and `mypy src/ --strict`

## WAT Framework Guidelines
- **Workflows (W)**: High-level markdown files (e.g., `WAT.md`) defining the SOP. Use predefined orchestration patterns — prompt chaining, routing, parallelisation, orchestrator-workers, evaluator-optimiser. Start here before reaching for agents.
- **Agents (A)**: Claude Code acts as the coordinator to interpret workflows. Agents decide next steps based on environmental feedback. 
- **Tools (T)**: Modular Python scripts that perform specific actions (API calls, data transforms, scoring). Available connections: Supabase (state management, async webhooks, potential MCP connection), n8n (orchestration), VAPI (voice calls), Git CLI. Document MCP servers in `.mcp.json` as they are added.

## Coding Standards
- **Naming**: `snake_case` for Python and SQL. No abbreviations except domain terms (EV, ART, CPL, UTM, GBM, COMPACT).
- **Modularity**: Keep tools small and single-purpose so they can be reused across workflows. Consolidate frequently chained operations only where it reduces round-trips without sacrificing clarity.
- **Error Handling**: Always include try-except blocks and detailed logging in tool scripts. Deterministic code for precision work (calculations, data joins); LLM for reasoning and planning only.
- **Types**: Type hints on all Python functions, docstrings on public interfaces.
- **SQL**: CTEs over subqueries, explicit column lists (no `SELECT *`), lowercase keywords.
- **Commits**: Conventional commits (`feat:`, `fix:`, `refactor:`, `docs:`), reference context in body.
- **Secrets**: No credentials in code — use environment variables.

## Claude Skills
Before creating files, always read the relevant SKILL.md first:
- **Word docs**: `/mnt/skills/public/docx/SKILL.md`
- **PDFs**: `/mnt/skills/public/pdf/SKILL.md`
- **Presentations**: `/mnt/skills/public/pptx/SKILL.md`
- **Spreadsheets**: `/mnt/skills/public/xlsx/SKILL.md`
- **Web UIs**: `/mnt/skills/public/frontend-design/SKILL.md`
- **Custom skills**: `/mnt/skills/examples/skill-creator/SKILL.md`

## Before Modifying Code
1. **Investigate** — Read relevant files, check git history
2. **Plan** — Outline changes, list files affected
3. **Implement** — Incremental changes, commit logical units
4. **Validate** — Run tests and linting
5. **Document** — Update docs if behaviour changes
