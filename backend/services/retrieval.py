import re
from pathlib import Path
from ..models import Brief, Match, Template
from .json_store import read_templates
from .feedback import feedback

try:
    import chromadb
    from chromadb.utils import embedding_functions
except Exception:
    chromadb = None
    embedding_functions = None

def _tokens(text: str) -> set[str]: return set(re.findall(r"[a-z0-9]+", text.lower()))

class RetrievalService:
    def __init__(self):
        self.templates = [Template(**x) for x in read_templates()]
        self._collection = None
        self._initialized = False

    def _ensure_collection(self):
        if self._initialized or not (chromadb and embedding_functions):
            return
        self._initialized = True
        try:
            root = Path(__file__).resolve().parents[2] / "data" / "chroma"
            client = chromadb.PersistentClient(path=str(root))
            ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
            self._collection = client.get_or_create_collection("solution_templates", embedding_function=ef)
            self._collection.upsert(ids=[t.id for t in self.templates], documents=[self._doc(t) for t in self.templates], metadatas=[{"region":t.region,"segment":t.segment} for t in self.templates])
        except Exception:
            self._collection = None

    def _doc(self, t: Template) -> str:
        return " ".join([t.name, t.region, t.segment, " ".join(t.regulators), t.problem_solved, " ".join(t.capabilities), " ".join(t.integrations)])

    def search(self, brief: Brief) -> list[Match]:
        self._ensure_collection()
        rows = {r["template_id"]: r for r in feedback()}
        query = " ".join([brief.problem, brief.segment, brief.regulator, brief.region, " ".join(brief.systems)])
        vector_scores = {}
        if self._collection:
            result = self._collection.query(query_texts=[query], n_results=len(self.templates), include=["distances"])
            for tid, distance in zip(result["ids"][0], result["distances"][0]): vector_scores[tid] = max(0.0, min(1.0, 1 - float(distance)))
        q = _tokens(query)
        matches = []
        for t in self.templates:
            r = rows.get(t.id, {"accepted_count":0,"edited_count":0,"rejected_count":0})
            cap = _tokens(" ".join(t.capabilities + [t.problem_solved] + t.integrations))
            overlap = len(q & cap) / max(1, len(q | cap))
            segment = 1.0 if t.segment == brief.segment else 0.0
            regulator = 1.0 if brief.regulator in t.regulators else 0.0
            systems = 1.0 if q & _tokens(" ".join(t.integrations)) else 0.0
            region = 1.0 if t.region == brief.region else 0.4
            feedback_adjustment = min(0.25, r["accepted_count"]*.08 + r["edited_count"]*.03 - r["rejected_count"]*.12)
            score = max(0.0, min(1.0, .35*vector_scores.get(t.id, overlap) + .20*segment + .15*regulator + .15*systems + .10*region + .05*.8 + feedback_adjustment))
            reasons = [f"{int(score*100)}% match score", f"{t.region} template; region relevance {int(region*100)}%"]
            if segment: reasons.append(f"segment matches: {brief.segment}")
            if regulator: reasons.append(f"regulator matches: {brief.regulator}")
            if systems: reasons.append("customer systems overlap with template integrations")
            if q & cap: reasons.append("problem/capability terms overlap")
            if feedback_adjustment: reasons.append(f"feedback adjustment: {feedback_adjustment:+.2f}")
            matches.append(Match(template=t, score=round(score, 3), reasons=reasons))
        return sorted(matches, key=lambda x: x.score, reverse=True)[:3]
