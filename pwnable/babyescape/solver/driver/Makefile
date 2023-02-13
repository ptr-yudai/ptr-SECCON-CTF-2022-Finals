obj-m := pwn.o
BUILDROOT_PATH := /home/ptr/armoury/buildroot
KBUILD_DIR := $(BUILDROOT_PATH)/output/build/linux-6.1.5

all:
	$(MAKE) -C $(KBUILD_DIR) M=$(shell pwd) modules

clean:
	$(MAKE) -C $(KBUILD_DIR) M=$(shell pwd) clean
