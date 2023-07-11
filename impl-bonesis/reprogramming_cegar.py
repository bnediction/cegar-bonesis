
import bonesis
from bonesis.views import SomeView
from bonesis0.asp_encoding import configurations_of_facts

import time


bonesis.settings["quiet"] = True

def trapspace_reprogramming(dom, M, k,exclude, mode=3, display="cli", tick=None):
    data = {"M": M}

    bo = bonesis.BoNesis(dom, data)
    P = bo.Some(max_size=k, exclude=list(M)+exclude)
    with bo.mutant(P):
        if mode <= 3:
            # there exists at least one minimal trap spaces matching M
            bo.fixed(bo.obs("M"))

    class BoCegar(SomeView):
        single_shot = False
        project = False
        ice = 0
        def __iter__(self):
            self.configure()
            return self

        def __next__(self):
            while True:
                with self.control.solve(yield_=True) as candidates:
                    found_P = False
                    for candidate in candidates:
                        found_P = True
                        P = self.parse_model(candidate)
                        if display == "cli":
                            print(f"~ CHECKING {P}", file=sys.stderr)

                        ## check candidate
                        boc = bonesis.BoNesis(dom, data)
                        with boc.mutant(P):
                            x = boc.cfg()
                            boc.in_attractor(x)
                            x != boc.obs("M")
                        view = x.assignments(limit=1)
                        view.configure()
                        if (ce := next(iter(view.control.solve(yield_=True)), None)) is not None:
                            self.ice += 1
                            if display == "bench":
                                print("CE", tick())
                            else:
                                x = view.format_model(ce)
                                print(f"~~ COUNTER EXAMPLE: {x}", file=sys.stderr)
                            x = [a for a in ce.symbols(shown=True)
                                    if a.name == "cfg" and a.arguments[0].string == "__cfg0"]
                        else:
                            p = candidate.symbols(shown=True)
                            if display == "cli":
                                print(f"~~ valid!", file=sys.stderr)
                        break

                    if not found_P:
                        raise StopIteration

                if ce is None:
                    inject = f":- {','.join(map(str, p))}."
                    self.control.add("skip", [], inject)
                    self.control.ground([("skip", [])])
                    return P
                ns = f"_ce{self.ice}_"
                cets = f"{ns}ts"
                fixts = f"{ns}fix"
                inject = [f"mcfg({cets},{a.arguments[1]},{a.arguments[2]})." for a in x]
                inject += [
                        # compute trap space of counter example
                        f"mcfg({cets},N,V) :- {ns}eval({cets},N,V).",
                        f"clamped({cets},N,V) :- mutant(_,N,V).",
                        # choose sub-space in it
                        f"1 {{mcfg({fixts},N,V):mcfg({cets},N,V)}} :- mcfg({cets},N,_).",
                        # saturate it
                        f"mcfg({fixts},N,V) :- {ns}eval({fixts},N,V).",
                        f"clamped({fixts},N,V) :- clamped({cets},N,V).",

                        f"{ns}eval(X,N,C,-1) :- clause(N,C,L,-V), mcfg(X,L,V), not clamped(X,N,_).",
                        f"{ns}eval(X,N,C,1) :- mcfg(X,L,V): clause(N,C,L,V); clause(N,C,_,_), mcfg(X,_,_), not clamped(X,N,_).",
                        f"{ns}eval(X,N,1) :- {ns}eval(X,N,C,1), clause(N,C,_,_).",
                        f"{ns}eval(X,N,-1) :- {ns}eval(X,N,C,-1): clause(N,C,_,_); clause(N,_,_,_), mcfg(X,_,_).",
                        f"{ns}eval(X,N,V) :- clamped(X,N,V).",
                        f"{ns}eval(X,N,V) :- constant(N,V), mcfg(X,_,_), not clamped(X,N,_).",

                        f"{ns}eval(X,N,V) :- {ns}evalbdd(X,N,V), node(N), not clamped(X,N,_).",
                        f"{ns}evalbdd(X,V,V) :- mcfg(X,_,_), V=(-1;1).",
                        f"{ns}evalbdd(X,B,V) :- bdd(B,N,_,HI), mcfg(X,N,1), {ns}evalbdd(X,HI,V).",
                        f"{ns}evalbdd(X,B,V) :- bdd(B,N,LO,_), mcfg(X,N,-1), {ns}evalbdd(X,LO,V).",
                        f"{ns}evalbdd(X,B,V) :- mcfg(X,_,_), bdd(B,V).",
                    ]
                if mode >= 3:
                    # TS(y) must match with M
                    inject.append(f":- obs(\"M\",N,V), mcfg({fixts},N,-V).")
                elif mode >= 1:
                    # TS(y) must be different than TS(x)
                    inject.append(f"diff({fixts}) :- mcfg({cets},N,V), not mcfg({fixts},N,V). :- not diff({fixts}).")
                if mode == 2:
                    # y must match with M
                    inject.append(f"mcfg({fixts},N,V) :- obs(\"M\",N,V).")

                inject = "\n".join(inject)
                self.control.add(f"cegar{ns}", [], inject)
                self.control.ground([(f"cegar{ns}", [])])

#    return BoCegar(P, bo)
    return BoCegar(P, bo, solutions="subset-minimal")

if __name__ == "__main__":
    import sys
    from argparse import ArgumentParser
    import json
    from bonesis.cli import _setup_argument_domain, _load_domain
    from itertools import islice
    ap = ArgumentParser()
    _setup_argument_domain(ap)
    ap.add_argument("marker",
            help="Marker specification (partial configuration) - JSON format")
    ap.add_argument("max_size", type=int,
            help="Maximum number of perturbation")
    ap.add_argument("--limit", type=int,
            help="Maximum number of solutions")
    ap.add_argument("--exclude",
                    help="Perturbation blacklist - JSON format")
    ap.add_argument("--mode", choices=[3,2,1,4], default=3, type=int,
                    help="counter-example version (3:TS(y)|=M; 2:y|=M, 1:TS(y)!=TS(x), 4:3-existence)")
    ap.add_argument("--display", choices=["cli", "bench"], default="cli",
                    help="Display mode")
    args = ap.parse_args()

    if args.display == "bench":
        print(args)

    dom = _load_domain(args)
    M = json.loads(args.marker)
    k = args.max_size


    exclude = json.loads(args.exclude) if args.exclude else []

    pt0 = time.process_time()
    def tick():
        return f"{time.process_time() - pt0:.2f}s"

    s = it = trapspace_reprogramming(dom, M, k, exclude, mode=args.mode,
                                     display=args.display, tick=tick)

    if args.display == "bench":
        print("START", tick())
    if args.limit:
        it = islice(it, args.limit)
    has_it = False
    for i, P in enumerate(it):
        has_it = True
        if args.display == "bench":
            print("SAT", tick())
        else:
            print(P)
    if not has_it:
        if args.display == "bench":
            print("UNSAT", tick())
        else:
            print("No solution", file=sys.stderr)
    if args.display != "bench":
        print(s.ice)
