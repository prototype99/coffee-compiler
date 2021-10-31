# this file should be identical for both the semantic analysis and code generation uploads. If there are any notable differences please contact for clarification
# Oh and... sorry if it's not my best work. I briefly made the mistake of taking up an internship
# completed semantic analysis tasks: 1, 2
# TODO: add code for rules : 5, 7, 26
# completed codegen tasks: 2

# TODO: add more shared message/duplicate check functions
import antlr4 as antlr
import os
from CoffeeLexer import CoffeeLexer
from CoffeeVisitor import CoffeeVisitor
from CoffeeParser import CoffeeParser
# remember to add Loop for loops
from CoffeeUtil import Var, Method, Import, SymbolTable

# constants used to improve codegen readability
# we add indents to make diffs smoother
indent = '  '
result = '%rax'


# define some static helper functions
def array_check(ctx, i):
    return ctx.var_assign(i).var().INT_LIT()


def var_size(isarray, ctx, i, line, var_id):
    if isarray:
        size: int = ctx.var_assign(i).var().INT_LIT().getText() * 8
        # catch rule 14
        if int(size) == 0:
            print('error on line ' + str(line) + ': array \'' + var_id + '\' has an illegal zero length')
        return size
    else:
        return 8


# method with extended semantic analysis capabilities
class Method(Method):
    def __init__(self, id: str, return_type: str, line: int):
        super().__init__(id, return_type, line)
        # used for if statement semantic analysis
        self.blocks: int = 0
        # list of if statement evaluation results
        self.if_returns = []

    def check_if(self, ctx):
        # evaluate whether or not if statement equates to a method return
        # TODO: actually like... evaluate whether returns are going on, or whatever, idk, we live in a society
        if ctx.ELSE():
            # for i in range(len(ctx.block())):
            #     print(ctx.block(i).getText())
            self.if_returns.append(True)
        else:
            self.if_returns.append(False)
        # rule 9
        if len(self.if_returns) == self.blocks:
            if True in self.if_returns:
                self.has_return = True
            else:
                print('warning on line ' + str(self.line) + ': method \'' + self.id + '\' method does not always return a value')


# define main visitor class
class CoffeeTreeVisitor(CoffeeVisitor):
    def __init__(self):
        self.stbl: SymbolTable = SymbolTable()
        self.data: str = '.data\n'
        self.body: str = '.text\n.global main\n'

    # def visitAssign(self, ctx):
    #     pass

    def visitBlock(self, ctx):
        line: int = ctx.start.line
        # check to see if a scope is pushed
        if ctx.LCURLY():
            self.stbl.pushScope()
        # go through the code
        self.visitChildren(ctx)
        if ctx.RCURLY():
            self.stbl.popScope()
        # braces should be matched
        elif ctx.LCURLY():
            print('error on line ' + str(line) + ': expected \'}\', got \'{\'')

    def visitExpr(self, ctx):
        # rule 22: the language spec never actually says that ints can be true or false
        if ctx.NOT() and len(ctx.expr()) == 1 and ctx.expr(0).literal().INT_LIT():
            print('error on line ' + str(ctx.start.line) + ': cannot apply boolean action to integer value')
        if ctx.literal():
            return self.visit(ctx.literal())
        elif ctx.location():
            return self.visit(ctx.location())
        elif len(ctx.expr()) == 2:
            method_ctx = self.stbl.getMethodContext()
            expr0_type: str = self.visit(ctx.expr(0))
            method_ctx.body += indent + 'movq ' + result + ', %r10\n'
            expr1_type: str = self.visit(ctx.expr(1))
            method_ctx.body += indent + 'movq ' + result + ', %r11\n'
            if ctx.ADD():
                method_ctx.body += indent + 'addq %r10, %r11\n'
            method_ctx.body += indent + 'movq %r11, ' + result + '\n'
            # return the highest precedence type, if this is wrong I'll cry
            if expr0_type == 'float' or expr1_type == 'float':
                return 'float'
            if expr0_type == 'int' or expr1_type == 'int':
                return 'int'
            else:
                return 'bool'
        elif ctx.data_type():
            return ctx.data_type()
        else:
            return self.visitChildren(ctx)

    def visitFor(self, ctx):
        method_ctx = self.stbl.getMethodContext()
        start_label = self.stbl.getNextLabel()
        end_label = self.stbl.getNextLabel()
        self.stbl.pushScope()
        loop_var_id = ctx.loop_var().getText()
        loop_var = Var(loop_var_id, 'int', 8, Var.LOCAL, False, ctx.start.line)
        self.stbl.pushVar(loop_var)
        # TODO: this implementation is pretty basic, I could probably add compatibility with expressions that aren't just simple int literals
        limits: CoffeeParser.LimitContext = ctx.limit()
        low = limits.low()
        high = limits.high()
        step = limits.step()
        # TODO: initialise loop variable
        method_ctx.body += start_label + ':\n'
        self.visit(ctx.block())
        # TODO: increment loop variable
        # TODO: check loop termination criterion
        method_ctx.body += end_label + ':\n'
        self.stbl.popScope()

    def visitGlobal_decl(self, ctx):
        method_ctx = self.stbl.getMethodContext()
        line: int = ctx.start.line
        for i in range(len(ctx.var_decl().var_assign())):
            var_id: str = ctx.var_decl().var_assign(i).var().ID().getText()
            var_array: bool = array_check(ctx.var_decl(), i)
            var: Var = self.stbl.find(var_id)
            # rule 2
            if var:
                print('error on line ' + str(line) + ': global var \'' + var_id + '\' already declared on line ' + str(var.line))
            global_var_size = var_size(var_array, ctx.var_decl(), i, line, var_id)
            # add global variable to code
            method_ctx.data += indent + '.comm ' + var_id + ',' + str(global_var_size) + '\n'
            var: Var = Var(var_id,
                           ctx.var_decl().data_type().getText(),
                           global_var_size,
                           Var.GLOBAL,
                           var_array,
                           line)
            self.stbl.pushVar(var)
        self.visitChildren(ctx.var_decl())

    def visitIf(self, ctx):
        method_ctx = self.stbl.getMethodContext()
        method_ctx.check_if(ctx)
        self.visitChildren(ctx)
        # rule 11
        if ctx.expr().AND():
            for i in range(len(ctx.expr().expr())):
                if ctx.expr().expr(i).NOT() and len(ctx.expr().expr(i).expr()) == 1 and ctx.expr().expr(i).expr(0).literal().INT_LIT():
                    line: int = ctx.start.line
                    print('error on line ' + str(line) + ': expression \'' + ctx.expr().expr(i).getText() + '\' is non-boolean, this comparison is invalid')

    def visitImport_stmt(self, ctx):
        # do not give into the temptation of the sline, it is a false idol
        line: int = ctx.start.line
        for i in range(len(ctx.ID())):
            # in this context the id is an imported method. there is no getter so you must convert it to a string or experience hell
            import_id = str(ctx.ID(i))
            import_symbol = self.stbl.find(import_id)
            # rule 3
            if import_symbol:
                print('error on line ' + str(line) + ': symbol \'' + import_id + '\' already imported on line ' + str(import_symbol.line))
            import_symbol = Import(import_id, 'int', line)
            self.stbl.pushMethod(import_symbol)

    def visitLiteral(self, ctx):
        if ctx.bool_lit():
            return 'bool'
        if ctx.INT_LIT():
            method_ctx = self.stbl.getMethodContext()
            method_ctx.body += indent + 'movq $' + ctx.getText() + ', ' + result + '\n'
            return 'int'
        if ctx.CHAR_LIT():
            return 'char'
        if ctx.FLOAT_LIT():
            return 'float'
        if ctx.STRING_LIT():
            return 'string'

    def visitLocation(self, ctx):
        loc: Var = self.stbl.find(ctx.ID().getText())
        if loc:
            if loc.scope == Var.GLOBAL:
                pass
            elif loc.scope == Var.LOCAL:
                method_ctx = self.stbl.getMethodContext()
                method_ctx.body += indent + 'movq ' + str(loc.addr) + '(%rbp), ' + result + '\n'
            return loc.data_type

    def visitMethod_call(self, ctx):
        # rule 4
        if self.stbl.find(str(ctx.ID())):
            method_ctx = self.stbl.getMethodContext()
            param_len = len(ctx.expr())
            # if there are more thn 6 arguments we must allocate a stack size
            if param_len > 5:
                # this assumes that there are no arrays, also no there will be no etymological explanation
                porigin = (param_len - 6) * -8
            # we need an else clause to prevent null pointers
            else:
                porigin = 0
            pointer = porigin
            for i in range(param_len):
                self.visit(ctx.expr(i))
                if i < 6:
                    method_ctx.body += indent + 'movq ' + result + ', ' + self.stbl.param_reg[i] + '\n'
                else:
                    method_ctx.body += indent + 'movq ' + result + ', ' + str(pointer) + '(%rsp)\n'
                    # move to next pointer
                    pointer += 8
            # you have to make sure it starts at the largest pointer
            method_ctx.body += indent + 'addq $' + str(self.stbl.getStackPtr() + porigin) + ', %rsp\n'
            method_ctx.body += indent + 'call ' + str(ctx.ID()) + '\n'
            method_ctx.body += indent + 'subq $' + str(self.stbl.getStackPtr() + porigin) + ', %rsp\n'
        else:
            line: int = ctx.start.line
            print('error on line ' + str(line) + ': method \'' + str(ctx.ID()) + '\' does not exist, method call dropped')

    def visitMethod_decl(self, ctx):
        line: int = ctx.start.line
        method_id: str = ctx.ID().getText()
        method: Method = self.stbl.find(method_id)
        # rule 3
        if method:
            print('error on line ' + str(line) + ': method \'' + method_id + '\' already declared on line ' + str(method.line) + '. this declaration will be ignored')
        else:
            method: Method = Method(method_id, ctx.return_type().getText(), line)
            self.stbl.pushMethod(method)
            self.stbl.pushFrame(method)
            # produce the basic method code
            method.body += method.id + ':\n'
            method.body += indent + 'push %rbp\n'
            method.body += indent + 'movq %rsp, %rbp\n'
            pointer = 8
            for i in range(len(ctx.param())):
                param_id: str = ctx.param(i).ID().getText()
                param_type: str = ctx.param(i).data_type().getText()
                param_size: int = 8
                param_array: bool = False
                param: Var = self.stbl.peek(param_id)
                # rule 2
                if param:
                    print('error on line ' + str(line) + ': param \'' + param_id + '\' already declared on line ' + str(param.line) + '. this declaration will be ignored')
                else:
                    method.pushParam(param_type)
                    param: Var = Var(param_id,
                                     param_type,
                                     param_size,
                                     Var.LOCAL,
                                     param_array,
                                     line)
                    self.stbl.pushVar(param)
                    # only up to 6 values can fit into registers
                    if i < 6:
                        method.body += indent + 'movq ' + self.stbl.param_reg[i] + ', ' + str(param.addr) + '(%rbp)\n'
                    else:
                        pointer += param_size
                        # this whole pointer + param_size thing would allow for arrays, I don't think we're expected to do arrays, but whatever
                        method.body += indent + 'movq ' + str(pointer) + '(%rsp), ' + result + '\n'
                        # you can't move pointer to pointer directly
                        method.body += indent + 'movq ' + result + ', ' + str(param.addr) + '(%rbp)\n'
            self.visitChildren(ctx)
            if not method.has_return:
                method.body += indent + 'pop %rbp\n'
                method.body += indent + 'ret\n'
            self.data += method.data
            self.body += method.body
            self.stbl.popFrame()

    # starting point
    def visitProgram(self, ctx):
        # main method should push an int
        method = Method('main', 'int', ctx.start.line)
        # record number of blocks inside method
        for i in range(len(ctx.block())):
            # check if it is an if and thus should be counted, you must use isinstance so it doesn't freak out
            # TODO: find ALL if statements
            if isinstance(ctx.block(i).statement(), CoffeeParser.IfContext):
                method.blocks = method.blocks + 1
        # create new stack frame
        self.stbl.pushFrame(method)
        # push the method to the symbol table
        self.stbl.pushMethod(method)
        method.body += method.id + ':\n'
        method.body += indent + 'push %rbp\n'
        method.body += indent + 'movq %rsp, %rbp\n'
        self.visitChildren(ctx)
        if not method.has_return:
            method.body += indent + 'pop %rbp\n'
            method.body += indent + 'ret\n'
        self.data += method.data
        self.body += method.body
        self.stbl.popFrame()

    def visitReturn(self, ctx):
        method_ctx: Method = self.stbl.getMethodContext()
        line: int = ctx.start.line
        # rule 8, starts freaking out if it doesn't get type checked
        if method_ctx.id == 'main' and isinstance(ctx.expr().literal(), CoffeeParser.LiteralContext) and not ctx.expr().literal().INT_LIT():
            print('error on line ' + str(line) + ': main method may only return an integer value')
        # rule 6
        if ctx.expr() and method_ctx.return_type == 'void':
            print('error on line ' + str(line) + ': return type specified for void method \'' + method_ctx.id + '\' declared on line ' + str(method_ctx.line))
        self.visitChildren(ctx)

    def visitVar_assign(self, ctx):
        method_ctx = self.stbl.getMethodContext()
        self.visitChildren(ctx)
        method_ctx.body += indent + 'movq ' + result + ', ' + ctx.var().getText() + '(%rip)\n'

    def visitVar_decl(self, ctx):
        line: int = ctx.start.line
        for i in range(len(ctx.var_assign())):
            var_id: str = ctx.var_assign(i).var().ID().getText()
            var_array: bool = array_check(ctx, i)
            var: Var = self.stbl.peek(var_id)
            # rule 2
            if var:
                print('error on line ' + str(line) + ': var \'' + var_id + '\' already declared on line ' + str(
                    var.line) + ' in same scope')
            var: Var = Var(var_id,
                           ctx.data_type().getText(),
                           var_size(var_array, ctx, i, line, var_id),
                           Var.LOCAL,
                           var_array,
                           line)
            self.stbl.pushVar(var)
        self.visitChildren(ctx)


# load base test file
# filein = open('./test.coffee', 'r')
# filein = open('1a-original.coffee', 'r')
# filein = open('1b-original.coffee', 'r')
# filein = open('2b-original.coffee', 'r')
# filein = open('2b-8arg.coffee', 'r')
# filein = open('2b-6arg.coffee', 'r')
# filein = open('2b-1arg.coffee', 'r')
filein = open('2c-original.coffee', 'r')
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
