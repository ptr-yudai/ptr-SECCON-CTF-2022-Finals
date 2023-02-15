class Byte(object):
    def __init__(self, value):
        if value < 0:
            value = (-value ^ 0xff) + 1
        self.value = value & 0xff

    def call(self, *args):
        raise RuntimeError("Byte is not callable")

    def cast_to(self, type):
        from interpreter.types.boolean  import Bool
        from interpreter.types.signed   import Int
        from interpreter.types.unsigned import UInt
        if type == Int:
            return Int(self.value)
        elif type == UInt:
            return UInt(self.value)
        elif type == Byte:
            return self
        elif type == Bool:
            return Bool(self.value != 0)
        else:
            raise RuntimeError(f"Cannot cast Byte to {type}")

    def clone(self):
        return Byte(self.value)

    def __add__(self, other):
        if not isinstance(other, Byte):
            raise RuntimeError(f"Unsupported operand types for +: Byte and {type(other)}")
        return Byte(self.value + other.value)

    def __sub__(self, other):
        if not isinstance(other, Byte):
            raise RuntimeError(f"Unsupported operand types for -: Byte and {type(other)}")
        return Byte(self.value - other.value)

    def __mul__(self, other):
        if not isinstance(other, Byte):
            raise RuntimeError(f"Unsupported operand types for *: Byte and {type(other)}")
        return Byte(self.value * other.value)

    def __mod__(self, other):
        if not isinstance(other, Byte):
            raise RuntimeError(f"Unsupported operand types for %: Byte and {type(other)}")
        if other.value == 0:
            raise RuntimeError("Modulo by zero")
        return Byte(self.value % other.value)

    def __floordiv__(self, other):
        if not isinstance(other, Byte):
            raise RuntimeError(f"Unsupported operand types for /: Byte and {type(other)}")
        if other.value == 0:
            raise RuntimeError("Integer division by zero")
        return Byte(self.value // other.value)

    def __lshift__(self, other):
        if not isinstance(other, Int) and not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for <<: Byte and {type(other)}")
        if other.value >= 8:
            raise RuntimeError(f"Shift count is too big: 8 <= {type(other.value)}")
        return Byte(self.value << other.value)

    def __rshift__(self, other):
        if not isinstance(other, Int) and not isinstance(other, UInt):
            raise RuntimeError(f"Unsupported operand types for >>: Byte and {type(other)}")
        if other.value >= 8:
            raise RuntimeError(f"Shift count is too big: 8 <= {type(other.value)}")
        return Byte(self.value >> other.value)

    def __xor__(self, other):
        if not isinstance(other, Byte):
            raise RuntimeError(f"Unsupported operand types for ^: Byte and {type(other)}")
        return Byte(self.value ^ other.value)

    def __and__(self, other):
        if not isinstance(other, Byte):
            raise RuntimeError(f"Unsupported operand types for &: Byte and {type(other)}")
        return Byte(self.value & other.value)

    def __or__(self, other):
        if not isinstance(other, Byte):
            raise RuntimeError(f"Unsupported operand types for |: Byte and {type(other)}")
        return Byte(self.value | other.value)

    def __not__(self):
        return Byte(self.value ^ 0xff)

    def __neg__(self):
        return Byte((self.value ^ 0xff) + 1)

    def __pos__(self):
        return Byte(self.value)

    def __eq__(self, other):
        if not isinstance(other, Byte):
            raise RuntimeError(f"Unsupported operand types for ==: Byte and {type(other)}")
        return Bool(self.value == other.value)

    def __ne__(self, other):
        if not isinstance(other, Byte):
            raise RuntimeError(f"Unsupported operand types for !=: Byte and {type(other)}")
        return Bool(self.value != other.value)

    def __lt__(self, other):
        if not isinstance(other, Byte):
            raise RuntimeError(f"Unsupported operand types for <: Byte and {type(other)}")
        return Bool(self.svalue < other.svalue)

    def __le__(self, other):
        if not isinstance(other, Byte):
            raise RuntimeError(f"Unsupported operand types for <=: Byte and {type(other)}")
        return Bool(self.svalue <= other.svalue)

    def __gt__(self, other):
        if not isinstance(other, Byte):
            raise RuntimeError(f"Unsupported operand types for >: Byte and {type(other)}")
        return Bool(self.svalue > other.svalue)

    def __ge__(self, other):
        if not isinstance(other, Byte):
            raise RuntimeError(f"Unsupported operand types for >=: Byte and {type(other)}")
        return Bool(self.svalue >= other.svalue)
