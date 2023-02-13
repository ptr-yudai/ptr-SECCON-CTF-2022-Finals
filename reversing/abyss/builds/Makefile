all:
	cd seabios; make
	cp seabios/out/bios.bin qemu/
	cd src; make
	cp src/delver qemu/mount/usr/bin
	cd qemu/mount; find . -print0 | cpio -o --null --format=newc --owner=root:root > ../rootfs.cpio
	./run.sh
