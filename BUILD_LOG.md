# Build log

## Decomposition

The build was decomposed into one vertical Brief-to-POC loop:

1. Define typed brief, template, draft, event, feedback, SLA, and trigger models.
2. Create three synthetic won-opportunity briefs and eight reusable financial-services templates across multiple regions.
3. Persist briefs and OS events in JSON and calculate the two-business-day pickup SLA.
4. Initialize ChromaDB, ingest the template library, retrieve the top three candidates, and attach scoring reasons, evidence, and citations.
5. Add Gemini and LM Studio adapters that produce an editable POC plan and Delivery handoff.
6. Add a LangGraph human-review checkpoint so the US Solution Architect accepts, edits, or rejects the draft.
7. Feed decisions back into template ranking and reuse-rate measurement.
8. Create a named SLA trigger with the current draft and context, then expose the queue, health, retrieval, draft, trigger log, and actions on one React screen.
9. Add retrieval/workflow/SLA tests and run Python compilation plus the frontend production build.

## Tools and models

- Codex for decomposition, implementation, debugging, documentation, and verification.
- React, Vite, TypeScript, and CSS for the control surface.
- Python, FastAPI, Pydantic, and JSON-backed persistence for the API and prototype state.
- ChromaDB with local `all-MiniLM-L6-v2` embeddings for template retrieval.
- LangGraph for the human-review checkpoint and decision resume flow.
- Gemini (`gemini-3.6-flash` by default) and LM Studio (`google/gemma-3-1b` by default) as selectable providers.
- PowerShell, `rg`, `pytest`, `compileall`, and `npm run build` for inspection and verification.

## Prompt iteration

The most important instruction changed from a summary-oriented request to a strict output contract. The final prompt tells the model to analyze only the normalized brief and the three retrieved templates, explain relevance and mismatches, recommend reuse or adaptation, produce an actionable POC plan and Delivery handoff, return only schema-shaped JSON, and never invent customer facts, regulatory requirements, systems, integrations, capabilities, or templates. It also explicitly asks for risks, missing information, and open questions.

## What failed first

- A summary-only draft did not satisfy R2 because a solutions engineer needs an editable plan and handoff, not a brief recap.
- Local-model responses sometimes drifted from the JSON schema, so JSON repair and normalization were added before Pydantic validation.
- Retrieval initially needed stronger explainability, so structured score components, evidence strings, and citations were added to the match output.
- The drawer initially reopened after an outside click because a global click handler matched the drawer's own text; the opener was restricted to the actual trigger button.
- The original provider timeouts were too short for slow LLM responses; Gemini and LM Studio are now configurable with ten-minute defaults.

## What was discarded

Real CRM, call-intelligence, enrichment, notification, and knowledge-store integrations were cut in favor of synthetic adapters.  A multi-screen dashboard was reduced to one control surface. Automatic agent approval was rejected because the named Solution Architect must own judgement. Production queues, background workers, durable workflow checkpoints, and deployment automation were also left out of the one-day prototype.

## Honest prototype boundary

The system computes SLA health from event-derived brief timestamps and automatically creates a named trigger with business context when the seam is breached. In this prototype, the check runs during brief retrieval rather than through a production background scheduler.
