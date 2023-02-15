/* gcc sandbox.c -o sandbox -lseccomp */
#include <stdio.h>
#include <unistd.h>
#include <seccomp.h>

int main(int argc, char **argv, char **envp) {
  scmp_filter_ctx ctx;

  if (argc < 2) {
    printf("Usage: %s <program> <arg1> ...\n", argv[0]);
    return 1;
  }

  ctx = seccomp_init(SCMP_ACT_KILL);
  if (ctx == NULL)
    return 1;

  if (seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(read), 1,
                       SCMP_A0(SCMP_CMP_EQ, STDIN_FILENO)))
    goto err;

  if (seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(write), 1,
                       SCMP_A0(SCMP_CMP_EQ, STDOUT_FILENO)))
    goto err;

  if (seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit), 0))
    goto err;

  if (seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(execve), 0))
    goto err;

  if (seccomp_load(ctx))
    goto err;

  seccomp_release(ctx);

  execve(argv[1], &argv[2], envp);
  return 0;

 err:
  seccomp_release(ctx);
  return 1;
}
