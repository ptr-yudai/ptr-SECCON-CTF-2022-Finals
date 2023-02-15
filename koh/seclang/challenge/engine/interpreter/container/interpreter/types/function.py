from interpreter.scope import *
from interpreter.types.boolean import Bool

class Function(object):
    def __init__(self, param_list, stmt_or_func, builtin=False):
        self.param_list = tuple(param_list)
        self.builtin = builtin
        if builtin:
            self.func = stmt_or_func
        else:
            self.stmt = stmt_or_func

    def cast_to(self, type):
        raise RuntimeError(f"Cannot cast Function to {type}")

    def clone(self):
        if self.builtin:
            return Function(self.param_list, self.func, self.builtin)
        else:
            return Function(self.param_list, self.stmt, self.builtin)

    def __add__(self, other):
        raise RuntimeError(f"Unsupported operator + for Function")

    def __sub__(self, other):
        raise RuntimeError(f"Unsupported operator - for Function")

    def __mul__(self, other):
        raise RuntimeError(f"Unsupported operator * for Function")

    def __mod__(self, other):
        raise RuntimeError(f"Unsupported operator % for Function")

    def __floordiv__(self, other):
        raise RuntimeError(f"Unsupported operator / for Function")

    def __lshift__(self, other):
        raise RuntimeError(f"Unsupported operator << for Function")

    def __rshift__(self, other):
        raise RuntimeError(f"Unsupported operator >> for Function")

    def __xor__(self, other):
        raise RuntimeError(f"Unsupported operator ^ for Function")

    def __and__(self, other):
        raise RuntimeError(f"Unsupported operator & for Function")

    def __or__(self, other):
        raise RuntimeError(f"Unsupported operator | for Function")

    def __not__(self):
        raise RuntimeError(f"Unsupported operator ! for Function")

    def __neg__(self):
        raise RuntimeError(f"Unsupported operator -(neg) for Function")

    def __pos__(self):
        raise RuntimeError(f"Unsupported operator +(pos) for Function")

    def __eq__(self, other):
        if not isinstance(other, Function):
            raise RuntimeError(f"Unsupported operand types for ==: Function and {type(other)}")

        if self.builtin != other.builtin:
            return Bool(False)

        if self.builtin:
            return Bool(self.func == other.func)
        else:
            return Bool(self.stmt == other.stmt)

    def __ne__(self, other):
        if not isinstance(other, Function):
            raise RuntimeError(f"Unsupported operand types for !=: Function and {type(other)}")

        if self.builtin != other.builtin:
            return Bool(True)

        if self.builtin:
            return Bool(self.func != other.func)
        else:
            return Bool(self.stmt != other.stmt)

    def __lt__(self, other):
        raise RuntimeError(f"Unsupported comparison operator < for Function")

    def __le__(self, other):
        raise RuntimeError(f"Unsupported comparison operator <= for Function")

    def __gt__(self, other):
        raise RuntimeError(f"Unsupported comparison operator > for Function")

    def __ge__(self, other):
        raise RuntimeError(f"Unsupported comparison operator >= for Function")

    @property
    def n_params(self):
        return len(self.param_list)

    def call(self, visitor, args):
        """Call this function
        """
        if len(args) != self.n_params:
            raise RuntimeError(f"Function takes {self.n_params} arguments but {len(args)} were given")

        if self.builtin:
            # Builtin function
            retval = self.func(*args)
        else:
            # User-defined function
            old_scope = visitor.scope
            new_scope = Scope()

            # Prepare arguments
            for param, arg in zip(self.param_list, args):
                new_scope.define(param, arg)

            visitor.scope = new_scope
            retval = visitor.visit(self.stmt)
            visitor.scope = old_scope

        return retval
