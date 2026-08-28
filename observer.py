"""
OMEGA ORIGIN - OBSERVER MOTHER BRICK
The Mother Brick - Architecturally Maximal
Three Layers: Extraction, Evaluation, Export
Ready for AXIOM ENGINE

Phone-compatible, zero external deps
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, List, Dict, Tuple
import math
import itertools
import json


# ========== CORE OBJECTS ==========

@dataclass
class Invariant:
    name: str
    value: Any
    kind: str  # constant, distributional, structural, relational
    support: float  # 0.0 - 1.0
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
    kind: str = "functional"  # functional, correlation, causal_hint

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


# ========== SCORING ENGINE ==========

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

    @staticmethod
    def support(values: List[Any], dominant_value: Any) -> float:
        if not values:
            return 0.0
        count = sum(1 for v in values if str(v) == str(dominant_value))
        return count / len(values)


# ========== MOTHER BRICK ==========

class ObserverMother:
    """
    Three layers:
    1. Extraction: what exists
    2. Evaluation: how strong, how real
    3. Export: ready for AXIOM ENGINE
    """

    def __init__(self, data: List[Any]):
        self.data = data
        self.invariants: List[Invariant] = []
        self.relations: List[Relation] = []
        self.hypotheses: List[GenerativeHypothesis] = []

    # ---- Layer 1: EXTRACTION ----

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
            # Find original value
            original_val = next((v for v in values if str(v) == most_common_val), most_common_val)
            
            support = most_common_count / len(values)
            ent = Scorer.entropy(values)
            norm_ent = Scorer.normalized_entropy(values)
            confidence = 1.0 - norm_ent

            # Constant detection
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
            # Near-constant (strong invariant with noise)
            elif support >= 0.8:
                self.invariants.append(Invariant(
                    name=field_name,
                    value=original_val,
                    kind="near_constant",
                    support=support,
                    confidence=confidence,
                    entropy=ent,
                    description=f"{field_name} is {original_val} in {support*100:.1f}% cases"
                ))
            # Distributional invariant (e.g., always small set)
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
        # Detect structural invariants: same length, same keys, same shape
        if not self.data:
            return
        
        # Key set invariant
        if isinstance(self.data[0], dict):
            key_sets = [frozenset(d.keys()) for d in self.data if isinstance(d, dict)]
            if key_sets:
                common_keys = set.intersection(*[set(k) for k in key_sets]) if key_sets else set()
                if common_keys:
                    self.invariants.append(Invariant(
                        name="structure_keys",
                        value=list(common_keys),
                        kind="structural",
                        support=len(key_sets)/len(self.data),
                        confidence=1.0,
                        entropy=0.0,
                        description=f"All samples share keys {list(common_keys)}"
                    ))

        # Length invariant
        lengths = [len(d) if hasattr(d, '__len__') else 0 for d in self.data]
        if lengths and len(set(lengths)) == 1:
            self.invariants.append(Invariant(
                name="structure_length",
                value=lengths[0],
                kind="structural",
                support=1.0,
                confidence=1.0,
                entropy=0.0,
                description=f"All samples have length {lengths[0]}"
            ))

    def _extract_relations(self):
        fields = self._extract_field_values()
        field_names = list(fields.keys())
        if len(field_names) < 2:
            return

        for src, tgt in itertools.permutations(field_names, 2):
            src_vals = fields[src]
            tgt_vals = fields[tgt]
            if len(src_vals) != len(tgt_vals):
                continue

            # Build mapping
            mapping = {}
            conflict = False
            for s, t in zip(src_vals, tgt_vals):
                s_key = str(s)
                t_key = str(t)
                if s_key in mapping and mapping[s_key] != t_key:
                    conflict = True
                    break
                mapping[s_key] = t_key

            if not conflict and len(mapping) > 1:
                # Functional dependency
                strength = len(mapping) / len(set(str(v) for v in src_vals)) if src_vals else 0
                # Check bijective
                reverse_vals = list(mapping.values())
                is_bijective = len(reverse_vals) == len(set(reverse_vals))
                
                # Strength based on entropy reduction
                src_ent = Scorer.entropy(src_vals)
                # Conditional entropy approximation
                conditional_ent = 0.0  # perfect mapping = 0
                strength_score = 1.0 - (conditional_ent / (src_ent + 1e-9)) if src_ent > 0 else 1.0

                self.relations.append(Relation(
                    source=src,
                    target=tgt,
                    mapping=mapping,
                    strength=strength_score,
                    is_bijective=is_bijective,
                    is_functional=True,
                    kind="functional" if is_bijective else "functional_many_to_one"
                ))

    # ---- Layer 2: EVALUATION ----

    def _evaluate(self):
        # Score MDL cost for each invariant
        for inv in self.invariants:
            # MDL: cost = bits to describe invariant + bits to describe exceptions
            # Simple approximation: lower entropy + higher support = lower cost
            base_cost = math.log2(len(str(inv.value)) + 1)
            exception_cost = (1 - inv.support) * len(self.data) * 2
            inv.confidence = max(0.0, min(1.0, inv.confidence))

        # Sort invariants by strength
        self.invariants.sort(key=lambda x: (x.support, x.confidence), reverse=True)
        self.relations.sort(key=lambda x: x.strength, reverse=True)

    def _build_hypotheses(self):
        if not self.invariants:
            return

        strong_invs = [i for i in self.invariants if i.is_strong()]
        if not strong_invs:
            strong_invs = self.invariants[:2]

        # Build generative rule text
        if strong_invs:
            rule_parts = [f"{inv.name}={inv.value}" for inv in strong_invs]
            generative_rule = " AND ".join(rule_parts) + " => structure holds"
        else:
            generative_rule = "No strong invariant found - search deeper"

        # MDL cost
        mdl_cost = sum([len(str(i.value)) for i in strong_invs]) + len(self.relations) * 5
        coverage = sum([i.support for i in strong_invs]) / len(strong_invs) if strong_invs else 0.0

        self.hypotheses.append(GenerativeHypothesis(
            invariants=strong_invs,
            relations=self.relations[:3],
            generative_rule=generative_rule,
            mdl_cost=mdl_cost,
            coverage=coverage,
            falsifiable=True
        ))

    # ---- Layer 3: EXPORT ----

    def observe(self) -> Dict[str, Any]:
        """Main entry - runs all three layers"""
        self.invariants.clear()
        self.relations.clear()
        self.hypotheses.clear()

        # Layer 1
        self._extract_constants()
        self._extract_structural()
        self._extract_relations()
        
        # Layer 2
        self._evaluate()
        
        # Layer 3
        self._build_hypotheses()

        return self.export()

    def export(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total_samples": len(self.data),
                "invariants_found": len(self.invariants),
                "strong_invariants": len([i for i in self.invariants if i.is_strong()]),
                "relations_found": len(self.relations)
            },
            "invariants": [i.to_dict() for i in self.invariants],
            "relations": [r.to_dict() for r in self.relations],
            "hypotheses": [h.to_dict() for h in self.hypotheses]
        }

    def export_for_axiom_engine(self) -> str:
        """Exports as JSON ready for next phase"""
        return json.dumps(self.export(), ensure_ascii=False, indent=2)

    def what_repeats(self):
        return [(inv.name, inv.value, inv.support) for inv in self.invariants]

    def what_changes(self):
        fields = self._extract_field_values()
        changes = {}
        for k, vals in fields.items():
            changes[k] = {
                "unique": len(set(str(v) for v in vals)),
                "entropy": round(Scorer.entropy(vals), 3),
                "is_invariant": len(set(str(v) for v in vals)) == 1
            }
        return changes


# ========== SELF TEST ==========

if __name__ == "__main__":
    print("=== TEST 1: Bongard-like ===")
    bongard_data = [
        {"shape": "circle", "count": 1, "inside": "dot", "color": "black"},
        {"shape": "circle", "count": 1, "inside": "dot", "color": "black"},
        {"shape": "square", "count": 1, "inside": "dot", "color": "black"},
        {"shape": "triangle", "count": 1, "inside": "dot", "color": "black"},
    ]
    mother = ObserverMother(bongard_data)
    report = mother.observe()
    print(json.dumps(report, ensure_ascii=False, indent=2))

    print("\n=== TEST 2: Physical law ===")
    physics_data = [
        {"mass": 10, "gravity": 9.8, "weight": 98},
        {"mass": 20, "gravity": 9.8, "weight": 196},
        {"mass": 5, "gravity": 9.8, "weight": 49},
    ]
    mother2 = ObserverMother(physics_data)
    print(mother2.export_for_axiom_engine())
