# Assignment coverage

## R1 — Event in

Implemented. `POST /api/briefs` accepts a normalized won-opportunity brief, writes it to `data/briefs/`, and records an `opportunity.won` OS event with timestamp, owner, brief ID, account, and source context. Three synthetic briefs are included.

Evidence: `backend/main.py`, `backend/services/events.py`, `data/briefs/`.

## R2 — Agent does the work

Implemented. Eight synthetic solution templates cover financial-services use cases across multiple regions. ChromaDB retrieves the top three candidates. Each match includes a score, structured components, reasons, evidence, and citation metadata. The selected LLM produces an editable POC plan and Delivery handoff skeleton rather than only a summary.

Evidence: `data/templates/`, `backend/services/retrieval.py`, `backend/services/llm.py`, `frontend/src/main.tsx`.

## R3 — Person decides

Implemented. The named US Solution Architect can edit the draft on screen, accept it, or reject it with a reason. Decisions create OS events and update template feedback, including the reuse rate used by ranking and displayed by the control surface.

Evidence: `backend/services/workflow.py`, `backend/services/feedback.py`, `frontend/src/main.tsx`.

## R4 — The seam watches itself

Implemented at prototype scope. Business hours are calculated from `received_at` against the two-business-day SLA and rolled to `GREEN`, `AMBER`, or `RED`. A red seam creates a trigger for the US Solution Architect with the draft, account, elapsed time, reason, and event context attached.

Prototype limitation: the check runs during brief retrieval and uses events to avoid duplicate breach triggers; it is not a continuously running production scheduler or worker.

Evidence: `backend/services/sla.py`, `backend/main.py`, `backend/services/events.py`, `frontend/src/main.tsx`.

## R5 — One control surface

Implemented. One screen contains the brief queue, brief details, seam health, retrieval evidence, editable draft, Delivery handoff, trigger/event log, and accept/reject actions.

Evidence: `frontend/src/main.tsx`, `frontend/src/styles.css`.

## R6 — Built with AI

Implemented and documented. The build log records decomposition, tools/models, the main prompt iteration, early failures, discarded approaches, and verification steps.

Evidence: `BUILD_LOG.md`.

## Stretch items not implemented

- Root-cause categories for each delay.
- A second prospect-silence seam.
- Regional SLA/variance reporting.
- A formal agent evaluation harness.
- A real external integration from the reference list.

These were cut to keep the primary event-to-retrieval-to-human-decision loop coherent within the eight-hour challenge.

## Decision I would never delegate

I would never hand the final acceptance or rejection of a customer-facing POC plan to an agent. The agent can retrieve prior work, identify similarities and gaps, draft a plan, and suggest risks, but a named Solution Architect must decide whether the proposed scope, regulatory interpretation, integrations, commitments, and delivery risks are accurate. That decision creates customer and commercial commitments, so the agent should support judgement rather than own it.
