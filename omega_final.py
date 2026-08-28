from collections import Counter
import itertools
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

@dataclass
class Invariant:
    name: str; value: Any; support: float

@dataclass
class Axiom:
    statement: str; cost: float; strength: float

class OmegaFinal:
    def observe(self, samples):
        fields = {k for s in samples for k in s.keys()}
        fvals = {f:[s.get(f) for s in samples if f in s] for f in fields}
        invs=[]
        for fn, vals in fvals.items():
            c=Counter(vals); mv,mc=c.most_common(1)[0]
            if mc/len(vals)==1.0: invs.append(Invariant(fn,mv,1.0))
        return invs

    def learn_color_map(self, train_pairs):
        cmap={}
        for inp, out in train_pairs:
            for r in range(len(inp)):
                for c in range(len(inp[0])):
                    ic=inp[r][c]; oc=out[r][c]
                    if ic in cmap and cmap[ic]!=oc: pass
                    else: cmap[ic]=oc
        return cmap

    def predict(self, test_input, cmap):
        return [[cmap.get(cell, cell) for cell in row] for row in test_input]

def run():
    print("=== OMEGA FINAL - PREDICTOR ===")
    train = [
        ([[0,0,0],[0,1,0],[0,0,0]], [[2,2,2],[2,1,2],[2,2,2]]),
        ([[0,0,0],[0,1,0],[0,0,0]], [[2,2,2],[2,1,2],[2,2,2]]),
        ([[0,0,0],[0,1,0],[0,0,0]], [[2,2,2],[2,1,2],[2,2,2]]),
    ]
    test_in = [[0,0,0],[0,1,0],[0,0,0]]
    omega=OmegaFinal()
    cmap=omega.learn_color_map(train)
    print(f"Learned mapping: {cmap}")
    print(f"AXIOM: FORALL x: color_map({cmap})")
    pred=omega.predict(test_in, cmap)
    print(f"Input: {test_in}")
    print(f"Predicted Output: {pred}")
    print(f"Expected Output: [[2,2,2],[2,1,2],[2,2,2]]")
    print("SUCCESS!" if pred==[[2,2,2],[2,1,2],[2,2,2]] else "FAIL")

if __name__ == "__main__":
    run()