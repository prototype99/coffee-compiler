import antlr4 as antlr
import os
from CoffeeLexer import CoffeeLexer
from CoffeeVisitor import CoffeeVisitor
from CoffeeParser import CoffeeParser
from CoffeeUtil import Var, Method, Import, Loop, SymbolTable


class CoffeeTreeVisitor(CoffeeVisitor):
    def __init__(self):
        self.stbl: SymbolTable = SymbolTable()
        self.data: str = '.data\n'
        self.body: str = '.text\n.global main\n'

    def visitBlock(self, ctx):
        line: int = ctx.start.line
        # check to see if a scope is pushed
        if ctx.LCURLY() is not None:
            self.stbl.pushScope()
        # go through the code
        self.visitChildren(ctx)
        if ctx.RCURLY() is not None:
            self.stbl.popScope()
        # braces should be matched
        elif ctx.LCURLY() is not None:
            print('error near line ' + str(line) + ': expected \'}\'')

    def visitExpr(self, ctx):
        if ctx.literal() is not None:
            return self.visit(ctx.literal())
        elif ctx.location() is not None:
            return self.visit(ctx.location())
        elif len(ctx.expr()) == 2:
            method_ctx = self.stbl.getMethodContext()
            expr0_type: str = self.visit(ctx.expr(0))
            method_ctx.body += 'movq %rax, %r10\n'
            expr1_type: str = self.visit(ctx.expr(1))
            method_ctx.body += 'movq %rax, %r11\n'
            if ctx.ADD() is not None:
                method_ctx.body += 'addq %r10, %r11\n'
            method_ctx.body += 'movq %r11, %rax\n'
            if expr0_type == 'float' or expr1_type == 'float':
                return 'float'
            if expr0_type == 'int' or expr1_type == 'int':
                return 'int'
            if expr0_type == 'bool' or expr1_type == 'bool':
                return 'bool'
        elif ctx.data_type() is not None:
            return ctx.data_type()
        else:
            return self.visitChildren(ctx)

    def visitGlobal_decl(self, ctx):
        line: int = ctx.start.line
        for i in range(len(ctx.var_decl().var_assign())):
            var_id: str = ctx.var_decl().var_assign(i).var().ID().getText()
            # handle arrays
            if ctx.var_decl().var_assign(i).var().INT_LIT() is not None:
                var_size: int = ctx.var_decl().var_assign(i).var().INT_LIT().getText() * 8
                # catch rule 14
                if int(var_size) == 0:
                    print('error on line ' + str(line) + ': global var array \'' + var_id + '\' has an illegal zero length')
                var_array: bool = True
            else:
                var_size: int = 8
                var_array: bool = False
            var: Var = self.stbl.find(var_id)
            if var is not None:
                print('error on line ' + str(line) + ': global var \'' + var_id + '\' already declared on line ' + str(var.line))
            var: Var = Var(var_id,
                           ctx.var_decl().data_type().getText(),
                           var_size,
                           Var.GLOBAL,
                           var_array,
                           line)
            self.stbl.pushVar(var)

    def visitLiteral(self, ctx):
        if ctx.bool_lit() is not None:
            return 'bool'
        if ctx.INT_LIT() is not None:
            method_ctx = self.stbl.getMethodContext()
            method_ctx.body += 'movq $' + ctx.getText() + ', %rax\n'
            return 'int'
        if ctx.CHAR_LIT() is not None:
            return 'char'
        if ctx.FLOAT_LIT() is not None:
            return 'float'
        if ctx.STRING_LIT() is not None:
            return 'string'

    def visitLocation(self, ctx):
        loc: Var = self.stbl.find(ctx.ID().getText())
        if loc is not None:
            if loc.scope == Var.GLOBAL:
                pass
            elif loc.scope == Var.LOCAL:
                method_ctx = self.stbl.getMethodContext()
                method_ctx.body += 'movq ' + str(loc.addr) + '(%rbp), %rax\n'
            return loc.data_type

    def visitMethod_call(self, ctx):
        method_ctx = self.stbl.getMethodContext()

        for i in range(len(ctx.expr())):
            self.visit(ctx.expr(i))
            method_ctx.body += 'movq %rax, %rdi\n'
        method_ctx.body += 'addq $' + str(self.stbl.getStackPtr()) + ', %rsp\n'
        method_ctx.body += 'call ' + str(ctx.ID()) + '\n'
        method_ctx.body += 'subq $' + str(self.stbl.getStackPtr()) + ', %rsp\n'

    def visitMethod_decl(self, ctx):
        line: int = ctx.start.line
        method_id: str = ctx.ID().getText()
        method_type: str = ctx.return_type().getText()
        method: Method = self.stbl.find(method_id)
        if method is not None:
            print('error on line ' + str(line) + ': method \'' + method_id + '\' already declared on line ' + str(method.line) + '. this declaration will be ignored')
        else:
            method: Method = Method(method_id, method_type, line)
            self.stbl.pushMethod(method)
            self.stbl.pushFrame(method)
            method.body += method.id + ':\n'
            method.body += 'push %rbp\n'
            method.body += 'movq %rsp, %rbp\n'
            for i in range(len(ctx.param())):
                param_id: str = ctx.param(i).ID().getText()
                param_type: str = ctx.param(i).data_type().getText()
                param_size: int = 8
                param_array: bool = False
                param: Var = self.stbl.peek(param_id)
                if param is not None:
                    print('error on line ' + str(line) + ': param \'' + param_id + '\' already declared on line ' + str(param.line))
                else:
                    method.pushParam(param_type)
                    param: Var = Var(param_id,
                                     param_type,
                                     param_size,
                                     Var.LOCAL,
                                     param_array,
                                     line)
                    self.stbl.pushVar(param)
                    method.body += 'movq ' + self.stbl.param_reg[i] + ', ' + str(param.addr) + '(%rbp)\n'
            if ctx.block() is not None:
                self.visit(ctx.block())
            else:
                self.visit(ctx.expr())
            if not method.has_return:
                method.body += 'pop %rbp\n'
                method.body += 'ret\n'
            self.data += method.data
            self.body += method.body
            self.stbl.popFrame()

    # starting point
    def visitProgram(self, ctx):
        # main method should push an int
        method = Method('main', 'int', ctx.start.line)
        # create new stack frame
        self.stbl.pushFrame(method)
        # push the method to the symbol table
        self.stbl.pushMethod(method)
        method.body += method.id + ':\n'
        method.body += 'push %rbp\n'
        method.body += 'movq %rsp, %rbp\n'
        self.visitChildren(ctx)
        if not method.has_return:
            method.body += 'pop %rbp\n'
            method.body += 'ret\n'
        self.data += method.data
        self.body += method.body
        self.stbl.popFrame()

    def visitVar_decl(self, ctx):
        line: int = ctx.start.line
        for i in range(len(ctx.var_assign())):
            var_id: str = ctx.var_assign(i).var().ID().getText()
            var_size: int = 8
            var_array: bool = False
            var: Var = self.stbl.peek(var_id)
            if var is not None:
                print('error on line ' + str(line) + ': var \'' + var_id + '\' already declared on line ' + str(
                    var.line) + ' in same scope')
            var: Var = Var(var_id,
                           ctx.data_type().getText(),
                           var_size,
                           Var.GLOBAL,
                           var_array,
                           line)
            self.stbl.pushVar(var)


# load base test file
filein = open('./test.coffee', 'r')
# read whatever file was enabled
source_code = filein.read()
filein.close()

# create a token stream from source code
lexer = CoffeeLexer(antlr.InputStream(source_code))
stream = antlr.CommonTokenStream(lexer)

# parse token stream
parser = CoffeeParser(stream)
tree = parser.program()

# create Coffee Visitor object
visitor = CoffeeTreeVisitor()

# visit nodes from tree root
visitor.visit(tree)

# print assembly output code
code = visitor.data + visitor.body
print(code)

# save the assembly file to a.s
fileout = open('a.s', 'w')
fileout.write(code)
fileout.close()

# assemble and link via gcc
os.system("gcc a.s -lm ; ./a.out ; echo $?")
