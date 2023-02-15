#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <limits.h>

ssize_t myers_diff(unsigned char *a, ssize_t sa,
               unsigned char *b, ssize_t sb) {
  assert (sa < LONG_MAX/2 && sb < LONG_MAX/2);
  ssize_t max = sa + sb;
  assert (max < (LONG_MAX/2-1)/sizeof(ssize_t));

  ssize_t *v = (ssize_t*)calloc(2*max+1, sizeof(ssize_t));

  ssize_t x, y;
  for (ssize_t d = 0; d <= max; d++) {
    for (ssize_t k = -d; k <= d; k += 2) {
      if (k == -d || (k != d && v[max+k-1] < v[max+k+1])) {
        x = v[max+k+1];
      } else {
        x = v[max+k-1] + 1;
      }
      y = x - k;
      while (x < sa && y <= sb && a[x] == b[y]) {
        x++;
        y++;
      }
      v[max+k] = x;
      if (x >= sa && y >= sb) {
        return d;
      }
    }
  }
}

ssize_t get_size(FILE *fp) {
  ssize_t s;
  fseek(fp, 0, SEEK_END);
  s = ftell(fp);
  fseek(fp, 0, SEEK_SET);
  return s;
}

int main(int argc, char **argv) {
  if (argc < 3) {
    printf("Usage: %s <file1> <file2>\n", argv[0]);
    return 1;
  }

  FILE *fa = fopen(argv[1], "r");
  if (fa == NULL) {
    perror(argv[1]);
    return 1;
  }
  FILE *fb = fopen(argv[2], "r");
  if (fb == NULL) {
    perror(argv[2]);
    fclose(fa);
    return 1;
  }

  ssize_t sa, sb;
  sa = get_size(fa);
  sb = get_size(fb);

  void *a = malloc(sa);
  if (a == NULL) {
    fclose(fb);
    fclose(fa);
    return 1;
  }

  void *b = malloc(sb);
  if (a == NULL) {
    free(a);
    fclose(fb);
    fclose(fa);
    return 1;
  }

  if (fread(a, 1, sa, fa) != sa
      || fread(b, 1, sb, fb) != sb)
    goto out;

  printf("%ld", myers_diff(a, sa, b, sb));

 out:
  free(b);
  free(a);
  fclose(fb);
  fclose(fa);
  return 0;
}
