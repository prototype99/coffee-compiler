import antlr4 as antlr
from CoffeeLexer import CoffeeLexer
from CoffeeVisitor import CoffeeVisitor
from CoffeeParser import CoffeeParser
from CoffeeUtil import Var, Method, Import, Loop, SymbolTable


class CoffeeTreeVisitor(CoffeeVisitor):
    def __init__(self):
        self.stbl = SymbolTable()

    def visitProgram(self, ctx):
        method = Method('main', 'int', ctx.start.line)
        self.stbl.pushFrame(method)
        self.visitChildren(ctx)
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
                print('error')

            # checking for arrays
            if ctx.var_decl().var_assign(i).var().INT_LIT() is not None:
                print(ctx.var_decl().var_assign(i).var().INT_LIT().getText())

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
                print('error on line ' + str(line) + ': var \'' + var_id + '\' already declared on line ' + str(var.line))

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
            print('error on line ' + str(line) + ': var \'' + method_id + '\' already declared on line ' + str(method.line))
        method = Method(method_id, method_type, line)
        self.stbl.pushMethod(method)
        self.stbl.pushFrame(method)
        for i in range(len(ctx.param())):
            var_id = ctx.param(i).ID().getText()
            var_type = ctx.param(i).data_type().getText()
            var_size = 8
            var_array = False
            var = self.stbl.peek(var_id)
            if var is not None:
                print('error on line ' + str(line) + ': var \'' + var_id + '\' already declared on line ' + str(var.line))
            method.pushParam(var_type)
        self.visit(ctx.block())
        self.stbl.popFrame()


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
