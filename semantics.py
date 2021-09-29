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
        if ctx.LCURLY() != None:
            self.stbl.pushScope()

        self.visitChildren(ctx)

        if ctx.LCURLY() != None:
            self.stbl.popScope()

    def visitGlobal_decl(self, ctx):
        line = ctx.start.line
        var_type = ctx.var_decl().data_type().getText()
        for i in range(len(ctx.var_decl().var_assign())):
            var_id = ctx.var_decl().var_assign(i).var().ID().getText()
            var_size = 8
            var_array = False

            var = self.stbl.peek(var_id)
            if var != None:
                print('error')

            # checking for arrays
            if ctx.var_decl().var_assign(i).var().INT_LIT() != None:
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
            if var != None:
                print('error')

            var = Var(var_id,
                      var_type,
                      var_size,
                      Var.GLOBAL,
                      var_array,
                      line)
            self.stbl.pushVar(var)


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
