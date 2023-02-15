import std.algorithm.iteration : map;
import std.algorithm.comparison : equal;
import std.stdio;
import std.string;

bool check_password(string password) {
  char[] s = password.dup;
  auto f = (dchar a) {
    return a ^ 0x77;
  };

  return equal(s.map!(f),
               [58, 22, 28, 18, 87, 51, 90, 27, 22, 25, 16, 87,
                48, 5, 18, 22, 3, 87, 54, 16, 22, 30, 25, 86]);
}

void main() {
  asm {
    xor R10D, R10D;
    mov EDX, 1;
    xor ESI, ESI;
    xor EDI, EDI;
    mov EAX, 101;
    syscall;
    test EAX, EAX;
    jz L1;
    mov EDI, 1;
    mov EAX, 60;
    syscall;
  L1:;
  }

  write("Password: ");
  string password = readln().strip;

  if (check_password(password)) {
    writeln("Correct!");
  } else {
    writeln("Wrong...");
  }
}
