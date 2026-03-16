# WAT: Weekly AI & Technology Newsletter

## Overview
An automated weekly newsletter pipeline that researches AI & Technology Trends, summarises findings, creates a Gamma presentation, and delivers a formatted HTML email every Monday.

## Pattern: Prompt Chaining
Each step's output is the next step's input. Failure at any step exits the pipeline with a non-zero code (n8n treats this as an execution error).

## Trigger
- **n8n Schedule**: Every Monday at 08:00 local time
- **Entry point**: `python main.py`
- **Manual run**: `python main.py` from the project root

---

## Steps

### Step 1 — Web Research
**Tool**: `src/tools/web_search.py`
**Function**: `run_web_search(topic: str) -> list[dict]`

| | Detail |
|---|---|
| Input | `topic = "AI & Technology Trends"` |
| API | Tavily (`TAVILY_API_KEY`) |
| Sub-queries | 5 varied queries covering research, product launches, LLMs, regulation, funding |
| Settings | `search_depth="advanced"`, `topic="news"`, `max_results=5` per query |
| Output | Deduplicated list of `{title, url, content, score}` dicts, sorted by score |
| Error | Log and raise on empty results or API failure |

### Step 2 — Summarise
**Tool**: `src/tools/summarise.py`
**Function**: `run_summarise(search_results: list[dict], topic: str, week_label: str) -> dict`

| | Detail |
|---|---|
| Input | Raw search results from Step 1 |
| API | Anthropic (`ANTHROPIC_API_KEY`), model: `claude-3-5-sonnet-20241022` |
| Output fields | `newsletter_intro`, `top_trends` (max 5), `key_insights` (3–4), `notable_developments` (list of `{title, summary, url}`), `slide_outline` (markdown with `---` separators) |
| Error | Retry once on API error; raise on second failure |

### Step 3 — Create Presentation
**Tool**: `src/tools/create_presentation.py`
**Function**: `run_create_presentation(summary: dict, week_label: str) -> str`

| | Detail |
|---|---|
| Input | `summary["slide_outline"]` + structured content from Step 2 |
| API | Gamma (`GAMMA_API_KEY`) — `https://public-api.gamma.app/v1.0` |
| Phase 1 | POST `/generations` → returns `generationId` |
| Phase 2 | Poll GET `/generations/{id}` every 10s, max 12 attempts (2 min) |
| Output | `gammaUrl` string |
| Error | `TimeoutError` on poll timeout; `RuntimeError` on `status: failed` |

### Step 4 — Send Email
**Tool**: `src/tools/send_email.py`
**Function**: `run_send_email(summary: dict, gamma_url: str, week_label: str) -> None`

| | Detail |
|---|---|
| Input | Summary dict from Step 2 + `gammaUrl` from Step 3 |
| Protocol | Gmail SMTP, STARTTLS, port 587 |
| Auth | `GMAIL_SENDER` + `GMAIL_APP_PASSWORD` |
| Recipients | `NEWSLETTER_RECIPIENTS` (comma-separated env var) |
| Subject | `"AI & Tech Trends — Week of {date}"` |
| Body | HTML email: intro, top trends, key insights, notable developments, CTA button → Gamma URL |
| Error | Log SMTP errors with full traceback and raise |

---

## Environment Variables

| Variable | Description |
|---|---|
| `TAVILY_API_KEY` | Tavily API key (app.tavily.com) |
| `ANTHROPIC_API_KEY` | Anthropic API key (console.anthropic.com) |
| `GAMMA_API_KEY` | Gamma API key (gamma.app > Settings > API Key, Pro required) |
| `GMAIL_SENDER` | Gmail address to send from |
| `GMAIL_APP_PASSWORD` | Gmail App Password (requires 2FA, 16-char) |
| `NEWSLETTER_RECIPIENTS` | Comma-separated recipient email addresses |

---

## Error Handling Strategy
- Each tool raises on unrecoverable errors
- `main.py` catches all exceptions, logs them, and exits with code 1
- n8n marks the execution as failed and can notify via its built-in error workflow
- No state is persisted — each Monday run is fully independent

## Future Enhancements
- Log run metadata (status, gamma_url, timestamp) to Supabase for a run history dashboard
- Add a routing step to vary topic based on a weekly schedule
- Support multiple recipients lists (different audience segments)
