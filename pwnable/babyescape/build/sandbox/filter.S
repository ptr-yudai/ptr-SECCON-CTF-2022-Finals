  A = arch
  A != ARCH_X86_64 ? dead : next
  A = sys_number
  A >= 0x40000000 ? dead : next
  A == chroot  ? dead : next
  A == mount   ? dead : next
  A == unshare ? dead : next
  A == reboot  ? dead : next
  A == ptrace  ? dead : next
  A == process_vm_readv  ? dead : next
  A == process_vm_writev ? dead : next
  A == open_by_handle_at ? dead : next
  A == pivot_root ? dead : next
  return ALLOW
dead:
  return KILL
