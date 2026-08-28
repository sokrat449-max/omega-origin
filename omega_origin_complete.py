from collections import Counter
import math, json, itertools
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class Invariant:
    name: str
    value: Any
    support: float
    type: str
    confidence: float = 0.0

@dataclass
class Relation:
    source: str
    target: str
    type: str
    support: float
    mapping: Dict[Any, Any] = field(default_factory=dict)

@dataclass
class Axiom:
    statement: str
    mdl_cost: float
    strength: float
    source: str

class Scorer:
    def entropy(self, values: List[Any]) -> float:
        if not values: return 0.0
        c = Counter(values)
        total = len(values)
        return -sum((v/total) * math.log2(v/total) for v in c.values() if v>0)
    def normalized_entropy(self, values: List[Any]) -> float:
        if not values: return 0.0
        e = self.entropy(values)
        max_e = math.log2(len(set(values))) if len(set(values))>1 else 1
        return e / max_e if max_e>0 else 0.0
    def confidence(self, values: List[Any]) -> float:
        return 1.0 - self.normalized_entropy(values)

class ObserverMother:
    def __init__(self):
        self.scorer = Scorer()
    def _extract_field_values(self, samples: List[Dict]) -> Dict[str, List]:
        fields = set()
        for s in samples:
            fields.update(s.keys())
        result = {}
        for f in fields:
            result[f] = [s.get(f) for s in samples if f in s]
        return result
    def _extract_constants(self, field_values: Dict[str, List]) -> List[Invariant]:
        invs = []
        for fname, vals in field_values.items():
            if not vals: continue
            c = Counter(vals)
            most_val, most_cnt = c.most_common(1)[0]
            support = most_cnt / len(vals)
            conf = self.scorer.confidence(vals)
            if support == 1.0:
                invs.append(Invariant(fname, most_val, support, "constant", conf))
            elif support >= 0.8:
                invs.append(Invariant(fname, most_val, support, "near_constant", conf))
        return invs
    def _extract_relations(self, samples: List[Dict]) -> List[Relation]:
        if not samples: return []
        all_fields = list({k for s in samples for k in s.keys()})
        relations = []
        for src, tgt in itertools.permutations(all_fields, 2):
            mapping = {}
            is_func = True
            for s in samples:
                if src not in s or tgt not in s: continue
                sv, tv = s[src], s[tgt]
                if sv in mapping and mapping[sv]!= tv:
                    is_func = False
                    break
                mapping[sv] = tv
            if is_func and len(mapping) >= 1:
                is_bij = len(set(mapping.values())) == len(mapping) == len(set(mapping.keys())) and len(mapping) > 1
                rtype = "bijective" if is_bij else "functional"
                relations.append(Relation(src, tgt, rtype, 1.0, mapping))
        return relations
    def observe(self, samples: List[Dict]) -> Dict:
        if not samples:
            return {"invariants": [], "relations": [], "fields": []}
        fvals = self._extract_field_values(samples)
        invs = self._extract_constants(fvals)
        rels = self._extract_relations(samples)
        return {"invariants": invs, "relations": rels, "fields": list(fvals.keys()), "total_samples": len(samples)}

class AxiomEngine:
    def _mdl(self, text: str) -> float:
        return len(text) * 0.5
    def generate(self, obs: Dict) -> List[Axiom]:
        axioms = []
        for inv in obs.get("invariants", []):
            if inv.confidence < 0.5 and inv.support < 1.0: continue
            stmt = f"FORALL x: {inv.name}(x) = {inv.value!r}"
            cost = self._mdl(stmt)
            axioms.append(Axiom(stmt, cost, inv.support * inv.confidence, f"Invariant:{inv.name}"))
        for rel in obs.get("relations", []):
            stmt = f"FORALL x: {rel.source}(x) -> {rel.target}(x) [{rel.type.upper()}]"
            cost = self._mdl(stmt)
            axioms.append(Axiom(stmt, cost, rel.support, f"Relation:{rel.source}->{rel.target}"))
        axioms.sort(key=lambda a: a.mdl_cost - a.strength*5)
        return axioms

def run_tests():
    mother = ObserverMother()
    engine = AxiomEngine()
    tests = [
        ("Test1 count=1", [{"count":1},{"count":1},{"count":1}]),
        ("Test2 inside=dot", [{"inside":"dot","shape":"tri"},{"inside":"dot","shape":"tri"},{"inside":"dot","shape":"tri"}]),
        ("Test3 shape->color", [{"shape":"circle","color":"red"},{"shape":"square","color":"blue"},{"shape":"circle","color":"red"}]),
        ("Test4 near_constant", [{"type":"animal"},{"type":"animal"},{"type":"animal"},{"type":"rock"}]),
    ]
    for name, data in tests:
        print(f"\n=== {name} ===")
        obs = mother.observe(data)
        axioms = engine.generate(obs)
        print(f"Invariants: {[(i.name, i.value) for i in obs['invariants']]}")
        for ax in axioms:
            print(f" AXIOM: {ax.statement}")

if __name__ == "__main__":
    print("OMEGA ORIGIN - Phase 1")
    run_tests()