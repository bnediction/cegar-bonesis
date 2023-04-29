
import sys
import time

import bonesis
from bonesis.views import BooleanNetworksView
from bonesis0.asp_encoding import configurations_of_facts

bonesis.settings["quiet"] = True

def trapspace_synthesis(dom, M, mode=3, display="cli", tick=None, **opts):
    data = {"M": M}

    bo = bonesis.BoNesis(dom, data)
    if mode <= 3:
        # there exists at least one minimal trap spaces matching M
        bo.fixed(bo.obs("M"))

    class BoCegar(BooleanNetworksView):
        single_shot = False
        project = False
        ice = 0
        skip_supersets = False
        def __iter__(self):
            self.configure()
            return self

        def __next__(self):
            while True:
                with self.control.solve(yield_=True) as candidates:
                    found = False
                    for candidate in candidates:
                        found = True
                        f = self.parse_model(candidate)
                        if display == "cli":
                            print(f"~ CHECKING", file=sys.stderr)

                        ## check candidate
                        boc = bonesis.BoNesis(f, data)
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
                            if mode == 0:
                                continue
                            x = [a for a in ce.symbols(shown=True)
                                    if a.name == "cfg" and a.arguments[0].string == "__cfg0"]
                        else:
                            atoms = candidate.symbols(shown=True)
                            if display == "cli":
                                print(f"~~ valid!", file=sys.stderr)
                        break

                    if not found:
                        raise StopIteration

                if ce is None:
                    preds = {
                        ("clause", 4): "in(A2,A0,A3), maxC(A0,C), A1=1..C",
                        ("constant", 2): "node(A0), A1=(-1;1)"
                    }
                    def match_preds(a):
                        return (a.name, len(a.arguments)) in preds
                    exclude_cst = list(map(str, filter(match_preds, atoms)))
                    if not self.skip_supersets:
                        for (n, ca) in preds:
                            nbatoms = len([a for a in atoms if a.name == n and len(a.arguments) == ca])
                            p = preds[(n,ca)]
                            exclude_cst.append("{0} {{ {1}({2}) : {3} }} {0}".format(nbatoms, n,
                                ",".join(["A%d"%i for i in range(ca)]), p))
                    self.control.add("skip", [], ":- {}.".format(",".join(exclude_cst)))
                    self.control.ground([("skip", [])])
                    return f

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

    return BoCegar(bo, **opts)

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
    ap.add_argument("--maxclause", type=int, default=128,
            help="Maximum number of clauses per local function")
    ap.add_argument("--quiet", action="store_true", default=False,
                    help="Do not display BNs")
    ap.add_argument("--no-canonic", action="store_true")
    ap.add_argument("--mode", choices=[4,3,2,1,0], default=3, type=int,
                    help="counter-example version (3:TS(y)|=M; 2:y|=M, 1:TS(y)!=TS(x), 0:no generalization)")
    ap.add_argument("--display", choices=["cli", "bench"], default="cli",
                    help="Display mode")

    args = ap.parse_args()

    if args.display == "bench":
        print(args)

    dom = _load_domain(args)
    if isinstance(dom, bonesis.BooleanNetwork):
        dom = bonesis.InfluenceGraph(dom.influence_graph(), exact=True, maxclause=args.maxclause)

    if hasattr(dom, "canonic"):
        dom.canonic = not args.no_canonic
    if hasattr(dom, "maxclause") and args.maxclause:
        dom.maxclause = args.maxclause

    M = json.loads(args.marker)

    pt0 = time.process_time()
    def tick():
        return f"{time.process_time() - pt0:.2f}s"
    s = it = trapspace_synthesis(dom, M, mode=args.mode, display=args.display,
                                 tick=tick)

    if args.display == "bench":
        print("START", tick())
    f = next(iter(it), None)
    if f is not None and args.display == "cli" and not args.quiet:
        print(f)
    if args.display != "bench":
        print(s.ice)
    if f is None:
        print("UNSAT", tick())
    else:
        print("SAT", tick())
