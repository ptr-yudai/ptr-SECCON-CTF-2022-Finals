import ast
import lark
import sys

sys.setrecursionlimit(4096)

TYPE_FUNC  = 0
TYPE_ARRAY = 1
TYPE_BOOL  = 2
TYPE_BYTE  = 3
TYPE_UINT  = 4
TYPE_INT   = 5

def emit_builtin_print(code):
    code.text([open("builtin/print.asm").read()])

def emit_builtin_scan(code):
    code.text([open("builtin/scan.asm").read()])

def emit_builtin_exit(code):
    code.text([open("builtin/exit.asm").read()])

class CompileError(Exception):
    pass

class Code(object):
    def __init__(self):
        self._text = ["section .text"]
        self._data = ["section .data"]
        self._label_num = 0

        # Entry point
        self.text(["global _start",
                   "_start:",
                   "call main",
                   "push rdx",
                   "push rax",
                   "call exit"])

    def __str__(self):
        return '\n'.join(self._text) + '\n' + '\n'.join(self._data)

    def label(self, is_global=False):
        self._label_num += 1
        if is_global:
            return f'L{self._label_num}'
        else:
            return f'.@L{self._label_num}'

    def text(self, code):
        self._text += code

    def data(self, data):
        self._data += data

    def pop_value(self, regval=None, regtype=None):
        if regval is None and regtype is None:
            self._text += ["add rsp, 0x10"]
        elif regtype is None:
            self._text += [f"pop {regval}", "add rsp, 8"]
        elif regval is None:
            self._text += ["add rsp, 8", f"pop {regtype}"]
        else:
            self._text += [f"pop {regval}", f"pop {regtype}"]

    def push_value(self, regval, regtype):
        self._text += [f"push {regtype}", f"push {regval}"]

class SecLangCompiler(lark.visitors.Interpreter):
    def __init__(self):
        """Initialize interpreter
        """
        self.g = {'print', 'scan', 'exit'} # Function names
        self.scope = {} # Variables in current scope
        self.break_labels = [] # Where break should jump
        self.varnum = 0
        self.code = Code()
        emit_builtin_print(self.code)
        emit_builtin_scan(self.code)
        emit_builtin_exit(self.code)

    def prog(self, tree):
        """Entry point
        """
        # Define all functions
        for func_decl in tree.children:
            func_name = self.visit(func_decl.children[0])
            if func_name in self.g:
                raise CompileError(f"Second definition of '{func_name}'")
            self.g.add(func_name)

        # Compile each function
        for func_decl in tree.children:
            self.visit(func_decl)

    def func_decl(self, tree):
        """Define function
        """
        func_name = self.visit(tree.children[0])
        self.code.text([f'{func_name}:',
                        f'push rbp',
                        f'mov rbp, rsp'])

        last_scope, self.scope = self.scope, {}
        last_break, self.break_labels = self.break_labels, []
        last_varnum, self.varnum = self.varnum, 0

        param_list = self.visit(tree.children[1])
        for i, param in enumerate(param_list):
            self.scope[param] = - (i + 1) * 0x10

        self.visit(tree.children[2])
        self.code.pop_value('rax', 'rdx') # return void (not used)
        if self.varnum > 0:
            self.code.text([f"add rsp, {0x10*self.varnum}"])
        self.code.text(["pop rbp", "ret"])

        self.scope, self.break_labels, self.varnum \
            = last_scope, last_break, last_varnum

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
        for stmt in tree.children:
            self.visit(stmt)
            self.code.pop_value() # discard stmt result

        # leave nothing
        self.code.text([f"mov rdx, {TYPE_INT}",
                        "xor eax, eax"])
        self.code.push_value('rax', 'rdx')

    def assign_stmt(self, tree):
        """Assignment statement
        """
        if tree.children[0].data == 'index_expr_ref':
            # x[y] = z
            self.visit(tree.children[1])
            self.visit(tree.children[0])
            self.code.pop_value('rdi')
            self.code.pop_value('rax', 'rdx')

            self.code.text(["mov [rdi], rax"])
            self.code.push_value('rax', 'rdx')

        else:
            # x = z
            var_name = tree.children[0].children[0]
            if var_name not in self.scope:
                self.scope[var_name] = self.varnum * 0x10
                self.varnum += 1
                self.code.text(["sub rsp, 0x10"])

            self.visit(tree.children[1])
            self.code.pop_value("rax", "rdx")
            ofs = self.scope[var_name]
            if ofs < 0:
                self.code.text([f"mov [rbp+{-ofs}], rax",
                                f"mov [rbp+{-ofs+8}], rdx"])
            else:
                self.code.text([f"mov [rbp-{ofs+0x08}], rax",
                                f"mov [rbp-{ofs+0x10}], rdx"])

            self.code.push_value('rax', 'rdx')

    def if_stmt(self, tree):
        """Conditional branch
        """
        l1, l2 = self.code.label(), self.code.label()
        self.visit(tree.children[0])

        self.code.pop_value('rax')
        self.code.text(["test rax, rax",
                        f"jz {l1}"])
        # true-path
        self.visit(tree.children[1])
        self.code.pop_value() # discard stmt result
        self.code.text([f"jmp {l2}",
                        f"{l1}:"])

        if tree.children[2] is not None:
            # false-path
            self.visit(tree.children[2])
            self.code.pop_value() # discard stmt result
        self.code.text([f"{l2}:"])

        # leave nothing
        self.code.text([f"mov rdx, {TYPE_INT}",
                        "xor eax, eax"])
        self.code.push_value('rax', 'rdx')

    def while_stmt(self, tree):
        """Loop
        """
        l1, l2 = self.code.label(), self.code.label()
        self.break_labels.append(l2)

        self.code.text([f"{l1}:"])
        self.visit(tree.children[0])
        self.code.pop_value('rax')
        self.code.text(["test rax, rax",
                        f"jz {l2}"])

        self.visit(tree.children[1])
        self.code.pop_value() # discard

        self.code.text([f"jmp {l1}",
                        f"{l2}:"])

        # leave nothing
        self.code.text([f"mov rdx, {TYPE_INT}",
                        "xor eax, eax"])
        self.code.push_value('rax', 'rdx')
        self.break_labels.pop()

    def break_stmt(self, tree):
        """Break
        """
        if len(self.break_labels) == 0:
            raise CompileError("'break' outside loop")
        self.code.text([f"jmp {self.break_labels[-1]}"])

    def return_stmt(self, tree):
        """Return statement
        """
        if len(tree.children) == 0:
            self.code.text([f"mov rdx, {TYPE_INT}",
                            "xor eax, eax"])
        else:
            self.visit(tree.children[0])
            self.code.pop_value("rax", "rdx")
            if self.varnum > 0:
                self.code.text([f"add rsp, {0x10*self.varnum}"])

        self.code.text(["pop rbp", "ret"])

    def expr(self, tree):
        """Expression
        """
        self.visit(tree.children[0])

    def or_or_expr(self, tree):
        """OR operator
        """
        if len(tree.children) == 1:
            self.visit(tree.children[0])
        else:
            self.visit(tree.children[0])
            self.visit(tree.children[1])
            self.code.pop_value('rdx')
            self.code.pop_value('rax')
            self.code.text(["or rax, rdx",
                            "test rax, rax",
                            "setnz al",
                            "movzx rax, al",
                            f"mov ebx, {TYPE_BOOL}"])
            self.code.push_value("rax", "rbx")

    def and_and_expr(self, tree):
        """AND operator
        """
        if len(tree.children) == 1:
            self.visit(tree.children[0])
        else:
            self.visit(tree.children[0])
            self.visit(tree.children[1])
            self.code.pop_value('rdx')
            self.code.pop_value('rax')
            self.code.text(["and rax, rdx",
                            "test rax, rax",
                            "setnz al",
                            "movzx rax, al",
                            f"mov ebx, {TYPE_BOOL}"])
            self.code.push_value("rax", "rbx")

    def or_expr(self, tree):
        """Logical OR operator
        """
        if len(tree.children) == 1:
            self.visit(tree.children[0])
        else:
            self.visit(tree.children[0])
            self.visit(tree.children[1])
            self.code.pop_value('rdx', 'rbx')
            self.code.pop_value('rax')
            self.code.text(["or rax, rdx"])
            self.code.push_value("rax", "rbx")

    def xor_expr(self, tree):
        """Logical XOR operator
        """
        if len(tree.children) == 1:
            self.visit(tree.children[0])
        else:
            self.visit(tree.children[0])
            self.visit(tree.children[1])
            self.code.pop_value('rdx', 'rbx')
            self.code.pop_value('rax')
            self.code.text(["xor rax, rdx"])
            self.code.push_value("rax", "rbx")

    def and_expr(self, tree):
        """Logical AND operator
        """
        if len(tree.children) == 1:
            self.visit(tree.children[0])
        else:
            self.visit(tree.children[0])
            self.visit(tree.children[1])
            self.code.pop_value('rdx', 'rbx')
            self.code.pop_value('rax')
            self.code.text(["and rax, rdx"])
            self.code.push_value("rax", "rbx")

    def cmp_expr(self, tree):
        """Comparison operator
        """
        if len(tree.children) == 1:
            self.visit(tree.children[0])
        else:
            self.visit(tree.children[0])
            op = tree.children[1]
            self.visit(tree.children[2])
            self.code.pop_value('rdx', 'rbx')
            self.code.pop_value('rax')

            if op == '==':
                self.code.text(["cmp rax, rdx",
                                "setz al"])
            elif op == '!=':
                self.code.text(["cmp rax, rdx",
                                "setnz al"])
            elif op == '>':
                l1, l2 = self.code.label(), self.code.label()
                self.code.text([f"cmp bl, {TYPE_INT}",
                                f"jz {l1}",
                                "cmp rax, rdx",
                                "seta al",
                                f"jmp {l2}",
                                f"{l1}:",
                                "cmp rax, rdx",
                                "setg al",
                                f"{l2}:"])
            elif op == '>=':
                l1, l2 = self.code.label(), self.code.label()
                self.code.text([f"cmp bl, {TYPE_INT}",
                                f"jz {l1}",
                                "cmp rax, rdx",
                                "setae al",
                                f"jmp {l2}",
                                f"{l1}:",
                                "cmp rax, rdx",
                                "setge al",
                                f"{l2}:"])
            elif op == '<':
                l1, l2 = self.code.label(), self.code.label()
                self.code.text([f"cmp bl, {TYPE_INT}",
                                f"jz {l1}",
                                "cmp rax, rdx",
                                "setb al",
                                f"jmp {l2}",
                                f"{l1}:",
                                "cmp rax, rdx",
                                "setl al",
                                f"{l2}:"])
            elif op == '<=':
                l1, l2 = self.code.label(), self.code.label()
                self.code.text([f"cmp bl, {TYPE_INT}",
                                f"jz {l1}",
                                "cmp rax, rdx",
                                "setbe al",
                                f"jmp {l2}",
                                f"{l1}:",
                                "cmp rax, rdx",
                                "setle al",
                                f"{l2}:"])
            else:
                raise CompileError("Unreachable")

            self.code.text(["movzx rax, al",
                            f"push {TYPE_BOOL}",
                            "push rax"])

    def shift_expr(self, tree):
        """Shift operator
        """
        if len(tree.children) == 1:
            self.visit(tree.children[0])
        else:
            self.visit(tree.children[0])
            op = tree.children[1]
            self.visit(tree.children[2])
            self.code.pop_value('rcx', 'rbx')
            self.code.pop_value('rax')
            if op == '<<':
                self.code.text(["shl rax, cl"])
            elif op == '>>':
                l1, l2 = self.code.label(), self.code.label()
                self.code.text([f"cmp bl, {TYPE_INT}",
                                f"jz {l1}",
                                "shr rax, cl",
                                f"jmp {l2}",
                                f"{l1}:",
                                "sar rax, cl",
                                f"{l2}:"])
            else:
                raise CompileError("Unreachable")
            self.code.push_value("rax", "rbx")

    def add_expr(self, tree):
        """Add/Sub operator
        x+y, x-y
        """
        if len(tree.children) == 1:
            self.visit(tree.children[0])
        else:
            self.visit(tree.children[0])
            op = tree.children[1]
            self.visit(tree.children[2])
            self.code.pop_value('rdx', 'rbx')
            self.code.pop_value('rax')
            if op == '+':
                self.code.text(["add rax, rdx"])
            elif op == '-':
                self.code.text(["sub rax, rdx"])
            else:
                raise CompileError("Unreachable")
            self.code.push_value('rax', 'rbx')

    def mul_expr(self, tree):
        """Mul/Div/Mod operator
        x*y, x/y, x%y
        """
        if len(tree.children) == 1:
            self.visit(tree.children[0])
        else:
            self.visit(tree.children[0])
            op = tree.children[1]
            self.visit(tree.children[2])
            self.code.pop_value('rcx', 'rbx')
            self.code.pop_value('rax')

            if op == '*':
                self.code.text(["xor edx, edx",
                                "mul rcx"])
            elif op == '/':
                l1, l2 = self.code.label(), self.code.label()
                self.code.text([f"cmp bl, {TYPE_INT}",
                                f"jz {l1}",
                                "xor edx, edx",
                                "div rcx",
                                f"jmp {l2}",
                                f"{l1}:",
                                "cqo",
                                "idiv rcx",
                                f"{l2}:"])
            elif op == '%':
                l1, l2 = self.code.label(), self.code.label()
                self.code.text([f"cmp bl, {TYPE_INT}",
                                f"jz {l1}",
                                "xor edx, edx",
                                "div rcx",
                                "mov rax, rdx",
                                f"jmp {l2}",
                                f"{l1}:",
                                "cqo",
                                "idiv rcx",
                                "mov rax, rdx",
                                f"{l2}:"])
            else:
                raise CompileError("Unreachable")

            self.code.push_value('rax', 'rbx')

    def unary_expr(self, tree):
        """Unary
        !x, +x, -x
        """
        if len(tree.children) == 1:
            self.visit(tree.children[0])
        else:
            op = tree.children[0]
            self.visit(tree.children[1])
            self.code.pop_value('rax', 'rbx')
            if op == '!':
                self.code.text(["not rax"])
            elif op == '+':
                self.code.text(["nop"])
            elif op == '-':
                self.code.text(["neg rax"])
            else:
                raise CompileError("Unreachable")
            self.code.push_value('rax', 'rbx')

    def cast_expr(self, tree):
        """Cast
        """
        self.visit(tree.children[0])
        self.code.pop_value('rax')

        t = tree.children[1].children[0]
        if t == 'uint':
            self.code.text([f"push {TYPE_UINT}",
                            "push rax"])
        elif t == 'int':
            self.code.text([f"push {TYPE_INT}",
                            "push rax"])
        elif t == 'byte':
            self.code.text(["movzx rax, al",
                            f"push {TYPE_BYTE}",
                            "push rax"])
        elif t == 'bool':
            self.code.text(["test rax, rax",
                            "setnz al",
                            "movzx rax, al",
                            f"push {TYPE_BOOL}",
                            "push rax"])
        else:
            raise CompileError("Unreachable")

    def index_expr(self, tree):
        """Array index
        """
        self.visit(tree.children[0]) # arr
        self.visit(tree.children[1]) # idx
        self.code.pop_value('rdx')
        self.code.pop_value('rsi')

        self.code.text(['mov rax, [rsi+rdx*8+0x10]',
                        'mov rdx, [rsi]'])
        self.code.push_value('rax', 'rdx')

    def index_expr_ref(self, tree):
        """Array index reference
        """
        self.visit(tree.children[0]) # arr
        self.visit(tree.children[1]) # idx
        self.code.pop_value('rdx')
        self.code.pop_value('rsi')

        self.code.text(['lea rax, [rsi+rdx*8+0x10]',
                        'mov rdx, [rsi]'])
        self.code.push_value('rax', 'rdx')

    def call_expr(self, tree):
        """Function call
        """
        if tree.children[0].data == 'primary_expr':
            self.visit(tree.children[0])
            return

        # Resolve function pointer
        self.visit(tree.children[0])

        # Push arguments to stack
        if len(tree.children) > 1:
            n_args = self.visit(tree.children[1])

        # Get saved function pointer
        self.code.text([f"add rsp, {n_args*0x10}"])
        self.code.pop_value("rax")
        self.code.text([f"sub rsp, {0x10+n_args*0x10}"])
        self.code.text(["call rax"])
        # Skip saved function pointer and arguments
        self.code.text([f"add rsp, {0x10+n_args*0x10}"])

        self.code.push_value('rax', 'rdx')

    def argument(self, tree):
        for arg in tree.children[::-1]:
            self.visit(arg)
        return len(tree.children)

    def primary_expr(self, tree):
        """Primary expression
        """
        self.visit(tree.children[0])

    def number_literal(self, tree):
        """Number
        """
        s_num = tree.children[0]
        if s_num.startswith("0x") or s_num.startswith("-0x"):
            v = int(s_num, 16)
        else:
            v = int(s_num, 10)
        self.code.text([f"push {TYPE_INT}",
                        f"mov rax, {v}",
                        "push rax"])

    def string_literal(self, tree):
        """String
        """
        l = self.code.label(True)
        s = ast.literal_eval(tree.children[0].value)

        self.code.data([f"{l}:",
                        f"dq {TYPE_BYTE}, {len(s)}"])
        for c in s:
            self.code.data([f"dq {ord(c)}"])

        self.code.text([f"push {TYPE_ARRAY}",
                        f"lea rax, [{l}]",
                        f"push rax"])

    def boolean_literal(self, tree):
        if tree.children[0] == "true":
            self.code.text([f"push {TYPE_BOOL}",
                            "push 1"])
        else:
            self.code.text([f"push {TYPE_BOOL}",
                            "push 0"])

    def array_literal(self, tree):
        """Construct array
        """
        if len(tree.children) == 1:
            # [a, b, c] format
            self.visit(tree.children[0])

        else:
            # [x; n] format
            s_num = tree.children[1].children[0]
            if s_num.startswith("0x"):
                n = int(s_num, 16)
            else:
                n = int(s_num, 10)

            if n <= 0 or n > 0x1000:
                raise CompileError(f"Invalid array size: {n}")

            self.varnum += 1 + (n+1)//2
            self.code.text([f"sub rsp, {0x10 + (n+1)//2*0x10}",
                            f"mov dword [rsp+8], {n}"])

            self.visit(tree.children[0])
            self.code.pop_value('rax', 'rdx')
            self.code.text(["mov [rsp], rdx",
                            f"mov ecx, {n}",
                            "lea rdi, [rsp+0x10]",
                            "cld",
                            "repne stosq",
                            "mov rax, rsp",
                            f"push {TYPE_ARRAY}",
                            "push rax"])

    def array_literal_values(self, tree):
        """Array values
        """
        n = len(tree.children)

        self.varnum += 1 + (n+1)//2
        self.code.text([f"sub rsp, {0x10 + (n+1)//2*0x10}",
                        f"mov dword [rsp+8], {n}"])

        for i, element in enumerate(tree.children):
            self.visit(element)
            self.code.pop_value('rax', 'rdx')
            self.code.text([f"mov [rsp+{i*8+0x10}], rax"])

        self.code.text(["mov [rsp], rdx",
                        "mov rax, rsp",
                        f"push {TYPE_ARRAY}",
                        "push rax"])

    def ident(self, tree):
        """Get variable
        """
        var_name = tree.children[0]
        if var_name in self.scope:
            # Local variable
            ofs = self.scope[var_name]
            if ofs < 0:
                self.code.text([f"mov rax, [rbp+{-ofs}]",
                                f"mov rdx, [rbp+{-ofs+8}]"])
            else:
                self.code.text([f"mov rax, [rbp-{ofs+0x08}]",
                                f"mov rdx, [rbp-{ofs+0x10}]"])
            self.code.push_value('rax', 'rdx')

        elif var_name in self.g:
            # Global variable (function)
            self.code.text([f"push {TYPE_FUNC}",
                            f"lea rax, [{var_name}]",
                            "push rax"])

        else:
            raise CompileError(f"Undefined variable: '{var_name}'")

    def __str__(self):
        return str(self.code)

def compile_program(program: str):
    """Compile seclang program to assembly code

    This function is called by tester.
    You can modify the behavior but do not remove or rename this function.

    Args:
      program (str): Seclang program to compile.

    Returns:
      str: Assembly code compatible with GCC 10.
    """
    with open('seclang.lark') as f:
        grammar = f.read()

    parser = lark.Lark(grammar, start='prog', parser='lalr',
                       propagate_positions=True)
    tree = parser.parse(program)

    c = SecLangCompiler()
    c.visit(tree)
    return str(c)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} sample.sec")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        program = f.read()

    try:
        print(compile_program(program))
    except CompileError as e:
        print("[CompileError]", e)
        sys.exit(1)
