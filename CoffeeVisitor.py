# Generated from ./Coffee.g4 by ANTLR 4.9.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .CoffeeParser import CoffeeParser
else:
    from CoffeeParser import CoffeeParser

# This class defines a complete generic visitor for a parse tree produced by CoffeeParser.

class CoffeeVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by CoffeeParser#program.
    def visitProgram(self, ctx:CoffeeParser.ProgramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#import_stmt.
    def visitImport_stmt(self, ctx:CoffeeParser.Import_stmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#global_decl.
    def visitGlobal_decl(self, ctx:CoffeeParser.Global_declContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#var_decl.
    def visitVar_decl(self, ctx:CoffeeParser.Var_declContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#var_assign.
    def visitVar_assign(self, ctx:CoffeeParser.Var_assignContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#var.
    def visitVar(self, ctx:CoffeeParser.VarContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#data_type.
    def visitData_type(self, ctx:CoffeeParser.Data_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#method_decl.
    def visitMethod_decl(self, ctx:CoffeeParser.Method_declContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#return_type.
    def visitReturn_type(self, ctx:CoffeeParser.Return_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#param.
    def visitParam(self, ctx:CoffeeParser.ParamContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#block.
    def visitBlock(self, ctx:CoffeeParser.BlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#eval.
    def visitEval(self, ctx:CoffeeParser.EvalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#assign.
    def visitAssign(self, ctx:CoffeeParser.AssignContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#if.
    def visitIf(self, ctx:CoffeeParser.IfContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#for.
    def visitFor(self, ctx:CoffeeParser.ForContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#while.
    def visitWhile(self, ctx:CoffeeParser.WhileContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#return.
    def visitReturn(self, ctx:CoffeeParser.ReturnContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#break.
    def visitBreak(self, ctx:CoffeeParser.BreakContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#continue.
    def visitContinue(self, ctx:CoffeeParser.ContinueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#pass.
    def visitPass(self, ctx:CoffeeParser.PassContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#loop_var.
    def visitLoop_var(self, ctx:CoffeeParser.Loop_varContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#method_call.
    def visitMethod_call(self, ctx:CoffeeParser.Method_callContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#expr.
    def visitExpr(self, ctx:CoffeeParser.ExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#assign_op.
    def visitAssign_op(self, ctx:CoffeeParser.Assign_opContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#literal.
    def visitLiteral(self, ctx:CoffeeParser.LiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#bool_lit.
    def visitBool_lit(self, ctx:CoffeeParser.Bool_litContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#location.
    def visitLocation(self, ctx:CoffeeParser.LocationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#limit.
    def visitLimit(self, ctx:CoffeeParser.LimitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#low.
    def visitLow(self, ctx:CoffeeParser.LowContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#high.
    def visitHigh(self, ctx:CoffeeParser.HighContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CoffeeParser#step.
    def visitStep(self, ctx:CoffeeParser.StepContext):
        return self.visitChildren(ctx)



del CoffeeParser