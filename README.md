# Tackling Universal Properties of Minimal Trap Spaces of Boolean Networks

Status:
- CEGAR-based reprogramming of minimal trap spaces, using an NP and a 2QBF problem (`impl-bonesis/reprogramming_cegar.py`)
- CEGAR-based synthesis with properties of minimal trap spaces, an NP and a 2QBF problem (`impl-bonesis/synthesis.py`)

Limitations:
- Locally-monotone BNs

Requirements:
- `git submodule update --recursive --remote  --init`
- `pip install deps/bonesis`

to execute the CEGAR approach for a synthesis problem
- `https://rustup.rs`
- `pip install biodivine-aeon`

Usage:

#

- to execute the CEGAR approach for marker-reprogramming problem:
```
python impl-bonesis/reprogramming_cegar.py instances/Moon22/L3_2013_Grieco_et_al/transition_formula.bnet '{"p":1}' 3
```
The first parameter is the .bnet file, the second one is the marker (in JSON), and the third is the maximum number k of components in a perturbation. 
To fix the marker, it is also possible to use a special node (ex: p) in the bnet file and require a marker '{"p":1}'.
In the Moon22 dataset, information about uncontrollable components are available, one can use `--exclude '["Apoptosis","Growth_Arrest","Proliferation"]'`.
If the marker is given as a component, it must be involed in the uncontrollable list.

Moreover, the markers of the Moon22 dataset are contained in the bnet files in a special component `p`.
Concerning the Trappist dataset, the possible markers are contained in files .markers, the user can choose between them.

The dataset synthetic_bns contains random generated BNs. Also in this case, different possible markers are contained in files .markers.

- to execute the Complementary approach for marker-reprogramming problem:
```
python impl-bonesis/reprogramming_complementary.py  instances/Moon22/L3_2013_Grieco_et_al/transition_formula.bnet '{"p":1}' 3 
```
Again, uncontrollable components can be specified.

- to execute the Enumeration & Filtering  approach for marker-reprogramming problem:
```
python impl-bonesis/reprogramming_trapspaces_naive.py  instances/Moon22/L3_2013_Grieco_et_al/transition_formula.bnet '{"p":1}' 3 
```
Again, uncontrollable components can be specified.

#

- to execute the CEGAR approach for a synthesis problem:
```
python impl-bonesis/synthesis.py instances/Moon22/L3_2013_Grieco_et_al/transition_formula.aeon '{"p":1}'
```
The first parameter is the prior knowledge graph in an .aeon file and the second one is the marker (in JSON). 
Another option is `--maxclause` which allow one to specify the maximum integer number of clauses authorised in local functions (by default is 128).
The option `--no-canonic` leads to specify the criteria for the refinement of the under-approximation (3 for TS(y)|=M ; 1 for \exists y s.t. TS(y)!=TS(x) or 0 to obtain just a different candidate solution).
   


