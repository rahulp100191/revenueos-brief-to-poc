# RevenueOS Brief-to-POC POC

A prototype for the Sales → US PreSales handoff. It accepts synthetic CRM-style won-opportunity events, retrieves prior solution templates with Chroma, generates an editable POC plan using Gemini or LM Studio, records human decisions, updates retrieval feedback, and creates an internal trigger when the two-business-day SLA is breached.

## Run locally

### Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item .env.example .env
uvicorn backend.main:app --reload --port 8000
```

Set `GEMINI_API_KEY` in `.env` for Gemini. Never commit `.env`. LM Studio must be running at `http://localhost:1234` with the configured model for the LM Studio option.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## VS Code Run and Debug

Install the Python and JavaScript Debugger extensions, then open **Run and Debug** and choose **RevenueOS: Full Stack**. This starts FastAPI with reload, starts Vite, and opens the frontend in Chrome. Individual configurations are available for the backend and frontend. The workspace expects the interpreter at `.venv\\Scripts\\python.exe`.

## Data

All demo data is synthetic and lives in `data/`. Templates are separate JSON files in `data/templates/`; briefs are separate JSON files in `data/briefs/`. Runtime events, feedback, drafts, and triggers are JSON-backed prototype persistence. ChromaDB is required: the backend validates and idempotently ingests all eight templates into `data/chroma/` using Chroma's local `all-MiniLM-L6-v2` embedding function. The API health endpoint reports whether the collection is ready; there is no lexical fallback.

## Provider behavior

The UI explicitly selects Gemini or LM Studio. A provider error is shown in the UI and is never silently replaced by another provider. The local Chroma retrieval and data workflow remain provider-independent.

## Retrieval scoring

Retrieval uses a hybrid score rather than semantic similarity alone:

- 35% semantic similarity from the Chroma embedding search
- 20% segment match
- 15% regulator match
- 15% customer-systems overlap
- 10% region match
- 5% recency signal
- feedback adjustment from prior accepted, edited, or rejected drafts

The final score is clamped to 0–100%. A 100% hybrid score therefore means the weighted score reached the cap; it does not mean the problem text has perfect semantic similarity. The UI also exposes semantic similarity, structured match reasons, evidence, and citations so reviewers can inspect the individual signals.

## SLA monitoring boundary

The system computes business-hour health from each brief's event-derived `received_at` timestamp and rolls the seam to green, amber, or red. A red seam creates an internal trigger for the named US Solution Architect with the account, elapsed time, reason, and current draft attached. In this prototype, the check runs during brief retrieval rather than through a continuously running production background scheduler.

Provider requests allow up to 600 seconds by default through `GEMINI_TIMEOUT_SECONDS` and `LM_STUDIO_TIMEOUT_SECONDS`; these values can be changed in `.env`.

## Production ownership view

- CRM: won-opportunity event and account records
- Call intelligence: brief content and transcript signals
- Knowledge store: reusable solution templates
- Agent runtime: retrieval context, POC drafting, and Delivery handoff drafting
- Trigger delivery: Slack, Teams, or email in production
- UI: queue, review, decision, and seam health control surface
