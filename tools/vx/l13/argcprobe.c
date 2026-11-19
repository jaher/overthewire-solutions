#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
/* argcprobe: execve self with argv={NULL}; the child (flagged) prints
   argc by re-execing a print helper... simpler: the flagged run prints
   argc directly: execve with argv={NULL} lands in main with argc=?
   This stub: run 1 (no flag) execve's /proc/self/exe with argv={NULL},
   envp={NULL}; run 2 (flag) just prints argc and argv. */
int main(int argc, char **argv, char **envp) {
    if (getenv("FLAGGED") != NULL) {
        printf("argc=%d argv0=%p\n", argc, (void*)(argc > 0 ? argv[0] : NULL));
        return 0;
    }
    char self[512];
    ssize_t n = readlink("/proc/self/exe", self, sizeof self - 1);
    self[n] = 0;
    char *av[1] = { NULL };
    char *ev[1] = { NULL };
    execve(self, av, ev);
    return 1;
}
