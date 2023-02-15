;; returns: int value
scan:
  sub rsp, 8
  xor r12d, r12d                ; value
  xor ebx, ebx                  ; negative flag
  .@Lloop:
  ; read 1 byte
  mov edx, 1
  mov rsi, rsp
  xor edi, edi
  xor eax, eax
  syscall
  cmp rax, 1
  jnz .@Lbreak
  mov al, [rsp]                 ; al = input character
  test ebx, ebx
  jnz .@Lconvert
  ; check if first character is '-'
  cmp al, '-'
  jnz .@Lpositive
  mov ebx, 2                    ; negative
  jmp .@Lloop
  .@Lpositive:
  mov ebx, 1                    ; positive
  .@Lconvert:
  cmp al, 0x0a
  jz .@Lbreak
  ; check if input is digit
  sub al, 0x30
  cmp al, 9
  ja .@Lfail
  ; v = (v * 10) + (c - '0')
  lea rdx, [r12+r12*4]
  movsx rax, al
  lea r12, [rax+rdx*2]
  jmp .@Lloop
  .@Lbreak:
  cmp ebx, 2                    ; is negative?
  jnz .@Lskip_negate
  neg r12
  .@Lskip_negate:
  mov edx, 5                    ; type=TYPE_INT
  mov rax, r12                  ; value
  add rsp, 8
  ret
  ; return 0 on undefined behavior
  .@Lfail:
  xor r12d, r12d
  jmp .@Lbreak
