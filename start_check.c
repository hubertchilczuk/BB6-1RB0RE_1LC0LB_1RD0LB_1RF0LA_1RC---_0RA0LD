/* Independent plain Turing-machine simulator (no macro steps, no acceleration) for
 * 1RB0RE_1LC0LB_1RD0LB_1RF0LA_1RC---_0RA0LD, started on a blank tape in state A.
 * Usage: start_check STEPS OUT  -> writes "steps state head_offset\ncells\n" (cells from the head
 * position to the rightmost 1; the head must be at the leftmost non-blank cell, as in the sample files).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* write, move (+1 R / -1 L), next state (-1 = halt) for [state][symbol], A..F = 0..5 */
static const int W[6][2] = {{1, 0}, {1, 0}, {1, 0}, {1, 0}, {1, -1}, {0, 0}};
static const int MV[6][2] = {{+1, +1}, {-1, -1}, {+1, -1}, {+1, -1}, {+1, 0}, {+1, -1}};
static const int NX[6][2] = {{1, 4}, {2, 1}, {3, 1}, {5, 0}, {2, -1}, {0, 3}};

int main(int argc, char **argv) {
    long long steps = atoll(argv[1]);
    long long size = 1LL << 26;
    unsigned char *t = calloc(size, 1);
    long long h = size / 2, lo = h, hi = h;
    int s = 0;
    for (long long i = 0; i < steps; i++) {
        int b = t[h];
        int ns = NX[s][b];
        if (ns < 0) { printf("HALT at step %lld\n", i); return 1; }
        t[h] = (unsigned char)W[s][b];
        h += MV[s][b];
        s = ns;
        if (h < 1 || h >= size - 1) { printf("tape overflow\n"); return 2; }
        if (h < lo) lo = h;
        if (h > hi) hi = h;
    }
    long long first = lo, last = hi;
    while (first < h && !t[first]) first++;
    while (last > h && !t[last]) last--;
    FILE *f = fopen(argv[2], "w");
    fprintf(f, "%lld %d %lld\n", steps, s, h - first);
    for (long long i = first; i <= last; i++) fputc('0' + t[i], f);
    fputc('\n', f);
    fclose(f);
    printf("steps=%lld state=%c head_offset=%lld cells=%lld\n", steps, 'A' + s, h - first, last - first + 1);
    return 0;
}
