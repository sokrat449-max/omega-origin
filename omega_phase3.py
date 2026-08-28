from collections import Counter
import math, itertools
from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class Invariant:
    name: str; value: Any; support: float; type: str

@dataclass
class Relation:
    source: str; target: str; type: str; support: float; mapping: Dict = field(default_factory=dict)

@dataclass
class Axiom:
    statement: str; cost: float; strength: float

class ObserverMother:
    def observe(self, samples):
        if not samples: return {"invariants":[],"relations":[]}
        fields = {k for s in samples for k in s.keys()}
        fvals = {f:[s.get(f) for s in samples if f in s] for f in fields}
        invs = []
        for fn, vals in fvals.items():
            c = Counter(vals); mv, mc = c.most_common(1)[0]; sup = mc/len(vals)
            if sup == 1.0: invs.append(Invariant(fn, mv, sup, "constant"))
        rels = []
        for src,tgt in itertools.permutations(fields,2):
            mp={}; ok=True
            for s in samples:
                if src not in s or tgt not in s: continue
                sv,tv=s[src],s[tgt]
                if sv in mp and mp[sv]!=tv: ok=False; break
                mp[sv]=tv
            if ok and mp:
                is_bij = len(set(mp.values()))==len(mp)==len(set(mp.keys())) and len(mp)>1
                rels.append(Relation(src,tgt,"bijective" if is_bij else "functional",1.0,mp))
        return {"invariants":invs,"relations":rels}

class AxiomEngine:
    def generate(self, obs):
        axs=[]
        for inv in obs["invariants"]:
            st=f"FORALL x: {inv.name}(x) = {inv.value!r}"
            axs.append(Axiom(st, len(st)*0.3, inv.support))
        for rel in obs["relations"]:
            st=f"FORALL x: {rel.source}(x) -> {rel.target}(x) [{rel.type}]"
            axs.append(Axiom(st, len(st)*0.5, rel.support))
        axs.sort(key=lambda a: a.cost - a.strength*10)
        return axs

class OmegaTestLab:
    def test(self, sample, axioms):
        bad=[]
        for ax in axioms:
            if " = " in ax.statement and "->" not in ax.statement:
                try:
                    left=ax.statement.split("=")[0]
                    fn=left.split(":")[1].split("(")[0].strip()
                    val=eval(ax.statement.split("=")[1].strip())
                    if fn in sample and sample[fn]!=val: bad.append(ax.statement)
                except: pass
        return {"holds": len(bad)==0, "broken": bad}

class ARCGridSolver:
    def solve(self, train_pairs):
        # train_pairs = [(input_grid, output_grid)]
        # هنستخرج قانون بسيط: لون الخلفية ثابت، شكل داخلي ثابت
        samples=[]
        for inp, out in train_pairs:
            flat_in = [c for row in inp for c in row]
            flat_out = [c for row in out for c in row]
            samples.append({"in_colors": tuple(sorted(set(flat_in))), "out_colors": tuple(sorted(set(flat_out))), "size": len(inp)})
        mother=ObserverMother()
        obs=mother.observe(samples)
        eng=AxiomEngine()
        axs=eng.generate(obs)
        return obs, axs

def run():
    print("=== OMEGA PHASE 3 - ARC SOLVER ===")
    mother=ObserverMother(); eng=AxiomEngine(); lab=OmegaTestLab()
    # Test 1: قانونك الأصلي
    data=[{"inside":"dot","shape":"tri"}]*3
    obs=mother.observe(data); axs=eng.generate(obs)
    print(f"Invariants: {[(i.name,i.value) for i in obs['invariants']]}")
    for a in axs: print(f" AXIOM: {a.statement}")
    print("Test good:", lab.test({"inside":"dot"}, axs))
    print("Test bad:", lab.test({"inside":"square"}, axs))
    # Test 2: ARC-like
    print("\n--- ARC Demo ---")
    train = [ ([[0,0,0],[0,1,0],[0,0,0]], [[2,2,2],[2,1,2],[2,2,2]] ) ]*3
    solver=ARCGridSolver()
    obs2, axs2 = solver.solve(train)
    print(f"ARC Invariants: {[(i.name,i.value) for i in obs2['invariants']]}")
    for a in axs2[:3]: print(f" ARC AXIOM: {a.statement}")

if __name__ == "__main__":
 run()
