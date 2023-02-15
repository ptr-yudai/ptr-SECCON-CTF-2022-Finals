from interpreter.types.boolean import Bool

class Int(object):
    def __init__(self, value):
        if value < 0:
            value = (-value ^ 0xffff_ffff_ffff_ffff) + 1
        self.value = value & 0xffff_ffff_ffff_ffff

    def call(self, *args):
        raise RuntimeError("Int is not callable")

    @property
    def svalue(self):
        if self.value >> 63:
            return -((self.value ^ 0xffff_ffff_ffff_ffff) + 1)
        else:
            return self.value

    def cast_to(self, type):
        from interpreter.types.boolean  import Bool
        from interpreter.types.byte     import Byte
        from interpreter.types.unsigned import UInt
        if type == Int:
            return self
        elif type == UInt:
            return UInt(self.value)
        elif type == Byte:
            return Byte(self.value)
        elif type == Bool:
            return Bool(self.value != 0)
        else:
            raise RuntimeError(f"Cannot cast Int to {type}")

    def clone(self):
        return Int(self.value)

    def __add__(self, other):
        if not isinstance(other, Int):
            raise RuntimeError(f"Unsupported operand types for +: Int and {type(other)}")
        return Int(self.value + other.value)

    def __sub__(self, other):
        if not isinstance(other, Int):
            raise RuntimeError(f"Unsupported operand types for -: Int and {type(other)}")
        return Int(self.value - other.value)

    def __mul__(self, other):
        if not isinstance(other, Int):
            raise RuntimeError(f"Unsupported operand types for *: Int and {type(other)}")
        return Int(self.value * other.value)

    def __mod__(self, other):
        if not isinstance(other, Int):
            raise RuntimeError(f"Unsupported operand types for %: Int and {type(other)}")
        if other.value == 0:
            raise RuntimeError("Modulo by zero")
        a, b = self.svalue, other.svalue
        c = a % b
        if a > 0 and b < 0 and c != 0:
            c += -b
        elif a < 0 and b > 0 and c != 0:
            c -= b
        return Int(c)

    def __floordiv__(self, other):
        if not isinstance(other, Int):
            raise RuntimeError(f"Unsupported operand types for /: Int and {type(other)}")
        if other.value == 0:
            raise RuntimeError("Integer division by zero")
        return Int(int(self.svalue / other.svalue))

    def __lshift__(self, other):
        if not isinstance(other, Int) and not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for <<: Int and {type(other)}")
        if other.value >= 64:
            raise RuntimeError(f"Shift count is too big: 64 <= {type(other.value)}")
        return Int(self.value << other.value)

    def __rshift__(self, other):
        if not isinstance(other, Int) and not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for >>: Int and {type(other)}")
        if other.value >= 64:
            raise RuntimeError(f"Shift count is too big: 64 <= {type(other.value)}")
        if self.value >> 63:
            return Int(((0xffff_ffff_ffff_ffff << 64) | self.value) >> other.value)
        else:
            return Int(self.value >> other.value)

    def __xor__(self, other):
        if not isinstance(other, Int):
            raise RuntimeError(f"Unsupported operand types for ^: Int and {type(other)}")
        return Int(self.value ^ other.value)

    def __and__(self, other):
        if not isinstance(other, Int):
            raise RuntimeError(f"Unsupported operand types for &: Int and {type(other)}")
        return Int(self.value & other.value)

    def __or__(self, other):
        if not isinstance(other, Int):
            raise RuntimeError(f"Unsupported operand types for |: Int and {type(other)}")
        return Int(self.value | other.value)

    def __not__(self):
        return Int(self.value ^ 0xffff_ffff_ffff_ffff)

    def __neg__(self):
        return Int((self.value ^ 0xffff_ffff_ffff_ffff) + 1)

    def __pos__(self):
        return Int(self.value)

    def __eq__(self, other):
        if not isinstance(other, Int):
            raise RuntimeError(f"Unsupported operand types for ==: Int and {type(other)}")
        return Bool(self.value == other.value)

    def __ne__(self, other):
        if not isinstance(other, Int):
            raise RuntimeError(f"Unsupported operand types for !=: Int and {type(other)}")
        return Bool(self.value != other.value)

    def __lt__(self, other):
        if not isinstance(other, Int):
            raise RuntimeError(f"Unsupported operand types for <: Int and {type(other)}")
        return Bool(self.svalue < other.svalue)

    def __le__(self, other):
        if not isinstance(other, Int):
            raise RuntimeError(f"Unsupported operand types for <=: Int and {type(other)}")
        return Bool(self.svalue <= other.svalue)

    def __gt__(self, other):
        if not isinstance(other, Int):
            raise RuntimeError(f"Unsupported operand types for >: Int and {type(other)}")
        return Bool(self.svalue > other.svalue)

    def __ge__(self, other):
        if not isinstance(other, Int):
            raise RuntimeError(f"Unsupported operand types for >=: Int and {type(other)}")
        return Bool(self.svalue >= other.svalue)
