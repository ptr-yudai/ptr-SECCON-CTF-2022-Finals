#!/bin/sh
exec qemu-system-x86_64 \
     -m 64M \
     -machine q35,smm=on \
     -bios bios.bin \
     -nographic \
     -kernel bzImage \
     -append "console=ttyS0 loglevel=3 oops=panic panic=-1 kaslr" \
     -no-reboot \
     -cpu kvm64,smap,smep \
     -monitor /dev/null \
     -initrd rootfs.cpio
