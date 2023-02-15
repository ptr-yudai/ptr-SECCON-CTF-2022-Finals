from interpreter.types.boolean import *
from interpreter.types.signed import *
from interpreter.types.unsigned import *

class ArrayRef(object):
    def __init__(self, array, index):
        self.array = array
        self.index = index

    def get(self):
        return self.array[self.index]

    def set(self, val):
        self.array[self.index] = val

class Array(object):
    def __init__(self, type, len, init=None):
        if len < 0 or len > 0x1000:
            raise RuntimeError("Array too big")
        self.type = type
        self.len = len
        self.data = [None if init is None else init.clone()
                     for i in range(self.len)]

    def call(self, *args):
        raise RuntimeError("Array is not callable")

    def cast_to(self, type):
        raise RuntimeError(f"Cannot cast Array to {type}")

    def clone(self):
        arr = Array(self.type, self.len)
        for i in range(self.len):
            arr[UInt(i)] = self.data[i].clone()
        return arr

    def __getitem__(self, idx):
        index = idx.cast_to(UInt)
        if index.value >= self.len:
            raise RuntimeError(f"Out-of-bounds read: (len={self.len}) <= (idx={index.value})")

        return self.data[index.value]

    def __setitem__(self, idx, val):
        if not isinstance(idx, Int) and not isinstance(idx, UInt):
            raise RuntimeError(f"Array indice must be of UInt type")

        idx = idx.cast_to(UInt)
        if idx.value >= self.len:
            raise RuntimeError(f"Out-of-bounds read: (len={self.len}) <= (idx={index.value})")

        if not isinstance(val, self.type):
            raise RuntimeError(f"Array type mismatch: {self.type}[] <-- {type(val)}")

        if isinstance(val, Array):
            raise RuntimeError("Multidimensional array is not supported")

        self.data[idx.value] = val

    def __add__(self, other):
        raise RuntimeError(f"Unsupported operator + for Array")

    def __sub__(self, other):
        raise RuntimeError(f"Unsupported operator - for Array")

    def __mul__(self, other):
        raise RuntimeError(f"Unsupported operator * for Array")

    def __mod__(self, other):
        raise RuntimeError(f"Unsupported operator % for Array")

    def __floordiv__(self, other):
        raise RuntimeError(f"Unsupported operator / for Array")

    def __lshift__(self, other):
        raise RuntimeError(f"Unsupported operator << for Array")

    def __rshift__(self, other):
        raise RuntimeError(f"Unsupported operator >> for Array")

    def __xor__(self, other):
        raise RuntimeError(f"Unsupported operator ^ for Array")

    def __and__(self, other):
        raise RuntimeError(f"Unsupported operator & for Array")

    def __or__(self, other):
        raise RuntimeError(f"Unsupported operator | for Array")

    def __not__(self):
        raise RuntimeError(f"Unsupported operator ! for Array")

    def __neg__(self):
        raise RuntimeError(f"Unsupported operator -(neg) for Array")

    def __pos__(self):
        raise RuntimeError(f"Unsupported operator +(pos) for Array")

    def __eq__(self, other):
        if not isinstance(other, Array):
            raise RuntimeError(f"Unsupported operand types for ==: Array and {type(other)}")
        return Bool(self.data == other.data)

    def __ne__(self, other):
        if not isinstance(other, Array):
            raise RuntimeError(f"Unsupported operand types for !=: Array and {type(other)}")
        return Bool(self.data != other.data)

    def __lt__(self, other):
        raise RuntimeError(f"Unsupported comparison operator < for Array")

    def __le__(self, other):
        raise RuntimeError(f"Unsupported comparison operator <= for Array")

    def __gt__(self, other):
        raise RuntimeError(f"Unsupported comparison operator > for Array")

    def __ge__(self, other):
        raise RuntimeError(f"Unsupported comparison operator >= for Array")
