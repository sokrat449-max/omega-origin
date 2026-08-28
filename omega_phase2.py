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
    def entropy(self, values):
        if not values: return 0.0
        c = Counter(values)
        total = len(values)
        return -sum((v/total)*math.log2(v/total) for v in c.values() if v>0)
    def confidence(self, values):
        if not values: return 0.0
        e = self.entropy(values)
        max_e = math.log2(len(set(values))) if len(set(values))>1 else 1
        return 1.0 - (e/max_e if max_e>0 else 0.0)

class ObserverMother:
    def __init__(self):
        self.scorer = Scorer()
    def observe(self, samples):
        if not samples:
            return {"invariants":[],"relations":[],"fields":[]}
        fields = {k for s in samples for k in s.keys()}
        fvals = {f:[s.get(f) for s in samples if f in s] for f in fields}
        invs = []
        for fname, vals in fvals.items():
            c = Counter(vals)
            most_val, most_cnt = c.most_common(1)[0]
            sup = most_cnt/len(vals)
            conf = self.scorer.confidence(vals)
            if sup==1.0:
                invs.append(Invariant(fname, most_val, sup, "constant", conf))
            elif sup>=0.8:
                invs.append(Invariant(fname, most_val, sup, "near_constant", conf))
        rels=[]
        for src,tgt in itertools.permutations(fields,2):
            mapping={}
            ok=True
            for s in samples:
                if src not in s or tgt not in s: continue
                sv,tv=s[src],s[tgt]
                if sv in mapping and mapping[sv]!=tv:
                    ok=False;break
                mapping[sv]=tv
            if ok and mapping:
                is_bij=len(set(mapping.values()))==len(mapping)==len(set(mapping.keys())) and len(mapping)>1
                rels.append(Relation(src,tgt,"bijective" if is_bij else "functional",1.0,mapping))
        return {"invariants":invs,"relations":rels,"fields":list(fields),"total":len(samples)}

class AxiomEngine:
    def generate(self, obs):
        axs=[]
        for inv in obs["invariants"]:
            stmt=f"FORALL x: {inv.name}(x) = {inv.value!r}"
            axs.append(Axiom(stmt,len(stmt)*0.5,inv.support*inv.confidence,f"Inv:{inv.name}"))
        for rel in obs["relations"]:
            stmt=f"FORALL x: {rel.source}(x) -> {rel.target}(x) [{rel.type.upper()}]"
            axs.append(Axiom(stmt,len(stmt)*0.5,rel.support,f"Rel:{rel.source}->{rel.target}"))
        axs.sort(key=lambda a: a.mdl_cost - a.strength*5)
        return axs

class OmegaTestLab:
    def test(self, sample, axioms):
        broken=[]
        for ax in axioms:
            if " = " in ax.statement and "->" not in ax.statement:
                try:
                    left=ax.statement.split("=")[0]
                    fname=left.split(":")[1].split("(")[0].strip()
                    val=eval(ax.statement.split("=")[1].strip())
                    if fname in sample and sample[fname]!=val:
                        broken.append(ax.statement)
                except: pass
        return {"holds":len(broken)==0,"broken":broken}

def run():
    mother=ObserverMother()
    engine=AxiomEngine()
    lab=OmegaTestLab()
    data=[{"inside":"dot","shape":"tri"},{"inside":"dot","shape":"tri"},{"inside":"dot","shape":"tri"}]
    obs=mother.observe(data)
    axs=engine.generate(obs)
    print("OMEGA ORIGIN PHASE 2 - RUNNING")
    print(f"Invariants: {[(i.name,i.value) for i in obs['invariants']]}")
    for a in axs: print(f" AXIOM: {a.statement}")
    print("\nValidation good:", lab.test({"inside":"dot","shape":"tri"}, axs))
    print("Validation bad:", lab.test({"inside":"square"}, axs))

if __name__=="__main__":
    run(
 )
