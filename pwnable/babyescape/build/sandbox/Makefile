all:
	gcc -S sandbox.c -o sandbox.S -Os
	musl-gcc sandbox.S -o sandbox -static
	strip --strip-all sandbox
	rm sandbox.S
