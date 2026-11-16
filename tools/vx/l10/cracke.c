#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define NV 20

/* Brute-force the srand() seed: for every candidate time value and skip
   count, reseed the target's own libc rand() and compare the next 20
   outputs against the array the level printed. */
int main(int argc, char **argv) {
    unsigned arr[NV];
    for (int i = 0; i < NV; i++) arr[i] = strtoul(argv[i+1], 0, 16);
    time_t t0 = time(0);
    for (int t = (int)t0 - 600; t < (int)t0 + 600; t++) {
        for (int skip = 0; skip < 500; skip++) {
            srand((unsigned)t);
            for (int i = 0; i < skip; i++) rand();
            int ok = 1;
            for (int i = 0; i < NV; i++)
                if ((unsigned)rand() != arr[i]) { ok = 0; break; }
            if (ok) { printf("FOUND seed=%d skip=%d\n", t, skip); return 0; }
        }
    }
    printf("NOPE\n");
    return 1;
}
