# RevenueOS Brief-to-POC Plan — Requirements

## 1. Document purpose

This file distills the requirements from **Engineering Challenge — AI-Native IC Engineering Lead, GTM Engineering**.

### Scope distinction

- **User request:** inspect the attached assignment and create this `requirement.md` file.
- **Embedded assignment instructions:** define the system that an engineering candidate is expected to build. They are captured below as product, technical, delivery, and evaluation requirements; they do not themselves authorize additional work in this repository.

## 2. Product objective

Build a working **Brief-to-POC-Plan loop** for a B2B software company selling to banks and insurers.

The loop must demonstrate that:

1. A won-opportunity event enters the system.
2. An AI agent retrieves relevant prior solution templates and produces an editable POC plan and Delivery handoff skeleton.
3. A named human role reviews and accepts, edits, or rejects the draft.
4. The decision is recorded and influences reuse and future template ranking.
5. The handoff monitors its own SLA health and escalates breaches automatically.

The primary bottleneck is the Sales → US PreSales handoff. The pickup SLA is **two business days**, while the US actual is **6.8 days**, largely because reusable UK and India solution templates are not retrievable when a brief arrives.

## 3. Functional requirements

### R1 — Event in

- Accept a won opportunity as an OS event.
- The event must resemble a real CRM or call-intelligence payload and include:
  - timestamp
  - owner
  - account
  - brief
- The brief must cover enough context for planning: customer/account, region, segment, regulator, business problem, systems, expected timeline, and what the POC must prove.
- Include at least **three varied synthetic briefs** that exercise retrieval.
- Declare that the data is synthetic.

### R2 — Agent does the work

The agent must:

- Read and understand the brief.
- Retrieve candidate solution templates from a constructed library.
- Explain why each candidate matches the brief.
- Draft a usable POC plan that a Solutions Engineer can edit and send.
- Draft a skeleton of the Delivery handoff document.

The output must be an actionable draft, not only a summary, classification, or list of insights.

The template library must contain at least **eight templates** across at least **two regions**, using realistic financial-services use cases such as:

- KYC document review
- Loan underwriting assistance
- Claims triage
- Regulatory reporting
- Customer-service copilots
- Fraud-alert triage

Suggested template fields:

`id`, `name`, `region of origin`, `segment`, `regulator context`, `problem solved`, `capabilities used`, `integrations`, `effort in weeks`, `outcome`, `date last used`, and `owner`.

### R3 — Person decides

- The reviewer must be represented as the named role **US Solution Architect**.
- The reviewer must be able to **accept, edit, or reject** the generated draft on screen.
- Each decision must create an OS event.
- Decisions must feed back into the system:
  - measure template reuse rate
  - improve or change future template ranking based on acceptance and rejection

### R4 — Seam watches itself

- Compute brief age continuously from event timestamps.
- Compare age with the **two-business-day SLA**.
- Classify seam health automatically as:
  - green
  - amber
  - red
- On breach, automatically fire a trigger to a named owner.
- Attach the current draft and relevant context to the trigger.
- Do not require manually entered metrics or manually entered health status.
- Compute all health and trigger state from system events.

### R5 — One control surface

Provide one screen where a person can:

- view the queue of briefs
- view current seam health
- inspect the current draft
- inspect the trigger log
- take the available actions

The surface must support action, not merely display dashboard metrics. A dashboard without an actionable workflow does not meet the requirement.

### R6 — Built with AI

Show how AI was used to build the system, including:

- work decomposition
- tools and models used
- prompts or agent instructions
- the main prompt/instruction iteration
- what failed first
- what was discarded
- evidence in commit history and the build log

## 4. Suggested data shapes

The following shapes are guidance, not a fixed schema. Any changes should be justified.

### Brief

- account
- region
- segment: retail bank, insurer, capital markets, lender, etc.
- regulator: OCC, FCA, RBI, etc.
- business problem in two or three sentences
- customer systems
- expected timeline
- successful-POC proof points

### Solution template

- See the fields listed under R2.
- Templates must be searchable and span multiple regions.

### POC plan

- objective
- success criteria
- scope in and out
- templates used and required changes
- integrations required
- week-by-week plan
- risks
- people needed

## 5. Domain model and operating rules

- **Seam:** a handoff between two functions with an SLA.
- **OS event:** a timestamped, owned record of something that happened at a seam, such as brief arrival, draft acceptance, or SLA breach.
- **Brief:** the Sales-to-PreSales handoff content.
- **Solution template:** a reusable record of a prior POC, including need, capabilities, scope, effort, and outcome.
- **Template library:** searchable cross-region template collection.
- **Trigger:** automatic escalation to a named person when a seam breaches its SLA, with context attached.

RevenueOS operating rules:

1. Every handoff is an event with a timestamp and owner.
2. Health is computed against an SLA; it is not manually reported.
3. Agents do retrieval, drafting, enrichment, and routing; people own judgment, relationships, and commitments.
4. CRM, call intelligence, and enrichment tools are the source of truth; numbers must not be typed into spreadsheets.

## 6. Synthetic scenario data and benchmark context

The assignment provides this benchmark context for the US bottleneck:

| Metric | US | Company average |
|---|---:|---:|
| Open opportunities per solutions engineer | 9.4 | 6.2 |
| POC turnaround | 31 days | 19 days |
| Briefs in backlog | 14 | 4 |
| Handoff documents complete at signing | 82% | 94% |
| Reuse of prior solutions | 21% | UK 58%, India 55% |

Use the given roles, SLA, and numbers where relevant instead of inventing replacement values.

## 7. Integration expectations

No real integrations or accounts are required. Synthetic data is expected. Credit is earned by:

- making event payloads faithful to the type of production tool that would emit them
- stating which tool would own each part of the production loop

Possible production ownership:

- CRM: won-opportunity event and account/deal records
- Call intelligence: brief content from transcripts and deal signals
- Enrichment: firmographics, contacts, and technology stack
- Knowledge/documents: template library
- Workflow: event routing and orchestration
- Agent runtime: retrieval, drafting, and function calls
- Retrieval store: vector or graph search over templates
- Trigger delivery: Slack, Microsoft Teams, or email
- UI: the fastest suitable implementation

Plausible tools named in the assignment include HubSpot, Attio, Salesforce, Pipedrive, Gong, Fireflies.ai, Otter.ai, Apollo.io, Clay, Notion, Google Drive, Confluence, n8n, Zapier, Make, Temporal, LangGraph, OpenAI Agents SDK, Anthropic Agent SDK, CrewAI, Pydantic AI, Vercel AI SDK, pgvector, Chroma, Qdrant, Weaviate, and Neo4j. Tool choices are optional and must be justified.

## 8. Optional stretch scope

No penalty for omission. Possible additions:

- root-cause categories for delays
- a second seam for prospects going silent after a demo, with a two-day Sales → Marketing SLA
- variance by region
- an agent evaluation harness
- one real integration from the integration reference

## 9. Constraints and implementation rules

- Any stack, language, model, or framework is acceptable.
- Justify the stack choice in one paragraph.
- Hosted or local execution is acceptable if it runs during the demo.
- Declare all synthetic data.
- If a product capability must be named but is unavailable, invent a plausible capability and label it as invented.
- Time-box implementation to **one working day / eight hours**.
- A focused, complete loop is preferred over broad but incomplete functionality.

## 10. Required submission deliverables

The assignment expects five deliverables:

1. Running system, live or a recording of **eight minutes or less**.
2. Repository with commit history intact.
3. One-page build log covering AI-assisted decomposition, tools, the most-iterated prompt or agent instruction, first failure, and discarded work.
4. Half-page cut list covering what was left out, why, and what breaks first at 10× volume.
5. One paragraph describing the decision in this loop that should never be handed to an agent, and why.

## 11. Demo and evaluation acceptance criteria

The panel may:

- run the system
- submit a brief the system has not seen
- break something and ask what happens next
- inspect the repository

Evaluation weights:

| Criterion | Weight | Acceptance signal |
|---|---:|---|
| Built with AI at speed | 35% | AI wrote most code, candidate directed it, method visible in commits/build log |
| Agent does the work | 30% | Draft is usable; accept/edit/reject changes future behavior |
| Reasons over knowledge | 20% | Structured library, explainable retrieval, measured reuse |
| Seam watches itself | 15% | Health computed from events; trigger reaches named owner with context |

Cross-cutting expectations:

- use the provided roles, SLA, and numbers
- make honest, specific cuts
- declare synthetic data without being prompted

## 12. Explicit non-requirements / non-scoring approaches

The following do not satisfy the assignment on their own:

- dashboard metrics typed in manually
- an agent that only summarizes, classifies, or surfaces insights
- breadth across many shallow screens
- a build approach that does not demonstrate meaningful AI-assisted engineering

## 13. Recommended end-to-end acceptance test

Given a new synthetic won-opportunity event:

1. The event appears in the brief queue with timestamp, owner, account, and brief.
2. The brief is assigned an automatically computed green/amber/red health state against the two-business-day SLA.
3. The agent retrieves multiple templates, displays match reasons, and produces an editable POC plan plus Delivery handoff skeleton.
4. The US Solution Architect edits, accepts, or rejects the draft.
5. The decision is persisted as an OS event and affects reuse/ranking behavior.
6. Advancing the event beyond the SLA automatically changes health and creates a trigger for a named owner with the draft attached.
7. All of the above is possible from the single control surface without manually entering metrics.

