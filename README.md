# BB(6) holdout: 1RB0RE_1LC0LB_1RD0LB_1RF0LA_1RC---_0RA0LD

Computer-assisted non-halting proof of the BB(6) holdout machine
`1RB0RE_1LC0LB_1RD0LB_1RF0LA_1RC---_0RA0LD`.

## The argument

Configurations at *canonical points* are written as `zone | w^N | T | u^M | tail` and grouped into
nodes (fixed zone/T/u/tail; families with `T = 0 4 3^k 2` and symbolic k). The proof (`proof4.json`) consists of

- **lemma A** per node: (N + P, M[, k]) -> (N, M + dM[, k]), symbolic in N, M (and k), for even and odd M,
  plus small-N lemmas (concrete N, symbolic M) and small-M lemmas (concrete M, symbolic N);
- **lemma B** per (node, r, parity of M): from the last canonical point (N = r) to the first canonical
  point of the next node, with N1, M1, K1 affine in M (and k);
- the **domain**: for every reachable node, N = r in [r_low, r_low + P), M >= 500, family k >= K_fam.

Non-halting follows from:

1. **start**: after 226 258 281 steps from the blank tape the machine is in the start node with
   N = 224, M = 2045 (`start_check.c`, a plain TM simulator), and lemma A takes it into the domain at (24, 5533);
2. **closure**: every domain state reaches a domain state again in a positive number of steps
   (`verify4.py`, see below);
3. **lemmas**: every lemma is a symbolic simulation by `ssim4` under recorded linear constraints.

## Checks

| check | what | result |
|---|---|---|
| `start_check.c` | plain TM simulation from the blank tape to the start configuration | identical to `s_226258280.txt` |
| `verify4.py` | closure over **all** M, k (affine classes, residue splits, peeled prefixes; monotonicity) | 385 nodes, 30 628 domain classes, 1 301 290 classes, **0 errors** |
| `verify4_mutations.py` | 9 injected defects in the proof data | 9/9 reported |
| `rerun4.py` | every lemma (32 018) re-derived with `ssim4` from the original inputs | all byte-identical; 1 constraint tightened by 1 |
| `BB6_PROOF=proof4.json verify4.py` | closure with the `ssim4` constraints | **0 errors** |
| `endpoint4.py` | every used lemma (30 191) evaluated by `ssim4` at the most extreme points the proof uses it at | 30 756 points, **0 mismatches** |
| `chaincheck2.py` | real trajectory from the start + 3000 random full cycles, run concretely with `fsim` | all as predicted |
| `xcheckA.py` | 810 lemma-A / small-N instances, `ssim3` vs `fsim` bit-exact | 0 mismatches |

`verify3.py` (the earlier checker) only checked each domain state at the smallest M; `verify4.py` replaces it.
`chaincheck.py` built ever larger concrete configurations (M grows ~9x per cycle: 3 GB input by cycle 5)
and most likely crashed the machine; `chaincheck2.py` replaces it with bounded checks.

## Trust base

The proof is complete **assuming the symbolic simulator `ssim4` is correct** (`ssim4.cpp` + `accel4.inc`:
backsymbol macro machine with block size 20, chain steps over runs, cycle acceleration; every
assumption about symbolic counts is recorded as a constraint). `ssim4` is `ssim3` plus two assumptions
that `ssim3` made silently:

- initial symbolic runs have count >= 1 (lemmas are used below the fitted instances, down to x = -250);
- in the cycle accelerator, a constant repetition limit chosen over a symbolic one requires the symbolic one to be >= it.

Independent evidence for the simulators: concrete `fsim` cross-checks of every lemma B (one instance each),
810 lemma-A instances, 3000 full random cycles and the real trajectory. A formal (e.g. Coq) verification
of the symbolic simulator is not done.

## Reproduce

```
gcc -O2 -o start_check.exe start_check.c && ./start_check.exe 226258281 sc.txt   # compare with s_226258280.txt
g++ -O2 -o ssim4.exe ssim4.cpp
python verify4.py 500
BB6_PROOF=proof4.json python verify4.py 500
```

`rerun4.py`, `endpoint4.py`, `chaincheck2.py` and `xcheckA.py` need the lemma input files and simulator
traces (`p2_*`, ~20 GB, git-ignored, regenerable with `prover2.py`).

## Layout

- `*.c`, `*.cpp`, `*.inc` - simulators (`fsim` concrete, `ssim3`/`ssim4` symbolic, ...), build to `*.exe`
- `prover2.py` (+ `lemmaA_odd.py`, `smallM.py`) - the prover that produced `proof2.json`
- `proof2.json` (ssim3 constraints), `proof4.json` (ssim4 constraints)
- `verify4.py`, `endpoint4.py`, `chaincheck2.py`, `rerun4.py`, `build_proof4.py` - the checks above
- other `*.py` - exploration scripts from the search for the proof structure
