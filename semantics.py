# for coursework raise exceptions rather than trying to recover from errors!
import antlr4 as antlr
import os
from CoffeeLexer import CoffeeLexer
from CoffeeVisitor import CoffeeVisitor
from CoffeeParser import CoffeeParser
from CoffeeUtil import Var, Method, Import, Loop, SymbolTable


class CoffeeTreeVisitor(CoffeeVisitor):
    def __init__(self):
        self.stbl = SymbolTable()
        self.data = '.data\n'
        self.body = '.text\n.global main\n'

    def visitProgram(self, ctx):
        method = Method('main', 'int', ctx.start.line)
        self.stbl.pushFrame(method)
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

    def visitBlock(self, ctx):
        if ctx.LCURLY() is not None:
            self.stbl.pushScope()

        self.visitChildren(ctx)

        if ctx.LCURLY() is not None:
            self.stbl.popScope()

    def visitGlobal_decl(self, ctx):
        line = ctx.start.line
        var_type = ctx.var_decl().data_type().getText()
        for i in range(len(ctx.var_decl().var_assign())):
            var_id = ctx.var_decl().var_assign(i).var().ID().getText()
            var_size = 8
            var_array = False

            var = self.stbl.peek(var_id)
            if var is not None:
                print('error on line ' + str(line) + ': global var \'' + var_id + '\' already declared on line ' + str(var.line))

            # checking for arrays
            if ctx.var_decl().var_assign(i).var().INT_LIT() is not None:
                var_size = ctx.var_decl().var_assign(i).var().INT_LIT().getText() * 8
                if int(var_size) == 0:
                    print('error on line ' + str(line) + ': global var array \'' + var_id + '\' has an illegal zero length')
                var_array = True

            var = Var(var_id,
                      var_type,
                      var_size,
                      Var.GLOBAL,
                      var_array,
                      line)
            self.stbl.pushVar(var)

    def visitVar_decl(self, ctx):
        line = ctx.start.line
        var_type = ctx.data_type().getText()
        for i in range(len(ctx.var_assign())):
            var_id = ctx.var_assign(i).var().ID().getText()
            var_size = 8
            var_array = False

            var = self.stbl.peek(var_id)
            if var is not None:
                print('error on line ' + str(line) + ': var \'' + var_id + '\' already declared on line ' + str(
                    var.line) + ' in same scope')

            var = Var(var_id,
                      var_type,
                      var_size,
                      Var.GLOBAL,
                      var_array,
                      line)
            self.stbl.pushVar(var)

    def visitMethod_decl(self, ctx):
        line = ctx.start.line
        method_id = ctx.ID().getText()
        method_type = ctx.return_type().getText()
        method = self.stbl.peek(method_id)
        if method is not None:
            print('error on line ' + str(line) + ': method \'' + method_id + '\' already declared on line ' + str(method.line))
        else:
            print('do method code here lol')
        method = Method(method_id, method_type, line)
        self.stbl.pushMethod(method)
        self.stbl.pushFrame(method)
        method.body += method.id + ':\n'
        method.body += 'push %rbp\n'
        method.body += 'movq %rsp, %rbp\n'
        if not method.has_return:
            method.body += 'pop %rbp\n'
            method.body += 'ret\n'
        self.data += method.data
        self.body += method.body
        for i in range(len(ctx.param())):
            param_id = ctx.param(i).ID().getText()
            param_type = ctx.param(i).data_type().getText()
            param_size = 8
            param_array = False
            param = self.stbl.peek(param_id)
            if param is not None:
                print('error on line ' + str(line) + ': param \'' + param_id + '\' already declared on line ' + str(param.line))
            method.pushParam(param_type)
            param = Var(param_id,
                        param_type,
                        param_size,
                        Var.LOCAL,
                        param_array,
                        line)
            self.stbl.pushVar(param)
        self.visit(ctx.block())
        self.stbl.popFrame()

    def visitExpr(self, ctx):
        if ctx.literal() is not None:
            return self.visit(ctx.literal())
        elif ctx.location() is not None:
            return self.visit(ctx.location())
        elif len(ctx.expr()) == 2:
            expr0_type = self.visit(ctx.expr(0))
            expr1_type = self.visit(ctx.expr(1))
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

    def visitLiteral(self, ctx):
        if ctx.bool_lit() is not None:
            return 'bool'
        if ctx.INT_LIT() is not None:
            return 'int'
        if ctx.CHAR_LIT() is not None:
            return 'char'
        if ctx.FLOAT_LIT() is not None:
            return 'float'
        if ctx.STRING_LIT() is not None:
            return 'string'

    def visitLocation(self, ctx):
        if ctx.expr() is not None:
            return 'var'
        if ctx.LSQUARE() is not None:
            return 'array'
        # find for global! not peek!


# load source code
filein = open('./test.coffee', 'r')
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

# assembly output code
code = visitor.data + visitor.body
print(code)

# save the assembly file
fileout = open('a.s', 'w')
fileout.write(code)
fileout.close()

# assemble and link
os.system("gcc a.s -lm ; ./a.out ; echo $?")
