#include <emscripten.h>
#include <stdio.h>
#include <stdlib.h>

#define LENGTH 4

int EMSCRIPTEN_KEEPALIVE
__internal_bruteforce(char *digits, void *callback, int n) {
  if (n < 0) {
    if (((int (*)(char*))callback)(digits)) {
      return 1;
    }
  } else {
    for (int i = 0; i < 10; i++, digits[n]++) {
      if (__internal_bruteforce(digits, callback, n-1)) {
        return 1;
      }
    }
    digits[n] = 0;
  }
  return 0;
}

int EMSCRIPTEN_KEEPALIVE bruteforce(char* digits, void *callback) {
  return __internal_bruteforce(digits, callback, LENGTH-1);
}

int EMSCRIPTEN_KEEPALIVE oracle(char *digits) {
  return digits[3] == 5 && digits[2] == 9 && digits[1] == 6 && digits[0] == 3;
}

int EMSCRIPTEN_KEEPALIVE main() {
  char *digits = (char*)malloc(sizeof(char) * LENGTH);
  for (int i = 0; i < LENGTH; i++) {
    digits[i] = 0;
  }
  puts("[+] Computing...");

  if (bruteforce(digits, oracle)) {
    printf("Hit: %d%d%d%d\n", digits[3], digits[2], digits[1], digits[0]);
  }

  puts("[+] Done.");
  free(digits);
  return 0;
}
