exit:
  mov rdi, [rsp+8]
  mov eax, 60
  syscall
  hlt
