class Bool(object):
    def __init__(self, value):
        assert isinstance(value, bool)
        self.value = value

    def call(self, *args):
        raise RuntimeError("Bool is not callable")

    def cast_to(self, type):
        if type == Bool:
            return self
        else:
            raise RuntimeError(f"Cannot cast Bool to {type}")

    def clone(self):
        return Bool(self.value)

    def __add__(self, other):
        raise RuntimeError(f"Unsupported operator + for Bool")

    def __sub__(self, other):
        raise RuntimeError(f"Unsupported operator - for Bool")

    def __mul__(self, other):
        raise RuntimeError(f"Unsupported operator * for Bool")

    def __mod__(self, other):
        raise RuntimeError(f"Unsupported operator % for Bool")

    def __floordiv__(self, other):
        raise RuntimeError(f"Unsupported operator / for Bool")

    def __lshift__(self, other):
        raise RuntimeError(f"Unsupported operator << for Bool")

    def __rshift__(self, other):
        raise RuntimeError(f"Unsupported operator >> for Bool")

    def __xor__(self, other):
        if not isinstance(other, Bool):
            raise RuntimeError(f"Unsupported operand types for ^: Bool and {type(other)}")
        return Bool(self.value ^ other.value)

    def __and__(self, other):
        if not isinstance(other, Bool):
            raise RuntimeError(f"Unsupported operand types for &: Bool and {type(other)}")
        return Bool(self.value and other.value)

    def __or__(self, other):
        if not isinstance(other, Bool):
            raise RuntimeError(f"Unsupported operand types for |: Bool and {type(other)}")
        return Bool(self.value or other.value)

    def __not__(self):
        return Bool(not self.value)

    def __neg__(self):
        raise RuntimeError(f"Unsupported operator -(neg) for Bool")

    def __pos__(self):
        raise RuntimeError(f"Unsupported operator +(pos) for Bool")

    def __eq__(self, other):
        if not isinstance(other, Bool):
            raise RuntimeError(f"Unsupported operand types for ==: Bool and {type(other)}")
        return Bool(self.value == other.value)

    def __ne__(self, other):
        if not isinstance(other, Bool):
            raise RuntimeError(f"Unsupported operand types for !=: Bool and {type(other)}")
        return Bool(self.value != other.value)

    def __lt__(self, other):
        raise RuntimeError(f"Unsupported comparison operator < for Bool")

    def __le__(self, other):
        raise RuntimeError(f"Unsupported comparison operator <= for Bool")

    def __gt__(self, other):
        raise RuntimeError(f"Unsupported comparison operator > for Bool")

    def __ge__(self, other):
        raise RuntimeError(f"Unsupported comparison operator >= for Bool")
