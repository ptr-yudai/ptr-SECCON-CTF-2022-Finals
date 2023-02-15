import ast
import lark
import sys
from interpreter import *

sys.setrecursionlimit(65535)

def builtin_print(*args):
    arg = args[0]
    if isinstance(arg, Array):
        if arg.type != Byte: print('[', end='')
        for i, c in enumerate(arg.data):
            builtin_print(c)
            if arg.type != Byte and i != arg.len - 1: print(', ', end='')
        if arg.type != Byte: print(']', end='')

    elif isinstance(arg, Byte):
        print(chr(arg.value), end='')

    elif isinstance(arg, Int):
        if arg.value >= 1<<63:
            print(-((arg.value ^ ((1<<64)-1)) + 1), end='')
        else:
            print(arg.value, end='')

    elif isinstance(arg, UInt):
        print(arg.value, end='')

    elif isinstance(arg, Bool):
        if arg.value:
            print('true', end='')
        else:
            print('false', end='')

    elif isinstance(arg, Function):
        print('<function>', end='')

    elif arg == None:
        raise RuntimeError("Unreachable")

    else:
        raise NotImplementedError(f"builtin_print: {type(arg)}")

def builtin_scan(*args):
    try:
        return Int(int(input()))
    except:
        raise RuntimeError("Invalid input")

def builtin_exit(*args):
    arg = args[0]
    if isinstance(arg, UInt):
        sys.exit(arg.value)
    elif isinstance(arg, Int):
        sys.exit(arg.svalue)
    else:
        raise RuntimeError(f"Cannot pass {type(arg)} as status code")

class SecLangInterpreter(lark.visitors.Interpreter):
    def __init__(self):
        """Initialize interpreter
        """
        self.g = Scope()  # Global scope
        self.scope = None # Local scope
        # Builtin functions
        self.g.define('print',
                      Function(['value'], builtin_print, builtin=True))
        self.g.define('scan',
                      Function([], builtin_scan, builtin=True))
        self.g.define('exit',
                      Function(['status'], builtin_exit, builtin=True))

    def prog(self, tree):
        """Entry point
        """
        # Define all functions
        for func_decl in tree.children:
            self.visit(func_decl)

        # Call main function
        if not self.g.has('main'):
            raise RuntimeError("'main' function is not defined")
        else:
            self.g.get('main').call(self, [])

    def func_decl(self, tree):
        """Define function
        """
        func_name = self.visit(tree.children[0])
        stmt = tree.children[2]
        if tree.children[1] is None:
            param_list = []
        else:
            param_list = self.visit(tree.children[1])

        # Add this function to globals
        self.g.define(func_name, Function(param_list, stmt))

    def func_name(self, tree):
        """Function identifier
        """
        return tree.children[0].children[0]

    def param_list(self, tree):
        """Function arguments
        """
        params = []
        for param in tree.children:
            params.append(param.children[0])
        return params

    def stmt_list(self, tree):
        """Statements
        """
        r = None
        for stmt in tree.children:
            r = self.visit(stmt)
            if not self.scope.is_top_scope_active():
                break
        return r

    def assign_stmt(self, tree):
        """Assignment statement
        """
        val = self.visit(tree.children[1])
        if val is None:
            raise RuntimeError("Cannot assign void to variable")

        if tree.children[0].data == 'index_expr_ref':
            # x[y] = z
            arr = self.visit(tree.children[0])
            arr.set(val)
            return val
        else:
            # x = z
            var_name = tree.children[0].children[0]
            if not self.scope.has(var_name) \
               and (self.scope.top_scope != 0 or self.scope.in_branch()):
                raise RuntimeError("Cannot declare variable in if/while scope")

            self.scope.set(var_name, val)
            return self.scope.get(var_name)

    def if_stmt(self, tree):
        """Conditional branch
        """
        self.scope.enter_branch()
        if self.visit(tree.children[0]).cast_to(Bool).value == True:
            r = self.visit(tree.children[1]) # true-path
        elif tree.children[2] is not None:
            r = self.visit(tree.children[2]) # false-path
        else:
            r = None
        self.scope.exit_branch()
        return r

    def while_stmt(self, tree):
        """Loop
        """
        sid = self.scope.create_child_scope()
        r = None
        while self.scope.is_child_scope_active(sid) and \
              self.visit(tree.children[0]).cast_to(Bool).value == True:
            r = self.visit(tree.children[1])
        self.scope.destroy_child_scope(sid)
        return r

    def break_stmt(self, tree):
        """Break
        """
        if self.scope.break_scope() is False:
            raise RuntimeError("'break' outside loop")

    def return_stmt(self, tree):
        """Return statement
        """
        if len(tree.children) == 0:
            r = None
        else:
            r = self.visit(tree.children[0])

        if isinstance(r, Array):
            raise RuntimeError("Cannot return Array object out of scope")

        self.scope.return_function()
        return r

    def expr(self, tree):
        """Expression
        """
        return self.visit(tree.children[0])

    def or_or_expr(self, tree):
        """OR operator
        """
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            l = self.visit(tree.children[0])
            r = self.visit(tree.children[1])
            if l is None or r is None:
                raise RuntimeError(f"Cannot use || operator for void operand")
            return l.cast_to(Bool) | r.cast_to(Bool)

    def and_and_expr(self, tree):
        """AND operator
        """
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            l = self.visit(tree.children[0])
            r = self.visit(tree.children[1])
            if l is None or r is None:
                raise RuntimeError(f"Cannot use && operator for void operand")
            return l.cast_to(Bool) & r.cast_to(Bool)

    def or_expr(self, tree):
        """Logical OR operator
        """
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            l = self.visit(tree.children[0])
            r = self.visit(tree.children[1])
            if l is None or r is None:
                raise RuntimeError(f"Cannot use | operator for void operand")
            return l | r

    def xor_expr(self, tree):
        """Logical XOR operator
        """
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            l = self.visit(tree.children[0])
            r = self.visit(tree.children[1])
            if l is None or r is None:
                raise RuntimeError(f"Cannot use ^ operator for void operand")
            return l ^ r

    def and_expr(self, tree):
        """Logical AND operator
        """
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            l = self.visit(tree.children[0])
            r = self.visit(tree.children[1])
            if l is None or r is None:
                raise RuntimeError(f"Cannot use & operator for void operand")
            return l & r

    def cmp_expr(self, tree):
        """Comparison operator
        """
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            l = self.visit(tree.children[0])
            op = tree.children[1]
            r = self.visit(tree.children[2])
            if l is None or r is None:
                raise RuntimeError(f"Cannot use {op} operator for void operand")
            if op == '==':
                return l == r
            elif op == '!=':
                return l != r
            elif op == '>':
                return l >  r
            elif op == '>=':
                return l >= r
            elif op == '<':
                return l <  r
            elif op == '<=':
                return l <= r
            else:
                raise RuntimeError("Unreachable")

    def shift_expr(self, tree):
        """Shift operator
        """
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            l = self.visit(tree.children[0])
            op = tree.children[1]
            r = self.visit(tree.children[2])
            if l is None or r is None:
                raise RuntimeError(f"Cannot use {op} operator for void operand")
            if op == '<<':
                return l << r
            elif op == '>>':
                return l >> r
            else:
                raise RuntimeError("Unreachable")

    def add_expr(self, tree):
        """Add/Sub operator
        x+y, x-y
        """
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            l = self.visit(tree.children[0])
            op = tree.children[1]
            r = self.visit(tree.children[2])
            if l is None or r is None:
                raise RuntimeError(f"Cannot use {op} operator for void operand")
            if op == '+':
                return l + r
            elif op == '-':
                return l - r
            else:
                raise RuntimeError("Unreachable")

    def mul_expr(self, tree):
        """Mul/Div/Mod operator
        x*y, x/y, x%y
        """
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            l = self.visit(tree.children[0])
            op = tree.children[1]
            r = self.visit(tree.children[2])
            if l is None or r is None:
                raise RuntimeError(f"Cannot use {op} operator for void operand")
            if op == '*':
                return l * r
            elif op == '/':
                return l // r
            elif op == '%':
                return l % r
            else:
                raise RuntimeError("Unreachable")

    def unary_expr(self, tree):
        """Unary
        !x, +x, -x
        """
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            op = tree.children[0]
            r = self.visit(tree.children[1])
            if r is None:
                raise RuntimeError(f"Cannot use {op} operator for void operand")
            if op == '!':
                return r.__not__()
            elif op == '+':
                return +r
            elif op == '-':
                return -r
            else:
                raise RuntimeError("Unreachable")

    def cast_expr(self, tree):
        """Cast
        """
        l = self.visit(tree.children[0])
        t = tree.children[1].children[0]
        if l is None:
            raise RuntimeError("Cannot cast void")
        if t == 'uint':
            return l.cast_to(UInt)
        elif t == 'int':
            return l.cast_to(Int)
        elif t == 'byte':
            return l.cast_to(Byte)
        elif t == 'bool':
            return l.cast_to(Bool)
        else:
            raise RuntimeError("Unreachable")

    def index_expr(self, tree):
        """Array index
        """
        arr = self.visit(tree.children[0])
        idx = self.visit(tree.children[1])
        if not isinstance(arr, Array):
            raise RuntimeError(f"{type(arr)} object is not subscriptable")
        return arr[idx]

    def index_expr_ref(self, tree):
        """Array index reference
        """
        arr = self.visit(tree.children[0])
        idx = self.visit(tree.children[1])
        if not isinstance(arr, Array):
            raise RuntimeError(f"{type(arr)} object is not subscriptable")
        return ArrayRef(arr, idx)

    def call_expr(self, tree):
        """Function call
        """
        function = self.visit(tree.children[0])
        if tree.children[0].data == 'primary_expr':
            return function

        if tree.children[1] is None:
            argument = []
        else:
            argument = self.visit(tree.children[1])

        return function.call(self, argument)

    def argument(self, tree):
        return [self.visit(child) for child in tree.children]

    def primary_expr(self, tree):
        """Primary expression
        """
        return self.visit(tree.children[0])

    def number_literal(self, tree):
        """Number
        """
        s_num = tree.children[0]
        if s_num.startswith("0x") or s_num.startswith("-0x"):
            v = int(s_num, 16)
        else:
            v = int(s_num, 10)
        return Int(v)

    def string_literal(self, tree):
        """String
        """
        s = ast.literal_eval(tree.children[0].value)
        arr = Array(Byte, len(s))
        for i, c in enumerate(s):
            arr[UInt(i)] = Byte(ord(c))
        return arr

    def boolean_literal(self, tree):
        if tree.children[0] == "true":
            return Bool(True)
        else:
            return Bool(False)

    def array_literal(self, tree):
        """Construct array
        """
        if len(tree.children) == 1:
            # [a, b, c] format
            a = self.visit(tree.children[0])
            if len(a) == 0:
                raise RuntimeError("Empty array")
            else:
                r = Array(type(a[0]), len(a))
                for i, elem in enumerate(a):
                    r[UInt(i)] = elem
        else:
            # [x; n] format
            x = self.visit(tree.children[0])
            n = self.visit(tree.children[1]).cast_to(UInt)
            r = Array(type(x), n.value)
            for i in range(n.value):
                r[UInt(i)] = x.clone()
        return r

    def array_literal_values(self, tree):
        """Array values
        """
        return [self.visit(element) for i, element in enumerate(tree.children)]

    def ident(self, tree):
        """Get variable
        """
        var_name = tree.children[0]
        if self.scope.has(var_name):
            # Local variable
            return self.scope.get(var_name)

        elif self.g.has(var_name):
            # Global variable (function)
            return self.g.get(var_name)

        else:
            raise RuntimeError(f"Undefined variable: '{var_name}'")

if __name__ == '__main__':
    with open('seclang.lark') as f:
        grammar = f.read()

    if len(sys.argv) < 2:
        program = ''
        while True:
            l = sys.stdin.readline()
            if l == '' or l == '__SECLANG_EOF__\n':
                break
            program += l
    else:
        with open(sys.argv[1]) as f:
            program = f.read()

    parser = lark.Lark(grammar, start='prog', parser='lalr',
                       propagate_positions=True)
    tree = parser.parse(program)

    try:
        SecLangInterpreter().visit(tree)
    except RuntimeError as e:
        print("[RuntimeError]", e)
        sys.exit(1)
