import hashlib
import json
import os
import re
from datetime import date
from pathlib import Path

from ..models import Brief, Match, Template
from .feedback import feedback

try:
    import chromadb
    from chromadb.utils import embedding_functions
except Exception as exc:  # pragma: no cover - exercised through health status
    chromadb = None
    embedding_functions = None
    CHROMA_IMPORT_ERROR = str(exc)
else:
    CHROMA_IMPORT_ERROR = None


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


class RetrievalService:
    def __init__(self):
        self.templates: list[Template] = []
        self._collection = None
        self.ready = False
        self.error: str | None = None
        self.collection_name = os.getenv("CHROMA_COLLECTION", "solution_templates_v1")
        self.persist_directory = Path(os.getenv("CHROMA_PERSIST_DIRECTORY", "data/chroma"))
        if not self.persist_directory.is_absolute():
            self.persist_directory = Path(__file__).resolve().parents[2] / self.persist_directory

    def initialize(self) -> None:
        """Validate source templates and idempotently ingest all records into Chroma."""
        try:
            if chromadb is None or embedding_functions is None:
                raise RuntimeError(f"ChromaDB import failed: {CHROMA_IMPORT_ERROR or 'unknown error'}")
            self.templates = self._load_templates()
            if len(self.templates) != 8:
                raise RuntimeError(f"Expected exactly 8 templates, found {len(self.templates)}")
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(self.persist_directory))
            if os.getenv("CHROMA_REBUILD_ON_STARTUP", "false").lower() == "true":
                try:
                    client.delete_collection(self.collection_name)
                except Exception:
                    pass
            embedder = embedding_functions.DefaultEmbeddingFunction()
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine", "schema_version": "1"},
                embedding_function=embedder,
            )
            ids = [template.id for template in self.templates]
            documents = [self._document(template) for template in self.templates]
            metadatas = [self._metadata(template) for template in self.templates]
            self._collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            existing = set(self._collection.get(include=[]) .get("ids", []))
            stale = sorted(existing - set(ids))
            if stale:
                self._collection.delete(ids=stale)
            self.ready = True
            self.error = None
            print(f"Chroma retrieval ready: collection={self.collection_name}, templates={len(ids)}, stale_removed={len(stale)}")
        except Exception as exc:
            self.ready = False
            self._collection = None
            self.error = str(exc)
            print(f"Chroma retrieval unavailable: {self.error}")

    def status(self) -> dict:
        return {
            "provider": "chroma",
            "collection": self.collection_name,
            "template_count": len(self.templates),
            "ready": self.ready,
            **({"error": self.error} if self.error else {}),
        }

    def _load_templates(self) -> list[Template]:
        template_dir = Path(__file__).resolve().parents[2] / "data" / "templates"
        paths = sorted(template_dir.glob("*.json"))
        return [Template(**json.loads(path.read_text(encoding="utf-8"))) for path in paths]

    def _document(self, template: Template) -> str:
        return "\n".join([
            template.name,
            f"Region: {template.region}.",
            f"Segment: {template.segment}.",
            f"Regulators: {', '.join(template.regulators)}.",
            f"Problem solved: {template.problem_solved}",
            f"Capabilities: {', '.join(template.capabilities)}.",
            f"Integrations: {', '.join(template.integrations)}.",
            f"Outcome: {template.outcome}",
        ])

    def _metadata(self, template: Template) -> dict:
        source_file = next((p.name for p in (Path(__file__).resolve().parents[2] / "data" / "templates").glob("*.json") if json.loads(p.read_text(encoding="utf-8")).get("id") == template.id), template.id)
        content_hash = hashlib.sha256(self._document(template).encode("utf-8")).hexdigest()
        return {
            "template_id": template.id,
            "name": template.name,
            "region": template.region,
            "segment": template.segment,
            "regulators_json": json.dumps(template.regulators),
            "capabilities_json": json.dumps(template.capabilities),
            "integrations_json": json.dumps(template.integrations),
            "effort_weeks": template.effort_weeks,
            "outcome": template.outcome,
            "last_used": template.last_used,
            "owner": template.owner,
            "document_path": template.document_path,
            "source_file": source_file,
            "schema_version": "1",
            "content_hash": content_hash,
        }

    def _brief_query(self, brief: Brief) -> str:
        return "\n".join([
            f"Problem: {brief.problem}",
            f"Region: {brief.region}",
            f"Segment: {brief.segment}",
            f"Regulator: {brief.regulator}",
            f"Systems: {', '.join(brief.systems)}",
            f"Success criteria: {', '.join(brief.success_criteria)}",
        ])

    def search(self, brief: Brief) -> list[Match]:
        if not self.ready or self._collection is None:
            raise RuntimeError(self.error or "Chroma retrieval is not initialized")
        feedback_rows = {r["template_id"]: r for r in feedback()}
        by_id = {template.id: template for template in self.templates}
        result = self._collection.query(
            query_texts=[self._brief_query(brief)],
            n_results=len(self.templates),
            include=["distances", "metadatas"],
        )
        vector_scores = {
            template_id: max(0.0, min(1.0, 1.0 - float(distance)))
            for template_id, distance in zip(result["ids"][0], result["distances"][0])
        }
        query_tokens = _tokens(self._brief_query(brief))
        matches: list[Match] = []
        for template in self.templates:
            row = feedback_rows.get(template.id, {"accepted_count": 0, "edited_count": 0, "rejected_count": 0})
            capability_tokens = _tokens(" ".join(template.capabilities + [template.problem_solved] + template.integrations))
            segment_match = 1.0 if template.segment == brief.segment else 0.0
            regulator_match = 1.0 if brief.regulator in template.regulators else 0.0
            systems_match = 1.0 if query_tokens & _tokens(" ".join(template.integrations)) else 0.0
            region_match = 1.0 if template.region == brief.region else 0.4
            recency_score = 0.8
            feedback_adjustment = min(0.25, row["accepted_count"] * .08 + row["edited_count"] * .03 - row["rejected_count"] * .12)
            vector_similarity = vector_scores.get(template.id, 0.0)
            score = max(0.0, min(1.0, .35 * vector_similarity + .20 * segment_match + .15 * regulator_match + .15 * systems_match + .10 * region_match + .05 * recency_score + feedback_adjustment))
            reasons = [f"{int(score * 100)}% hybrid match score", f"{template.region} template; region relevance {int(region_match * 100)}%", f"semantic similarity: {vector_similarity:.3f}"]
            if segment_match: reasons.append(f"segment matches: {brief.segment}")
            if regulator_match: reasons.append(f"regulator matches: {brief.regulator}")
            if systems_match: reasons.append("customer systems overlap with template integrations")
            if query_tokens & capability_tokens: reasons.append("problem/capability terms overlap")
            if feedback_adjustment: reasons.append(f"feedback adjustment: {feedback_adjustment:+.2f}")
            reasons.append(f"Evidence: {template.name}; {template.problem_solved}; capabilities: {', '.join(template.capabilities)}; integrations: {', '.join(template.integrations)}")
            reasons.append(f"Citation: {template.document_path}")
            matches.append(Match(template=by_id[template.id], score=round(score, 3), reasons=reasons, vector_similarity=round(vector_similarity, 3), structured_components={"segment_match": segment_match, "regulator_match": regulator_match, "systems_match": systems_match, "region_match": region_match, "recency_score": recency_score, "feedback_adjustment": round(feedback_adjustment, 3)}, citation={"document_path": template.document_path, "source_file": self._metadata(template)["source_file"]}))
        return sorted(matches, key=lambda match: match.score, reverse=True)[:3]
