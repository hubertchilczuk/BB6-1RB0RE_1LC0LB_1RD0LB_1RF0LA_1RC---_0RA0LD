/* Plain simulation from a config file; at every "new leftmost cell" event print "step state" and the tape
 * from the head to the rightmost 1. Stops after MAXEVENTS events or when the tape equals TARGET (optional).
 * usage: evtapes CFG MAXSTEPS MAXEVENTS
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const int W[6][2] = {{1, 0}, {1, 0}, {1, 0}, {1, 0}, {1, -1}, {0, 0}};
static const int MV[6][2] = {{+1, +1}, {-1, -1}, {+1, -1}, {+1, -1}, {+1, 0}, {+1, -1}};
static const int NX[6][2] = {{1, 4}, {2, 1}, {3, 1}, {5, 0}, {2, -1}, {0, 3}};
#define SZ (1 << 26)
static unsigned char t[SZ];

int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "r"); char sb[64]; int s; long long off;
    if (fscanf(f, "%63s %d %lld ", sb, &s, &off) != 3) return 1;
    long long maxsteps = atoll(argv[2]), maxev = atoll(argv[3]);
    long long h = SZ / 2, lo = h, hi = h, x = h; int ch;
    while ((ch = fgetc(f)) == '0' || ch == '1') { t[x] = ch - '0'; if (t[x] && x > hi) hi = x; x++; }
    fclose(f);
    h += off; lo = h; long long ev = 0;
    for (long long i = 0; i < maxsteps; i++) {
        int b = t[h], ns = NX[s][b];
        if (ns < 0) { printf("HALT\n"); return 0; }
        t[h] = W[s][b];
        if (t[h] && h > hi) hi = h;
        h += MV[s][b]; s = ns;
        if (h < lo) {
            lo = h;
            printf("%lld %d\n", i + 1, s);
            for (long long j = h; j <= hi; j++) putchar('0' + t[j]);
            putchar('\n');
            if (++ev >= maxev) return 0;
        }
    }
    return 0;
}
