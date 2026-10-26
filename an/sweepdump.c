/* Plain simulation from a config file; at every "new leftmost cell" event print the whole tape as items.
 * Tape (from the leftmost 1) is split by gaps of zeros between consecutive 1s; an item is the number k of
 * gap-1 ("10") units followed by the terminating gap: "k" for gap 3, "k*" for gap 0 ("11"), "k(g)" otherwise.
 * Consecutive equal items / equal item pairs are run-length compressed as x^n.
 * usage: sweepdump CFG MAXSTEPS [MAXEVENTS]
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const int W[6][2] = {{1, 0}, {1, 0}, {1, 0}, {1, 0}, {1, -1}, {0, 0}};
static const int MV[6][2] = {{+1, +1}, {-1, -1}, {+1, -1}, {+1, -1}, {+1, 0}, {+1, -1}};
static const int NX[6][2] = {{1, 4}, {2, 1}, {3, 1}, {5, 0}, {2, -1}, {0, 3}};
#define SZ (1 << 26)
static unsigned char t[SZ];
static int items[1 << 22]; /* encoded: k*64 + kind (0: gap3, 1: gap0, 2+g: other) */

static void item_str(int v, char *b) {
    int k = v >> 6, g = v & 63;
    if (g == 0) sprintf(b, "%d", k); else if (g == 1) sprintf(b, "%d*", k); else sprintf(b, "%d(%d)", k, g - 2);
}

static void dump(long long step, int s, long long h, long long hi) {
    long long i = h; while (i <= hi && !t[i]) i++;
    int n = 0, k = 0;
    long long p = i;
    while (p <= hi) {               /* p at a 1 */
        long long q = p + 1; int g = 0;
        while (q <= hi && !t[q]) { q++; g++; }
        if (q > hi) { items[n++] = k * 64 + 0; break; } /* trailing: treat as end */
        if (g == 1) { k++; p = q; continue; }
        items[n++] = k * 64 + (g == 3 ? 0 : g == 0 ? 1 : 2 + (g < 60 ? g : 60));
        k = 0; p = q;
    }
    printf("%lld %c lead0=%lld |", step, 'A' + s, i - h);
    char b[32], c[32];
    for (int a = 0; a < n;) {
        /* pair run */
        if (a + 3 < n && items[a] != items[a + 1] && items[a] == items[a + 2] && items[a + 1] == items[a + 3]) {
            int r = 1; while (a + 2 * r + 1 < n && items[a + 2 * r] == items[a] && items[a + 2 * r + 1] == items[a + 1]) r++;
            item_str(items[a], b); item_str(items[a + 1], c);
            printf(" (%s %s)^%d", b, c, r); a += 2 * r; continue;
        }
        int r = 1; while (a + r < n && items[a + r] == items[a]) r++;
        item_str(items[a], b);
        if (r > 1) printf(" %s^%d", b, r); else printf(" %s", b);
        a += r;
    }
    printf("\n");
}

int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "r"); char sb[64]; int s; long long off;
    if (fscanf(f, "%63s %d %lld ", sb, &s, &off) != 3) return 1;
    long long base = atoll(sb), maxsteps = atoll(argv[2]), maxev = argc > 3 ? atoll(argv[3]) : 1LL << 60;
    long long h = SZ / 2, lo = h, hi = h, x = h; int ch;
    while ((ch = fgetc(f)) == '0' || ch == '1') { t[x] = ch - '0'; if (x > hi) hi = x; x++; }
    fclose(f);
    h += off; long long ev = 0;
    for (long long i = 0; i < maxsteps; i++) {
        int b = t[h], ns = NX[s][b];
        if (ns < 0) { printf("HALT\n"); return 0; }
        t[h] = W[s][b]; h += MV[s][b]; s = ns;
        if (h > hi) hi = h;
        if (h < lo) { lo = h; dump(base + i + 1, s, h, hi); if (++ev >= maxev) return 0; }
    }
    return 0;
}
