from argparse import ArgumentParser
from itertools import islice, combinations
import json
import sys
import time
import bonesis
from bonesis.utils import frozendict

def validate_perturbation(f, M, P):
    bo = bonesis.BoNesis(f)
    with bo.mutant(dict(P)):
        x = bo.cfg()
        bo.in_attractor(x) != bo.obs(M)
    return not bo.is_satisfiable()

def marker_reprogramming_naive(f, M, k, exclude=None):
    nodes = list(set(f) - set(exclude if exclude else []))
    elements = [(n,0) for n in nodes] + [(n,1) for n in nodes]
    candidates = [frozendict({})]

    good = set()
    for size in range(k+1):
        bad = set()
        for P in combinations(elements, size):
            P = frozenset(P)
            dom = len([p[0] for p in P])
            if dom != size:
                continue
            superset = False
            for g in good:
                if g.issubset(P):
                    superset = True
                    break
            if superset:
                continue

            if validate_perturbation(f, M, P):
                good.add(P)
                yield dict(P)
        if size == 0 and good:
            return
        if size != k:
            if size == 1:
                elements = [e for e in elements if e not in good]
                if not elements:
                    return

def main(raw_args=None):
    ap = ArgumentParser()
    ap.add_argument("input",
            help="file specifying the domain of Boolean networks (supported: .bnet, .sif, .aeon)")
    ap.add_argument("marker",
            help="Marker specification (partial configuration) - JSON format")
    ap.add_argument("max_size", type=int,
            help="Maximum number of perturbation")
    ap.add_argument("--limit", type=int,
            help="Maximum number of solutions")
    ap.add_argument("--exclude",
            help="Perturbation blacklist - JSON format")
    args = ap.parse_args(raw_args)

    pt0 = time.process_time()
    def tick():
        return f"{time.process_time() - pt0:.2f}s"

    f = bonesis.BooleanNetwork(args.input)
    M = json.loads(args.marker)
    k = args.max_size
    exclude = json.loads(args.exclude) if args.exclude else []
    exclude = list(set(exclude+list(M)))

    it = marker_reprogramming_naive(f, M, k, exclude=exclude)

    if args.limit:
        it = islice(it, args.limit)
    has_one = False
    print("START", tick())
    for solution in it:
        print("SAT", tick())
        has_one = True
    if not has_one:
        print("UNSAT", tick())

if __name__ == "__main__":
    main()
