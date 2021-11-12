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
from CoffeeUtil import Import, Method, SymbolTable, Var

# we add indents to make diffs smoother
indent = '  '
# register named for readability purposes
result = '%rax'
# completed tests
tests = []


def test_file(file):
    # load base test file
    filein = open('./' + file + '.coffee', 'r')

    # read whatever file was enabled
    source_code = filein.read()
    filein.close()

    # create Coffee Visitor object
    visitor = CoffeeTreeVisitor()

    # visit nodes from tree root
    visitor.visit(CoffeeParser(antlr.CommonTokenStream(CoffeeLexer(antlr.InputStream(source_code)))).program())

    # print assembly output code
    code = visitor.data + visitor.body
    print(code)

    # save the assembly file to a.s
    fileout = open('a.s', 'w')
    fileout.write(code)
    fileout.close()

    # assemble and link via gcc
    os.system("gcc a.s -lm ; ./a.out ; echo $?")


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


# var, but syntax is slightly altered
class Var(Var):
    # enforcing bool helps catch errors, ctx typing must be specified to explain where start comes from
    def __init__(self, var_id, data_type, is_global: bool, line):
        super().__init__(var_id,
                         data_type,
                         8,
                         int(is_global),
                         False,
                         line)

    # actions that are only relevant if we expect an array
    def array_check(self, ctx):
        arrlit = ctx.var_assign(0).var().INT_LIT()
        # it's more performant to just allow same value reassignment here
        self.is_array = arrlit
        if arrlit:
            size: int = arrlit.getText() * 8
            # catch rule 14
            if int(size) == 0:
                print('error on line ' + str(self.line) + ': array \'' + self.id + '\' has an illegal zero length')
                return False
            else:
                self.size = size
                return True
        else:
            return True


# define main visitor class
class CoffeeTreeVisitor(CoffeeVisitor):
    def __init__(self):
        self.stbl: SymbolTable = SymbolTable()
        self.data: str = '.data\n'
        self.body: str = '.text\n.global main\n'

    # shared function for variable declaration contexts
    def decl(self, ctx, is_global):
        if is_global:
            prefix = ctx.var_decl()
        else:
            prefix = ctx
        var = self.new_var(ctx,
                           prefix.var_assign(0).var().ID(),
                           prefix.data_type().getText(),
                           int(is_global))
        # ya it's a really weirdly specific criteria
        if is_global and var and var.array_check(prefix):
            # add global variable to code
            method_ctx = self.stbl.getMethodContext()
            method_ctx.data += indent + '.comm ' + var.id + ',' + str(var.size) + '\n'
        self.visitChildren(prefix)

    # performs validation before pushing variables to table. returns variable, which also functions as an inefficient but versatile boolean
    # 0: local, 1: global, 2: param
    def new_var(self, ctx: antlr.ParserRuleContext, var_id, data_type, scope):
        # get the proper string value
        var_id = var_id.getText()
        # the most likely outcome
        is_global = False
        # rule 2, unfortunately python has no case statements so we must suffer
        if scope == 2:
            msg_scope = 'param'
        elif scope == 1:
            msg_scope = 'global'
            is_global = True
        elif scope == 0:
            msg_scope = 'local'
        # this condition shouldn't really be possible but whatever
        else:
            print('Invalid scope encountered')
            return False
        # ya these if statements are a bit out of hand
        if is_global:
            var: Var = self.stbl.find(var_id)
        else:
            var: Var = self.stbl.peek(var_id)
        line: int = ctx.start.line
        if var:
            print('error on line ' + str(line) + ': var \'' + var_id + '\' already declared on line ' + str(var.line) + ' in ' + msg_scope + ' scope, this declaration will be ignored')
            return False
        else:
            var = Var(var_id,
                      data_type,
                      is_global,
                      line)
            self.stbl.pushVar(var)
            return var

    def visitAssign(self, ctx):
        method_ctx = self.stbl.getMethodContext()
        method_ctx.body += indent + 'movq ' + ctx.location().getText() + '(%rip), ' + result + '\n'
        self.visitChildren(ctx)
        method_ctx.body += indent + 'movq ' + result + ', ' + ctx.location().getText() + '(%rip)\n'

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
        middle_label = self.stbl.getNextLabel()
        end_label = self.stbl.getNextLabel()
        self.stbl.pushScope()
        loop = self.new_var(ctx, ctx.loop_var(), 'int', 0)
        # TODO: this implementation is pretty basic, I could probably add compatibility with expressions that aren't just simple int literals
        # TODO: theres a lot of code duplication
        limits: CoffeeParser.LimitContext = ctx.limit()
        low = self.new_var(ctx, limits.low(), 'int', 0)
        method_ctx.body += indent + 'movq $' + low.id + ', ' + result + '\n'
        method_ctx.body += indent + 'movq ' + result + ', ' + str(low.addr) + '(%rbp)\n'
        high = self.new_var(ctx, limits.high(), 'int', 0)
        method_ctx.body += indent + 'movq $' + high.id + ', ' + result + '\n'
        method_ctx.body += indent + 'movq ' + result + ', ' + str(high.addr) + '(%rbp)\n'
        step = self.new_var(ctx, limits.step(), 'int', 0)
        method_ctx.body += indent + 'movq $' + step.id + ', ' + result + '\n'
        method_ctx.body += indent + 'movq ' + result + ', ' + str(step.addr) + '(%rbp)\n'
        # initialise loop variable
        method_ctx.body += indent + 'movq ' + str(low.addr) + '(%rbp), ' + result + '\n'
        method_ctx.body += indent + 'movq ' + result + ', ' + str(loop.addr) + '(%rbp)\n'
        method_ctx.body += start_label + ':\n'
        self.visit(ctx.block())
        method_ctx.body += middle_label + ':\n'
        # move required variables into registers
        method_ctx.body += indent + 'movq ' + str(loop.addr) + '(%rbp), ' + result + '\n'
        method_ctx.body += indent + 'movq ' + str(step.addr) + '(%rbp), %r11\n'
        # increment loop variable
        method_ctx.body += indent + 'addq %r11, ' + result + '\n'
        # push the loop variable
        method_ctx.body += indent + 'movq ' + result + ', ' + str(loop.addr) + '(%rbp)\n'
        # move max for loop value to register
        method_ctx.body += indent + 'movq ' + str(high.addr) + '(%rbp), %r10\n'
        # check if loop variable has hit the max value
        method_ctx.body += indent + 'cmp %r10, ' + result + '\n'
        # terminate loop if iteration has finished...
        method_ctx.body += indent + 'jge ' + end_label + '\n'
        # otherwise keep iterating
        method_ctx.body += indent + 'jmp ' + start_label + '\n'
        method_ctx.body += end_label + ':\n'
        self.stbl.popScope()

    def visitGlobal_decl(self, ctx):
        self.decl(ctx, True)

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
            # if there are more than 6 arguments we must allocate a stack size
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
            # used to record how many parameters are successful
            pid = 0
            for i in range(len(ctx.param())):
                param_type: str = ctx.param(i).data_type().getText()
                param: Var = self.new_var(ctx,
                                          ctx.param(i).ID(),
                                          param_type,
                                          2)
                # we only want to do all this if we actually have a parameter
                if param:
                    method.pushParam(param_type)
                    # only up to 6 values can fit into registers
                    if pid < 6:
                        method.body += indent + 'movq ' + self.stbl.param_reg[pid] + ', ' + str(param.addr) + '(%rbp)\n'
                    else:
                        pointer += 8
                        # this whole pointer + param_size thing would allow for arrays, I don't think we're expected to do arrays, but whatever
                        method.body += indent + 'movq ' + str(pointer) + '(%rsp), ' + result + '\n'
                        # you can't move pointer to pointer directly
                        method.body += indent + 'movq ' + result + ', ' + str(param.addr) + '(%rbp)\n'
                    # count the parameter
                    pid += 1
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
        # sentinel value to prevent invalid returns
        is_valid_return: bool = True
        # TODO: this looks kinda messy, idk, i could probably improve it
        # rule 8, starts freaking out if it doesn't get type checked
        if method_ctx.id == 'main' and isinstance(ctx.expr().literal(), CoffeeParser.LiteralContext) and not ctx.expr().literal().INT_LIT():
            print('error on line ' + str(line) + ': main method may only return an integer value')
            is_valid_return = False
        # rule 6
        if ctx.expr() and method_ctx.return_type == 'void':
            print('error on line ' + str(line) + ': return type specified for void method \'' + method_ctx.id + '\' declared on line ' + str(method_ctx.line))
            is_valid_return = False
        # I doubt that this covers every use case, but.... it's something
        if is_valid_return:
            method_ctx.body += indent + 'movq ' + ctx.expr().getText() + '(%rip), ' + result + '\n'
        self.visitChildren(ctx)

    def visitVar_assign(self, ctx):
        method_ctx = self.stbl.getMethodContext()
        self.visitChildren(ctx)
        var_ctx: CoffeeParser.VarContext = ctx.var()
        if var_ctx.LSQUARE():
            print('error on line ' + str(var_ctx.start.line) + ': assigning arrays is unsupported in this version')
        else:
            method_ctx.body += indent + 'movq ' + result + ', ' + ctx.var().getText() + '(%rip)\n'

    def visitVar_decl(self, ctx):
        self.decl(ctx, False)


test_file('test')
# test_file('1a')
# test_file('1b')
# test_file('2b')
# test_file('2c')
