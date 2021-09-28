import antlr4 as antlr
from CoffeeLexer import CoffeeLexer
from CoffeeVisitor import CoffeeVisitor
from CoffeeParser import CoffeeParser
from CoffeeUtil import Var, Method, Import, Loop, SymbolTable

class CoffeeTreeVisitor(CoffeeVisitor):
    def __init__(self):
        self.stbl = SymbolTable()
        
    def visitProgram(self, ctx):
        self.visitChildren(ctx)

#load source code
filein = open('./test.coffee', 'r')
source_code = filein.read();
filein.close()

#create a token stream from source code
lexer = CoffeeLexer(antlr.InputStream(source_code))
stream = antlr.CommonTokenStream(lexer)

#parse token stream
parser = CoffeeParser(stream)
tree = parser.program()

#create Coffee Visitor object
visitor = CoffeeTreeVisitor()

#visit nodes from tree root
visitor.visit(tree)
