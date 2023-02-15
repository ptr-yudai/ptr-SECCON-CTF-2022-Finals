;; arg1: value
;; arg2: type
;; returns: void
print:
  push rbp
  mov rbp, rsp
  push rcx
  push rsi
  mov al, [rbp+0x18]            ; al = type
  cmp al, 0                     ; is function?
  jz .@Lfunc
  cmp al, 1                     ; is array?
  jz .@Larray
  cmp al, 2                     ; is bool?
  jz .@Lbool
  cmp al, 3                     ; is byte?
  jz .@Lbyte
  cmp al, 4                     ; is int?
  jz .@Luint
  cmp al, 5                     ; is uint?
  jz .@Lint
;; function
  .@Lfunc:
  mov edx, 10
  call .@Sfunc
  db "<function>"
  .@Sfunc:
  pop rsi
  call .@Fwrite                 ; print "<function>"
  jmp .@Lret
;; array
  .@Larray:
  mov r15, [rbp+0x10]           ; r15 = array
  ; print '[' if not string
  cmp byte [r15], 3             ; is string?
  jz .@Lstr1
  mov edi, '['
  call .@Fwritechar
  .@Lstr1:
  ; for (i=0; i < array.length; i++) {
  xor r14d, r14d
  .@Lnext:
  cmp qword [r15+8], r14
  jle .@Lbreak
  ; print element
  push qword [r15]              ; element type
  push qword [r15+r14*8+0x10]   ; element value
  call print
  add rsp, 0x10
  inc r14d
  ; print ', ' if not string
  cmp byte [r15], 3             ; is byte array?
  jz .@Lstr2
  cmp qword [r15+8], r14        ; is last element?
  jz .@Lstr2
  mov edi, ','
  call .@Fwritechar
  mov edi, ' '
  call .@Fwritechar
  .@Lstr2:
  jmp .@Lnext
  ; }
  .@Lbreak:
  ; print ']' if not string
  cmp byte [r15], 3             ; is byte array
  jz .@Lstr3
  mov edi, ']'
  call .@Fwritechar
  .@Lstr3:
  jmp .@Lret
;; bool
  .@Lbool:
  mov al, [rbp+0x10]            ; value
  test al, al
  jz .@Lfalse
  ; print "true"
  call .@Strue
  db "true"
  .@Strue:
  pop rsi
  mov edx, 4
  call .@Fwrite
  jmp .@Lret
  ; print "false"
  .@Lfalse:
  call .@Sfalse
  db "false"
  .@Sfalse:
  pop rsi
  mov edx, 5
  call .@Fwrite
  jmp .@Lret
;; byte
  .@Lbyte:
  mov rdi, [rbp+0x10]           ; value
  call .@Fwritechar
  jmp .@Lret
;; uint
  .@Luint:
  mov rdi, [rbp+0x10]           ; value
  call .@Fwriteval
  jmp .@Lret
;; int
  .@Lint:
  mov rax, [rbp+0x10]           ; value
  mov rdi, rax
  shr rax, 63
  jz .@Lpos
  ; print '-' if negative
  neg rdi                       ; negate and print later
  push rdi
  mov edi, '-'
  call .@Fwritechar
  pop rdi
  .@Lpos:
  call .@Fwriteval
  jmp .@Lret
;; writeval(uint)
  .@Fwriteval:
  mov r8, -0x3333333333333333
  lea rbx, [rsp - 1]
  sub rsp, 0x18
  mov byte [rbx], 0
  xor ecx, ecx
  .@Lp:
  inc ecx
  dec rbx
  mov rax, rdi
  mul r8
  mov rax, rdi
  shr rdx, 3
  lea rsi, [rdx+rdx*4]
  add rsi, rsi
  sub rax, rsi
  add al, 0x30
  mov [rbx], al
  mov rax, rdi
  mov rdi, rdx
  cmp rax, 9
  ja .@Lp
  mov edx, ecx
  mov rsi, rbx
  call .@Fwrite
  add rsp, 0x18
  ret
;; writechar(byte)
  .@Fwritechar:
  mov edx, 1
  push rdi
  mov rsi, rsp
  call .@Fwrite
  add rsp, 8
  ret
;; write 1 byte
  .@Fwrite:
  mov edi, 1
  mov eax, edi
  syscall
  ret
;; cleanup
  .@Lret:
  pop rsi
  pop rcx
  pop rbp
  ret
