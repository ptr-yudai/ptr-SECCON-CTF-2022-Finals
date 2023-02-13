	A = arch
	A == ARCH_X86_64 ? next : kill
	A = sys_number
	A >= 0x40000000 ? kill : next
	A == execve ? kill : next
  A == execveat ? kill : next
  return ALLOW
kill:
  return KILL
