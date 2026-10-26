# BB(6) holdout: 1RB0RE_1LC0LB_1RD0LB_1RF0LA_1RC---_0RA0LD

Attempted non-halting proof of the BB(6) holdout machine
`1RB0RE_1LC0LB_1RD0LB_1RF0LA_1RC---_0RA0LD`.

## Approach

Inductive proof over canonical configurations parametrised by (N, M[, k]):

- **lemma A**: (N+P, M) -> (N, M+dM) for each node (even/odd M, plus small concrete M),
- **lemma B**: one per (node, r = N in [r_low, r_low+P), parity of M), proved with the
  symbolic simulator `ssim3` (affine expressions in up to three variables),
- families (`3^k` blocks) with symbolic k, and partial nodes covered by family lemmas.

Everything is stored in `proof2.json`, produced by `prover2.py` (+ `lemmaA_odd.py`, `smallM.py`).

## Status

- prover2 BFS closed: 925 nodes (180 partial), 19 162 lemma-B records
- `python verify3.py 500` -> 385 reachable nodes, 30 628 states, **0 errors**,
  start descends into the induction domain at (N, M) = (24, 5533)
- `xcheckA.py`: 810 ssim3-vs-fsim bit-exact cross-checks, 0 mismatches
- TODO: `chaincheck.py` (concrete check of the first induction steps from the start)

## Layout

- `*.c`, `*.cpp`, `*.inc` - simulators (`fsim` concrete, `ssim3` symbolic, ...), build to `*.exe`
- `*.py` - provers, verifiers and exploration scripts
- simulator traces (`pv_*`, `p*_*`, `tmp_*`, ...) are git-ignored; they are regenerable
