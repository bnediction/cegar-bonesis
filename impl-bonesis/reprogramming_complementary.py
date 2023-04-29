import sys
import json
from argparse import ArgumentParser
from itertools import islice, combinations

import bonesis
from bonesis.reprogramming import *
import time

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
    #print(exclude)
    it = marker_reprogramming(f, M, k,
        exclude=exclude)

    if args.limit:
        it = islice(it, args.limit)
    has_one = False


    print("START", tick())
    for solution in it:
        print("SAT", tick())
        #print(solution)
        has_one = True
    if not has_one:
        print("UNSAT", tick())


if __name__ == "__main__":
    main()

