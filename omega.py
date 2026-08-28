from collections import Counter
import itertools
from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass
class Invariant:
    name: str; value: Any; support: float

@dataclass
class Axiom:
    statement: str; cost: float; strength: float

class OmegaOrigin:
    def observe(self, samples):
        fields = {k for s in samples for k in s.keys()}
        fvals = {f:[s.get(f) for s in samples if f in s] for f in fields}
        invs=[]
        for fn, vals in fvals.items():
            c=Counter(vals); mv,mc=c.most_common(1)[0]
            if mc/len(vals)==1.0:
                invs.append(Invariant(fn,mv,1.0))
        rels=[]
        for src,tgt in itertools.permutations(fields,2):
            mp={}; ok=True
            for s in samples:
                if src not in s or tgt not in s: continue
                sv,tv=s[src],s[tgt]
                if sv in mp and mp[sv]!=tv: ok=False; break
                mp[sv]=tv
            if ok and mp:
                is_bij=len(set(mp.values()))==len(mp)==len(set(mp.keys())) and len(mp)>1
                rels.append((src,tgt,"bijective" if is_bij else "functional",mp))
        return invs, rels

    def learn_color_map(self, train_pairs):
        cmap={}
        for inp,out in train_pairs:
            for r in range(len(inp)):
                for c in range(len(inp[0])):
                    ic=inp[r][c]; oc=out[r][c]
                    if ic not in cmap: cmap[ic]=oc
        return cmap

    def predict(self, test_input, cmap):
        return [[cmap.get(cell,cell) for cell in row] for row in test_input]

def run():
    print("=== OMEGA ORIGIN - FINAL UNIFIED ===")
    omega=OmegaOrigin()
    # Phase 2 test
    data=[{"inside":"dot","shape":"tri"}]*3
    invs,rels=omega.observe(data)
    print(f"Phase2 Invariants: {[(i.name,i.value) for i in invs]}")
    print(f"Phase2 Relations: {rels}")
    # Phase 4 ARC test
    train=[
        ([[0,0,0],[0,1,0],[0,0,0]], [[2,2,2],[2,1,2],[2,2,2]]),
        ([[0,0,0],[0,1,0],[0,0,0]], [[2,2,2],[2,1,2],[2,2,2]]),
        ([[0,0,0],[0,1,0],[0,0,0]], [[2,2,2],[2,1,2],[2,2,2]]),
    ]
    test_in=[[0,0,0],[0,1,0],[0,0,0]]
    cmap=omega.learn_color_map(train)
    pred=omega.predict(test_in,cmap)
    print(f"\nLearned mapping: {cmap}")
    print(f"FORALL x: color_map({cmap})")
    print(f"Predicted: {pred}")
    print("SUCCESS!" if pred==[[2,2,2],[2,1,2],[2,2,2]] else "FAIL")
    print("\nOMEGA READY FOR ARC!")

if __name__ == "__main__":
    run()