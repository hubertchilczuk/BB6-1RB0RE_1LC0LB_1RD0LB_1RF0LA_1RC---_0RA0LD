# Why 1RB0RE_1LC0LB_1RD0LB_1RF0LA_1RC---_0RA0LD does not halt

Status: computer proof, checked as described in [README.md](README.md); not yet formalized in Rocq
(see [PLAN.md](PLAN.md)). The machine is on the BB(6) holdout list of 2026-10-24 (623 machines, line 124).
busycoq (`verify/Eqv_Misc.v`, module `TM44`, BB6 branch) proves it equivalent to
`1LB0LA_1RC0LA_1RF0LD_1RA0RE_1RB---_0RD0LC`, so the proof settles both.

```
     0    1
A   1RB  0RE
B   1LC  0LB
C   1RD  0LB
D   1RF  0LA
E   1RC  ---
F   0RA  0LD
```

## 1. Tape notation

Away from the head the tape consists of `1`s separated by gaps of one or three `0`s. Reading from the
leftmost `1`, we write it as a list of **items**: item `k` = `k` gaps of length one followed by a gap
of length three, i.e. the cells `1(01)^k 000`, of length `2k + 4`.
(`k*` marks a gap of length 0, `k(g)` a gap of length `g`; both only occur near the left end.)

At the moments the head reaches a new leftmost cell (each such moment ends a sweep over the whole tape),
the tape has the form

    Z  w^N  T  u^M  tail

- `Z`, the **zone**: a short list of small items,
- `w^N`: `N` copies of the word `w` (`w = 8` or `w = 0 3 1`),
- `T`: a short list, in one family `T = 0 4 3^k 2` with a parameter `k`,
- `u^M = (0 1)^M`: `M` copies of the items `0 1`,
- `tail = 0`.

A configuration is **canonical** when its zone is one of 6 zone patterns found by the search; together
with `w`, `T`, `u` and `tail` this gives the **nodes** of the proof (385 reachable nodes, 4 of them
families with symbolic `k`, 180 partial nodes = family members with a concrete small `k`).

## 2. What the machine does

The start: after 226 258 281 steps from the blank tape the machine is in the canonical configuration

    1 7 0 0* 4 3 0 0 0 0 0 9 | 8^224 | 3 | (0 1)^2045 | 0     (state C, head at the left end).

From there it alternates two phases.

**Phase A (descent).** The zone works like a complicated finite counter: every sweep changes a few of
its items, and now and then it absorbs a block of `8`s and appends pairs `0 1` at the far right. After a
fixed number of sweeps (3232 sweeps, ~3.6e8 steps for the start node at `N` ~ 224) the zone is back
in the same pattern with

    (N + P, M)  ->  (N, M + dM),     (P, dM) in {(40,704), (10,168), (100,1744), (132,2336), (3,52), (17,300)}

(lemma A; about 17.4-17.7 new pairs per consumed `8`). This repeats until fewer than `r_low + P`
copies of `w` are left (`r_low = 12`).

**Phase B (conversion).** With `r` copies of `w` left, the zone consumes them and then converts the
whole `(0 1)^M` block into about `M/2` copies of `8` (two pairs `0 1` and one `8` have the same length,
20 cells), leaving a new block of a few thousand pairs. The result is the first canonical configuration
of the next node, with

    N1 = a + b*x,   M1 = c + d*x,   (k1 = e + f*x),   x = (M - 1000 - (M mod 2)) / 2,

where `b = 1` for 87% of the transitions (otherwise `b = 0`), `d` in {0, 2}, and the next node depends on
the node, on `r` and on the parity of `M` (lemma B).

So one cycle (phase B followed by phase A) maps `M` to roughly `8.4 M` ... `8.85 M`
(asymptotic factor `b/2 * dM/P` of the target node, over all transitions). Which node and which `r`
come next depends on residues of `M`, so the sequence of nodes is erratic - but every possible
combination is covered by the proof, which is what makes the argument work.

For example, on the actual trajectory:

    start node (224, 2045) --A,A--> (24, 5533) --B--> T = '7 0 2' node (2800, 2939) --A...--> (100, 50027) --B--> ...

## 3. The proof

A **state** is a node together with `N = r` in `[r_low, r_low + P)` and `M` at the last canonical point
of a phase A. The **domain** is: every reachable node, every such `r`, every `M >= 500`, and for
families every `k >= K_fam` with the family's parity.

1. **Start.** The configuration above is reached from the blank tape (plain simulation,
   `start_check.c`), and two lemma-A steps bring it to the domain state (start node, `r = 24`, `M = 5533`).
2. **Lemmas.** For every node a lemma A (both parities of `M`, plus small-`N` and small-`M` variants),
   and for every (node, `r`, parity of `M`) a lemma B, each proved by symbolic simulation (`ssim4`) with
   `M` (and `k`) as variables under recorded linear constraints.
3. **Closure.** From every domain state, lemma B and then lemma A lead again to a domain state
   (`verify4.py`: 30 628 domain classes; every class, i.e. all `M >= 500` and all `k`, is checked, using
   residue splitting and monotonicity; 2 exceptional landings with `M < 500` are followed explicitly).

Every lemma takes at least one step, so the machine runs forever.

## 4. Trust base and checks

The lemmas rely on the C++ symbolic simulator `ssim4` (backsymbol macro machine with blocks of 20 cells,
chain steps over runs, cycle acceleration). Everything else is checked by short independent programs;
see the table in [README.md](README.md). Concrete simulations (`fsim`, and the plain `start_check.c`)
agree with every lemma prediction tested: all lemma-B instances used in the search, 810 lemma-A
instances, 3000 random full cycles and the real trajectory.

Why there is no short hand proof: the zone dynamics in phase A is deterministic and finite but
irregular (thousands of sweeps per lemma A with no visible arithmetic structure in the zone items).
The proof therefore consists of 6 zone patterns, per-node lemmas A and B, and a finite transition table,
rather than a few counter rules. A Rocq formalization will have to check these lemmas mechanically,
e.g. with a symbolic simulator verified in Rocq (PLAN.md, step 3).
