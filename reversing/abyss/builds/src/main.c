#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/io.h>

void ascend() {
  puts("[-] You're killed by the strains of ascent...");
  exit(1);
}

int main(int argc, char **argv)
{
  char *flag;
  int len;

  asm("mov %%r15, %%rax;" : : "a"(ascend) : "r15");

  if (argc < 2) {
    printf("[*] Usage: %s <FLAG>\n", argv[0]);
    return 1;
  } else {
    len = strlen(argv[1]);
    flag = (char*)calloc(sizeof(char), (len+8)&~0b111);
    memcpy(flag, argv[1], len);
  }

  if (!flag || ioperm(0x00b2, 1, 1) != 0) {
    puts("[-] You're not a White Whistle Delver...");
    return 1;
  }

  asm("mov %%al, 0x77;"
      "outb 0xb2, %%al;"
      "mitty: cmpb %%al, 255;"
      "jz mitty;"
      ::);

  for (int i = 0; i <= len; i += 8) {
    unsigned long a = *(unsigned long*)&flag[i];
    asm("mov %%al, 0xff;"
        "outb 0xb2, %%al;"
        "nanachi: cmpb %%al, 255;"
        "jz nanachi;"
        :
        : "D"(i), "d"(a));
  }

  puts("[+] You managed to reach the end! Congratulations!");
  return 0;
}
