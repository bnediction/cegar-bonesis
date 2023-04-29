import sys
import mpbn

f = mpbn.MPBooleanNetwork(sys.argv[1])
with open(sys.argv[2], "w") as fp:
    fp.write(f.source())
