# Build log

## Decomposition

1. Create synthetic JSON fixtures and typed domain models.
2. Implement event and JSON persistence.
3. Implement business-hour SLA calculation.
4. Load templates into Chroma with local embeddings.
5. Add Gemini and LM Studio provider adapters.
6. Add LangGraph-compatible workflow services and human decision endpoints.
7. Build one React control surface.
8. Add tests and demo documentation.

## Tools and models

- React, Vite, TypeScript, Tailwind CSS
- Python, FastAPI, Pydantic, LangGraph
- ChromaDB with `all-MiniLM-L6-v2` local embeddings
- Gemini `gemini-flash-latest` or LM Studio `google/gemma-3-1b`

## Prompt iteration

The main agent instruction was tightened from “summarize the brief” to “return only schema-valid JSON containing an actionable POC plan, Delivery handoff, explicit assumptions, risks, and open questions; do not invent customer facts.” This prevents the non-scoring summary-only behavior.

## Known tradeoffs

JSON persistence and synchronous API workflow keep the demo small but are not production persistence or job orchestration. Trigger delivery is an internal log rather than an external notification.

