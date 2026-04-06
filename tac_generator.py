"""
tac_generator.py

Generates Three Address Code (TAC) from the AST.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from parser import (
    ArrayAccess,
    Assign,
    BinaryOp,
    Block,
    Call,
    ExprStatement,
    ForLoop,
    FunctionDecl,
    Identifier,
    IfElse,
    Number,
    Program,
    Return,
    UnaryUpdate,
    VarDecl,
    WhileLoop,
)


@dataclass
class TACInstruction:
    op: str
    arg1: Optional[str] = None
    arg2: Optional[str] = None
    result: Optional[str] = None
    text: Optional[str] = None

    def __str__(self) -> str:
        if self.text is not None:
            return self.text
        if self.op == "label":
            return f"{self.result}:"
        if self.op == "goto":
            return f"goto {self.result}"
        if self.op == "ifFalse":
            return f"ifFalse {self.arg1} goto {self.result}"
        if self.op == "param":
            return f"param {self.arg1}"
        if self.op == "call":
            return f"{self.result} = call {self.arg1}"
        if self.op == "return":
            return "return" if self.arg1 is None else f"return {self.arg1}"
        if self.op == "array_load":
            return f"{self.result} = {self.arg1}[{self.arg2}]"
        if self.op == "array_store":
            return f"{self.result}[{self.arg2}] = {self.arg1}"
        if self.op == "=":
            return f"{self.result} = {self.arg1}"
        if self.arg2 is not None:
            return f"{self.result} = {self.arg1} {self.op} {self.arg2}"
        return f"{self.result} = {self.op} {self.arg1}"


class TACGenerator:
    def __init__(self) -> None:
        self.instructions: List[TACInstruction] = []
        self.temp_counter = 0
        self.label_counter = 0
        self.current_function: Optional[str] = None

    def new_temp(self) -> str:
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def new_label(self) -> str:
        self.label_counter += 1
        return f"L{self.label_counter}"

    def emit(self, instr: TACInstruction) -> None:
        self.instructions.append(instr)

    def generate(self, program: Program) -> List[TACInstruction]:
        self.instructions = []
        for function in program.functions:
            self.generate_function(function)
        return self.instructions

    def generate_function(self, function: FunctionDecl) -> None:
        self.current_function = function.name
        self.emit(TACInstruction(op="label", result=f"func_{function.name}"))
        for param in function.params:
            self.emit(TACInstruction(op="text", text=f"# param {param}"))
        self.generate_block(function.body)

    def generate_block(self, block: Block) -> None:
        for statement in block.statements:
            self.generate_statement(statement)

    def generate_statement(self, statement) -> None:
        if isinstance(statement, VarDecl):
            if statement.size is None:
                self.emit(TACInstruction(op="text", text=f"# declare int {statement.name}"))
            else:
                self.emit(TACInstruction(op="text", text=f"# declare int {statement.name}[{statement.size}]"))
            if statement.init is not None:
                value = self.generate_expression(statement.init)
                self.emit(TACInstruction(op="=", arg1=value, result=statement.name))
            return
        if isinstance(statement, Assign):
            value = self.generate_expression(statement.value)
            if isinstance(statement.target, Identifier):
                self.emit(TACInstruction(op="=", arg1=value, result=statement.target.name))
            elif isinstance(statement.target, ArrayAccess):
                index = self.generate_expression(statement.target.index)
                self.emit(
                    TACInstruction(
                        op="array_store",
                        arg1=value,
                        arg2=index,
                        result=statement.target.array,
                    )
                )
            return
        if isinstance(statement, ExprStatement):
            self.generate_expression(statement.expr)
            return
        if isinstance(statement, IfElse):
            self.generate_if(statement)
            return
        if isinstance(statement, WhileLoop):
            self.generate_while(statement)
            return
        if isinstance(statement, ForLoop):
            self.generate_for(statement)
            return
        if isinstance(statement, Return):
            value = self.generate_expression(statement.value) if statement.value else None
            self.emit(TACInstruction(op="return", arg1=value))
            return
        if isinstance(statement, Block):
            self.generate_block(statement)
            return
        raise TypeError(f"Unsupported statement type: {type(statement)!r}")

    def generate_if(self, statement: IfElse) -> None:
        condition = self.generate_expression(statement.condition)
        else_label = self.new_label()
        end_label = self.new_label()
        self.emit(TACInstruction(op="ifFalse", arg1=condition, result=else_label))
        self.generate_block(statement.then_block)
        if statement.else_block:
            self.emit(TACInstruction(op="goto", result=end_label))
            self.emit(TACInstruction(op="label", result=else_label))
            self.generate_block(statement.else_block)
            self.emit(TACInstruction(op="label", result=end_label))
        else:
            self.emit(TACInstruction(op="label", result=else_label))

    def generate_while(self, statement: WhileLoop) -> None:
        start_label = self.new_label()
        end_label = self.new_label()
        self.emit(TACInstruction(op="label", result=start_label))
        condition = self.generate_expression(statement.condition)
        self.emit(TACInstruction(op="ifFalse", arg1=condition, result=end_label))
        self.generate_block(statement.body)
        self.emit(TACInstruction(op="goto", result=start_label))
        self.emit(TACInstruction(op="label", result=end_label))

    def generate_for(self, statement: ForLoop) -> None:
        if statement.init is not None:
            self.generate_statement(statement.init)
        start_label = self.new_label()
        end_label = self.new_label()
        self.emit(TACInstruction(op="label", result=start_label))
        if statement.condition is not None:
            condition = self.generate_expression(statement.condition)
            self.emit(TACInstruction(op="ifFalse", arg1=condition, result=end_label))
        self.generate_block(statement.body)
        if statement.update is not None:
            self.generate_statement(statement.update)
        self.emit(TACInstruction(op="goto", result=start_label))
        self.emit(TACInstruction(op="label", result=end_label))

    def generate_expression(self, expr) -> str:
        if isinstance(expr, Number):
            return str(expr.value)
        if isinstance(expr, Identifier):
            return expr.name
        if isinstance(expr, ArrayAccess):
            index = self.generate_expression(expr.index)
            temp = self.new_temp()
            self.emit(TACInstruction(op="array_load", arg1=expr.array, arg2=index, result=temp))
            return temp
        if isinstance(expr, BinaryOp):
            left = self.generate_expression(expr.left)
            right = self.generate_expression(expr.right)
            temp = self.new_temp()
            self.emit(TACInstruction(op=expr.op, arg1=left, arg2=right, result=temp))
            return temp
        if isinstance(expr, Call):
            for arg in expr.args:
                arg_value = self.generate_expression(arg)
                self.emit(TACInstruction(op="param", arg1=arg_value))
            temp = self.new_temp()
            self.emit(TACInstruction(op="call", arg1=expr.name, result=temp))
            return temp
        if isinstance(expr, UnaryUpdate):
            if isinstance(expr.target, Identifier):
                current = expr.target.name
                temp = self.new_temp()
                operator = "+" if expr.op == "++" else "-"
                self.emit(TACInstruction(op=operator, arg1=current, arg2="1", result=temp))
                self.emit(TACInstruction(op="=", arg1=temp, result=current))
                return current
            if isinstance(expr.target, ArrayAccess):
                index = self.generate_expression(expr.target.index)
                current = self.new_temp()
                self.emit(TACInstruction(op="array_load", arg1=expr.target.array, arg2=index, result=current))
                updated = self.new_temp()
                operator = "+" if expr.op == "++" else "-"
                self.emit(TACInstruction(op=operator, arg1=current, arg2="1", result=updated))
                self.emit(
                    TACInstruction(
                        op="array_store",
                        arg1=updated,
                        arg2=index,
                        result=expr.target.array,
                    )
                )
                return updated
            raise TypeError("Increment/decrement target must be a variable or array element")
        raise TypeError(f"Unsupported expression type: {type(expr)!r}")


def generate_tac(program: Program) -> List[TACInstruction]:
    return TACGenerator().generate(program)
