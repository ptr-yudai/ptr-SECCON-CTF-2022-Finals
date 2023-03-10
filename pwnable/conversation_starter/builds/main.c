#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <linux/seccomp.h>
#include <sys/prctl.h>

#define MAX_SLOT 5
#define LEN_NAME 0x100

typedef unsigned char  u8;
typedef unsigned short u16;
typedef unsigned int   u32;
typedef int i32;

typedef struct {
  i32 (*fn_sleep)(u32);
  u32 interval;
  char message[40];
} dialogue_t;

u8 *name_alice = NULL, *name_bob = NULL;
dialogue_t *slot[MAX_SLOT];

/**
 * @fn
 * Get user input as string.
 * @param msg   Message to print before input.
 * @param buf   Buffer to store user input.
 * @param size  Maximum size to read.
 * @param delim Deliminater byte to stop reading input. If this value is zero, this function reads exactly @p size bytes.
 */
void readline(const char *msg, u8 delim, u8 *buf, u32 size) {
  u8 c;
  u32 i;
  printf("%s", msg);

  /* Read until deliminater */
  for (c = 0, i = 0; i < size-1; i++) {
    if (read(STDIN_FILENO, &c, 1) != 1) {
      break;
    } else if (delim && c == delim) {
      buf[i] = '\0';
      return;
    }
    buf[i] = c;
  }

  /* Clear uninitialized memory region */
  for (; i < size-1; i++, buf[i] = '\0');
}

/**
 * @fn
 * Get user input as integer.
 * @param msg Message to print before input.
 * @returns An integer value entered by the user.
 */
u32 read_u32(const char *msg) {
  u8 buf[0x10] = {};
  readline(msg, '\n', buf, sizeof(buf));
  return (u32)atoi(buf);
}

/**
 * @fn
 * Edit a dialogue
 */
void edit_message(void) {
  u32 index, type;

  /* Ask index */
  index = read_u32("index: ");
  if (index >= MAX_SLOT) return;

  /* Ask interval and unit */
  slot[index]->interval = read_u32("interval: ");
  type = read_u32("[1] sleep / [2] usleep: ");
  slot[index]->fn_sleep = (type == 1) ? (void*)sleep : usleep;

  /* Ask message */
  readline("message: ", '\n', slot[index]->message, sizeof(dialogue_t)-1);
}

/**
 * @fn
 * Start conversation
 */
void start_conversation(void) {
  u8 size;

  if (read_u32("change name? [1=Yes / 2=No]: ") == 1) {
    /* Ask name of Alice */
    size = (u8)read_u32("length of name 1: ");
    readline("name 1: ", 0, name_alice, size);

    /* Ask name of Bob */
    size = (u8)read_u32("length of name 2: ");
    readline("name 2: ", 0, name_bob, size);
  }

  for (i32 i = 0; i < MAX_SLOT; i++) {
    if (slot[i]->message[0]) {
      /* Print name */
      printf("%s: ", (i % 2 == 0) ? name_alice : name_bob);

      /* Print message */
      for (u8 *p = slot[i]->message; *p != 0; p++) {
        putchar(*p);
        slot[i]->fn_sleep(slot[i]->interval);
      }
      putchar('\n');

      /* Clear dialogue */
      memset(slot[i], 0, sizeof(dialogue_t));
    }
  }
}

/**
 * @fn
 * Entry point
 */
i32 main() {
  i32 choice;

  /* Initialize dialogue slots */
  strcpy(name_alice = malloc(LEN_NAME), "Alice");
  strcpy(name_bob = malloc(LEN_NAME), "Bob");
  for (i32 i = 0; i < MAX_SLOT; i++)
    slot[i] = (dialogue_t*)calloc(1, sizeof(dialogue_t));

  while (1) {
    puts("1. edit message\n"
         "2. start conversation");
    choice = read_u32("> ");

    switch (choice) {
      case 1: edit_message(); break;
      case 2: start_conversation(); break;
      default: return 0;
    }
  }
}

/**
 * @fn
 * Constructor
 */
__attribute__((constructor))
void setup(void) {
  /* Set seccomp filter */
  static unsigned char filter[] = {
    32,0,0,0,4,0,0,0,21,0,0,5,62,0,0,192,32,0,0,0,0,0,0,0,53,0,3,0,0,0,0,
    64,21,0,2,0,59,0,0,0,21,0,1,0,66,1,0,0,6,0,0,0,0,0,255,127,6,0,0,0,0,0,0,0
  };
  struct prog {
    unsigned short len;
    unsigned char *filter;
  } rule = {
    .len = sizeof(filter) >> 3,
    .filter = filter
  };
  if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
    perror("prctl(PR_SET_NO_NEW_PRIVS)");
    exit(1);
  }
  if (prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &rule) < 0) {
    perror("prctl(PR_SET_SECCOMP)");
    exit(2);
  }

  /* Disable buffering */
  setbuf(stdin, NULL);
  setbuf(stdout, NULL);
  setbuf(stderr, NULL);

  /* Set timeout */
  alarm(180);
}
