"""
OMEGA ORIGIN - OBSERVER MOTHER BRICK
The Mother Brick - Architecturally Maximal
Three Layers: Extraction, Evaluation, Export
Ready for AXIOM ENGINE
Phone-compatible, zero external deps
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, List, Dict
import math
import itertools
import json

@dataclass
class Invariant:
    name: str
    value: Any
    kind: str
    support: float
    confidence: float
    entropy: float
    description: str = ""

    def is_strong(self) -> bool:
        return self.support >= 0.9 and self.confidence >= 0.8

    def to_dict(self):
        return {
            "name": self.name,
            "value": str(self.value)[:200],
            "kind": self.kind,
            "support": round(self.support, 4),
            "confidence": round(self.confidence, 4),
            "entropy": round(self.entropy, 4),
            "strong": self.is_strong(),
            "description": self.description
        }

@dataclass
class Relation:
    source: str
    target: str
    mapping: Dict[str, str] = field(default_factory=dict)
    strength: float = 0.0
    is_bijective: bool = False
    is_functional: bool = False
    kind: str = "functional"

    def to_dict(self):
        return {
            "source": self.source,
            "target": self.target,
            "strength": round(self.strength, 4),
            "is_functional": self.is_functional,
            "is_bijective": self.is_bijective,
            "kind": self.kind,
            "mapping_size": len(self.mapping)
        }

@dataclass
class GenerativeHypothesis:
    invariants: List[Invariant]
    relations: List[Relation]
    generative_rule: str
    mdl_cost: float
    coverage: float
    falsifiable: bool = True

    def to_dict(self):
        return {
            "generative_rule": self.generative_rule,
            "mdl_cost": round(self.mdl_cost, 4),
            "coverage": round(self.coverage, 4),
            "invariants": [i.to_dict() for i in self.invariants],
            "relations": [r.to_dict() for r in self.relations],
            "falsifiable": self.falsifiable
        }

class Scorer:
    @staticmethod
    def entropy(values: List[Any]) -> float:
        if not values:
            return 0.0
        counter = Counter([str(v) for v in values])
        total = len(values)
        ent = 0.0
        for count in counter.values():
            p = count / total
            ent -= p * math.log2(p) if p > 0 else 0
        return ent

    @staticmethod
    def normalized_entropy(values: List[Any]) -> float:
        ent = Scorer.entropy(values)
        unique = len(set(str(v) for v in values))
        if unique <= 1:
            return 0.0
        max_ent = math.log2(unique)
        return ent / max_ent if max_ent > 0 else 0.0

class ObserverMother:
    def __init__(self, data: List[Any]):
        self.data = data
        self.invariants: List[Invariant] = []
        self.relations: List[Relation] = []
        self.hypotheses: List[GenerativeHypothesis] = []

    def _extract_field_values(self) -> Dict[str, List[Any]]:
        fields = defaultdict(list)
        for sample in self.data:
            if isinstance(sample, dict):
                for k, v in sample.items():
                    fields[k].append(v)
            elif isinstance(sample, (list, tuple)):
                for idx, v in enumerate(sample):
                    fields[f"pos_{idx}"].append(v)
            else:
                fields["value"].append(sample)
        return fields

    def _extract_constants(self):
        fields = self._extract_field_values()
        for field_name, values in fields.items():
            if not values:
                continue
            counter = Counter([str(v) for v in values])
            most_common_val, most_common_count = counter.most_common(1)[0]
            original_val = next((v for v in values if str(v) == most_common_val), most_common_val)
            support = most_common_count / len(values)
            ent = Scorer.entropy(values)
            norm_ent = Scorer.normalized_entropy(values)
            confidence = 1.0 - norm_ent
            if len(counter) == 1:
                self.invariants.append(Invariant(
                    name=field_name,
                    value=original_val,
                    kind="constant",
                    support=1.0,
                    confidence=1.0,
                    entropy=0.0,
                    description=f"{field_name} is always {original_val}"
                ))
            elif support >= 0.8:
                self.invariants.append(Invariant(
                    name=field_name,
                    value=original_val,
                    kind="near_constant",
                    support=support,
                    confidence=confidence,
                    entropy=ent,
                    description=f"{field_name} is {original_val} in {support*100:.1f}%"
                ))
            elif len(counter) <= 3 and norm_ent < 0.6:
                self.invariants.append(Invariant(
                    name=field_name,
                    value=list(counter.keys()),
                    kind="distributional",
                    support=1.0,
                    confidence=confidence,
                    entropy=ent,
                    description=f"{field_name} limited to {list(counter.keys())}"
                ))

    def _extract_structural(self):
        if not self.data:
            return
        if isinstance(self.data[0], dict):
            key_sets = [frozenset(d.keys()) for d in self.data if isinstance(d, dict)]
            if key_sets:
                common_keys = set.intersection(*[set(k) for k in key_sets])
