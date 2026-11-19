#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#ifndef AT_EMPTY_PATH
#define AT_EMPTY_PATH 0x1000
#endif
#include <sys/syscall.h>
#include <spawn.h>
#include <sys/wait.h>
extern char **environ;
/* exec13: try every exec path against /vortex/vortex13 and report whether
   the child reads stdin (i.e. vuln() runs past the argc gate).
   usage: exec13 <mode> <stdin-file>
   modes: execve (argv=NULL), execven (argv={NULL}), execveat (dirfd+empty),
          fexecve (memfd of the binary), posix_spawn (argv={NULL}). */
int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: exec13 <mode> <stdin-file>\n"); return 2; }
    const char *mode = argv[1];
    int st = 0;
    int in = open(argv[2], O_RDONLY);
    if (in < 0) { perror("open stdin"); return 2; }
    int pfd[2];
    if (pipe(pfd) < 0) { perror("pipe"); return 2; }
    pid_t pid = fork();
    if (pid == 0) {
        dup2(in, 0);
        close(in); close(pfd[0]);
        dup2(pfd[1], 2);            /* child's stderr -> the pipe */
        dup2(pfd[1], 1);
        close(pfd[1]);
        char *ev[1] = { NULL };
        char *av[1] = { NULL };
        char *av1[2] = { NULL, NULL };
        if (strcmp(mode, "execve") == 0) {
            syscall(SYS_execve, "/vortex/vortex13", NULL, ev);
        } else if (strcmp(mode, "execven") == 0) {
            syscall(SYS_execve, "/vortex/vortex13", av, ev);
        } else if (strcmp(mode, "execven1") == 0) {
            syscall(SYS_execve, "/vortex/vortex13", av1, ev);
        } else if (strcmp(mode, "execveat") == 0) {
            int dfd = open("/vortex", O_RDONLY | O_DIRECTORY);
            /* execveat(dfd, "vortex13", NULL argv, NULL env, 0) */
            syscall(SYS_execveat, dfd, "vortex13", NULL, ev, 0);
        } else if (strcmp(mode, "fexecve") == 0) {
            int fd = open("/vortex/vortex13", O_RDONLY);
            syscall(SYS_execveat, fd, "", NULL, ev, AT_EMPTY_PATH);
        }
        _exit(126);                  /* exec failed */
    }
    if (strcmp(mode, "spawn") == 0) {
        posix_spawn_file_actions_t fa;
        posix_spawn_file_actions_init(&fa);
        posix_spawn_file_actions_adddup2(&fa, in, 0);
        posix_spawn_file_actions_adddup2(&fa, pfd[1], 1);
        posix_spawn_file_actions_adddup2(&fa, pfd[1], 2);
        char *sav[2] = { NULL, NULL };
        char *sev[1] = { NULL };
        pid_t c;
        if (posix_spawn(&c, "/vortex/vortex13", &fa, NULL, sav, sev) != 0) {
            printf("posix_spawn failed\n");
            return 1;
        }
        close(in); close(pfd[1]);
        waitpid(c, &st, 0);
        close(pfd[0]);
        printf("mode=spawn exit=%d sig=%d\n",
               WIFEXITED(st) ? WEXITSTATUS(st) : -1,
               WIFSIGNALED(st) ? WTERMSIG(st) : 0);
        return 0;
    }
    close(pfd[1]);
    close(in);
    char buf[4096];
    ssize_t n;
    int got = 0;
    while ((n = read(pfd[0], buf, sizeof buf)) > 0) {
        if (!got) { printf("child output: "); got = 1; }
        for (ssize_t i = 0; i < n; i++)
            if (buf[i] >= 32 && buf[i] < 127) putchar(buf[i]);
        printf("\n");
    }
    close(pfd[0]);
    waitpid(pid, &st, 0);
    printf("mode=%s exit=%d sig=%d\n", mode,
           WIFEXITED(st) ? WEXITSTATUS(st) : -1,
           WIFSIGNALED(st) ? WTERMSIG(st) : 0);
    return 0;
}
