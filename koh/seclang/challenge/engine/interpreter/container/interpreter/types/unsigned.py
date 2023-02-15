from interpreter.types.signed import Int
from interpreter.types.boolean import Bool

class UInt(object):
    def __init__(self, value):
        if value < 0:
            value = (-value ^ 0xffff_ffff_ffff_ffff) + 1
        self.value = value & 0xffff_ffff_ffff_ffff

    def call(self, *args):
        raise RuntimeError("UInt is not callable")

    def cast_to(self, type):
        from interpreter.types.boolean  import Bool
        from interpreter.types.byte     import Byte
        from interpreter.types.signed   import Int
        if type == Int:
            return Int(self.value)
        elif type == UInt:
            return self
        elif type == Byte:
            return Byte(self.value)
        elif type == Bool:
            return Bool(self.value != 0)
        else:
            raise RuntimeError(f"Cannot cast UInt to {type}")

    def clone(self):
        return UInt(self.value)

    def __add__(self, other):
        if not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for +: UInt and {type(other)}")
        return UInt(self.value + other.value)

    def __sub__(self, other):
        if not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for -: UInt and {type(other)}")
        return UInt(self.value - other.value)

    def __mul__(self, other):
        if not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for *: UInt and {type(other)}")
        return UInt(self.value * other.value)

    def __mod__(self, other):
        if not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for %: UInt and {type(other)}")
        if other.value == 0:
            raise RuntimeError("Modulo by zero")
        return UInt(self.value % other.value)

    def __floordiv__(self, other):
        if not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for /: UInt and {type(other)}")
        if other.value == 0:
            raise RuntimeError("Integer division by zero")
        return UInt(self.value // other.value)

    def __lshift__(self, other):
        if not isinstance(other, Int) and not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for <<: UInt and {type(other)}")
        if other.value >= 64:
            raise RuntimeError(f"Shift count is too big: 64 <= {type(other.value)}")
        return UInt(self.value << other.value)

    def __rshift__(self, other):
        if not isinstance(other, Int) and not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for >>: UInt and {type(other)}")
        if other.value >= 64:
            raise RuntimeError(f"Shift count is too big: 64 <= {type(other.value)}")
        return UInt(self.value >> other.value)

    def __xor__(self, other):
        if not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for ^: UInt and {type(other)}")
        return UInt(self.value ^ other.value)

    def __and__(self, other):
        if not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for &: UInt and {type(other)}")
        return UInt(self.value & other.value)

    def __or__(self, other):
        if not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for |: UInt and {type(other)}")
        return UInt(self.value | other.value)

    def __not__(self):
        return UInt(self.value ^ 0xffff_ffff_ffff_ffff)

    def __neg__(self):
        return UInt((self.value ^ 0xffff_ffff_ffff_ffff) + 1)

    def __pos__(self):
        return UInt(self.value)

    def __eq__(self, other):
        if not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for ==: UInt and {type(other)}")
        return Bool(self.value == other.value)

    def __ne__(self, other):
        if not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for !=: UInt and {type(other)}")
        return Bool(self.value != other.value)

    def __lt__(self, other):
        if not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for <: UInt and {type(other)}")
        return Bool(self.value < other.value)

    def __le__(self, other):
        if not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for <=: UInt and {type(other)}")
        return Bool(self.value <= other.value)

    def __gt__(self, other):
        if not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for >: UInt and {type(other)}")
        return Bool(self.value > other.value)

    def __ge__(self, other):
        if not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for >=: UInt and {type(other)}")
        return Bool(self.value >= other.value)
