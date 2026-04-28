

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import List, Optional


@dataclass
class Program:
    functions: List["FunctionDecl"]


@dataclass
class FunctionDecl:
    name: str
    params: List[str]
    body: "Block"


@dataclass
class Block:
    statements: List["Statement"] = field(default_factory=list)


class Statement:
    pass


@dataclass
class VarDecl(Statement):
    name: str
    size: Optional[int] = None
    init: Optional["Expression"] = None


@dataclass
class Assign(Statement):
    target: "Expression"
    value: "Expression"


@dataclass
class IfElse(Statement):
    condition: "Expression"
    then_block: Block
    else_block: Optional[Block] = None


@dataclass
class WhileLoop(Statement):
    condition: "Expression"
    body: Block


@dataclass
class ForLoop(Statement):
    init: Optional[Statement]
    condition: Optional["Expression"]
    update: Optional[Statement]
    body: Block


@dataclass
class Return(Statement):
    value: Optional["Expression"] = None


@dataclass
class ExprStatement(Statement):
    expr: "Expression"


class Expression:
    pass


@dataclass
class Number(Expression):
    value: int


@dataclass
class Identifier(Expression):
    name: str


@dataclass
class ArrayAccess(Expression):
    array: str
    index: Expression


@dataclass
class BinaryOp(Expression):
    op: str
    left: Expression
    right: Expression


@dataclass
class Call(Expression):
    name: str
    args: List[Expression]


@dataclass
class UnaryUpdate(Expression):
    target: Expression
    op: str


TOKEN_RE = re.compile(
    r"""
    (?P<NUMBER>\d+)
    |(?P<IDENT>[A-Za-z_][A-Za-z0-9_]*)
    |(?P<OP>\+\+|--|==|!=|<=|>=|\+|-|\*|/|<|>|=)
    |(?P<SYMBOL>[(){}[\],;])
    |(?P<SKIP>\s+)
    |(?P<MISMATCH>.)
    """,
    re.VERBOSE,
)

KEYWORDS = {"function", "if", "else", "while", "for", "return", "int"}


@dataclass
class Token:
    kind: str
    value: str
    position: int


class TokenStream:
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.index = 0

    def peek(self) -> Token:
        return self.tokens[self.index]

    def peek_next(self) -> Token:
        next_index = min(self.index + 1, len(self.tokens) - 1)
        return self.tokens[next_index]

    def advance(self) -> Token:
        token = self.tokens[self.index]
        self.index += 1
        return token

    def expect(self, kind: str, value: Optional[str] = None) -> Token:
        token = self.peek()
        if token.kind != kind or (value is not None and token.value != value):
            expected = f"{kind} {value}" if value else kind
            raise SyntaxError(
                f"Expected {expected} at position {token.position}, found {token.kind} {token.value!r}"
            )
        return self.advance()

    def match(self, kind: str, value: Optional[str] = None) -> Optional[Token]:
        token = self.peek()
        if token.kind == kind and (value is None or token.value == value):
            return self.advance()
        return None


def tokenize(source: str) -> List[Token]:
    tokens: List[Token] = []
    for match in TOKEN_RE.finditer(source):
        kind = match.lastgroup
        value = match.group()
        position = match.start()
        if kind == "SKIP":
            continue
        if kind == "MISMATCH":
            raise SyntaxError(f"Unexpected character {value!r} at position {position}")
        if kind == "IDENT" and value in KEYWORDS:
            kind = "KEYWORD"
        tokens.append(Token(kind, value, position))
    tokens.append(Token("EOF", "", len(source)))
    return tokens


class Parser:
    def __init__(self, source: str) -> None:
        self.stream = TokenStream(tokenize(source))

    def parse(self) -> Program:
        functions: List[FunctionDecl] = []
        while self.stream.peek().kind != "EOF":
            functions.append(self.parse_function())
        return Program(functions=functions)

    def parse_function(self) -> FunctionDecl:
        if self.stream.peek().kind == "KEYWORD" and self.stream.peek().value == "function":
            self.stream.advance()
        else:
            # Accept a small C-style function header such as: int main(...)
            self.stream.expect("KEYWORD", "int")
        name = self.stream.expect("IDENT").value
        self.stream.expect("SYMBOL", "(")
        params: List[str] = []
        if not self.stream.match("SYMBOL", ")"):
            while True:
                if self.stream.peek().kind == "KEYWORD" and self.stream.peek().value == "int":
                    self.stream.advance()
                params.append(self.stream.expect("IDENT").value)
                if self.stream.match("SYMBOL", ")"):
                    break
                self.stream.expect("SYMBOL", ",")
        body = self.parse_block()
        return FunctionDecl(name=name, params=params, body=body)

    def parse_block(self) -> Block:
        self.stream.expect("SYMBOL", "{")
        statements: List[Statement] = []
        while not self.stream.match("SYMBOL", "}"):
            statements.append(self.parse_statement())
        return Block(statements=statements)

    def parse_statement(self) -> Statement:
        token = self.stream.peek()
        if token.kind == "KEYWORD" and token.value == "int":
            return self.parse_declaration()
        if token.kind == "KEYWORD" and token.value == "if":
            return self.parse_if()
        if token.kind == "KEYWORD" and token.value == "while":
            return self.parse_while()
        if token.kind == "KEYWORD" and token.value == "for":
            return self.parse_for()
        if token.kind == "KEYWORD" and token.value == "return":
            return self.parse_return()
        if token.kind == "SYMBOL" and token.value == "{":
            return self.parse_block()
        stmt = self.parse_assignment_or_expr_statement()
        self.stream.expect("SYMBOL", ";")
        return stmt

    def parse_declaration(self) -> VarDecl:
        self.stream.expect("KEYWORD", "int")
        name = self.stream.expect("IDENT").value
        size: Optional[int] = None
        init: Optional[Expression] = None
        if self.stream.match("SYMBOL", "["):
            size = int(self.stream.expect("NUMBER").value)
            self.stream.expect("SYMBOL", "]")
        if self.stream.match("OP", "="):
            init = self.parse_expression()
        self.stream.expect("SYMBOL", ";")
        return VarDecl(name=name, size=size, init=init)

    def parse_if(self) -> IfElse:
        self.stream.expect("KEYWORD", "if")
        self.stream.expect("SYMBOL", "(")
        condition = self.parse_expression()
        self.stream.expect("SYMBOL", ")")
        then_block = self.parse_statement_as_block()
        else_block = None
        if self.stream.match("KEYWORD", "else"):
            else_block = self.parse_statement_as_block()
        return IfElse(condition=condition, then_block=then_block, else_block=else_block)

    def parse_while(self) -> WhileLoop:
        self.stream.expect("KEYWORD", "while")
        self.stream.expect("SYMBOL", "(")
        condition = self.parse_expression()
        self.stream.expect("SYMBOL", ")")
        body = self.parse_statement_as_block()
        return WhileLoop(condition=condition, body=body)

    def parse_for(self) -> ForLoop:
        self.stream.expect("KEYWORD", "for")
        self.stream.expect("SYMBOL", "(")
        init: Optional[Statement] = None
        condition: Optional[Expression] = None
        update: Optional[Statement] = None

        if not self.stream.match("SYMBOL", ";"):
            init = self.parse_for_clause_statement()
            self.stream.expect("SYMBOL", ";")
        if not self.stream.match("SYMBOL", ";"):
            condition = self.parse_expression()
            self.stream.expect("SYMBOL", ";")
        if not self.stream.match("SYMBOL", ")"):
            update = self.parse_for_clause_statement()
            self.stream.expect("SYMBOL", ")")

        body = self.parse_statement_as_block()
        return ForLoop(init=init, condition=condition, update=update, body=body)

    def parse_return(self) -> Return:
        self.stream.expect("KEYWORD", "return")
        if self.stream.match("SYMBOL", ";"):
            return Return(value=None)
        value = self.parse_expression()
        self.stream.expect("SYMBOL", ";")
        return Return(value=value)

    def parse_statement_as_block(self) -> Block:
        if self.stream.peek().kind == "SYMBOL" and self.stream.peek().value == "{":
            return self.parse_block()
        stmt = self.parse_statement()
        return Block(statements=[stmt])

    def parse_assignment_or_expr_statement(self) -> Statement:
        target_expr = self.parse_expression()
        if self.stream.match("OP", "="):
            value = self.parse_expression()
            if not isinstance(target_expr, (Identifier, ArrayAccess)):
                raise SyntaxError("Left side of assignment must be a variable or array element")
            return Assign(target=target_expr, value=value)
        return ExprStatement(expr=target_expr)

    def parse_for_clause_statement(self) -> Statement:
        if self.stream.peek().kind == "KEYWORD" and self.stream.peek().value == "int":
            return self.parse_declaration()
        return self.parse_assignment_or_expr_statement()

    def parse_expression(self) -> Expression:
        return self.parse_equality()

    def parse_equality(self) -> Expression:
        expr = self.parse_relational()
        while self.stream.peek().kind == "OP" and self.stream.peek().value in {"==", "!="}:
            op = self.stream.advance().value
            right = self.parse_relational()
            expr = BinaryOp(op=op, left=expr, right=right)
        return expr

    def parse_relational(self) -> Expression:
        expr = self.parse_additive()
        while self.stream.peek().kind == "OP" and self.stream.peek().value in {"<", ">", "<=", ">="}:
            op = self.stream.advance().value
            right = self.parse_additive()
            expr = BinaryOp(op=op, left=expr, right=right)
        return expr

    def parse_additive(self) -> Expression:
        expr = self.parse_term()
        while self.stream.peek().kind == "OP" and self.stream.peek().value in {"+", "-"}:
            op = self.stream.advance().value
            right = self.parse_term()
            expr = BinaryOp(op=op, left=expr, right=right)
        return expr

    def parse_term(self) -> Expression:
        expr = self.parse_factor()
        while self.stream.peek().kind == "OP" and self.stream.peek().value in {"*", "/"}:
            op = self.stream.advance().value
            right = self.parse_factor()
            expr = BinaryOp(op=op, left=expr, right=right)
        return expr

    def parse_factor(self) -> Expression:
        token = self.stream.peek()
        if token.kind == "NUMBER":
            return Number(value=int(self.stream.advance().value))
        if token.kind == "IDENT":
            return self.parse_identifier_based_expression()
        if token.kind == "SYMBOL" and token.value == "(":
            self.stream.advance()
            expr = self.parse_expression()
            self.stream.expect("SYMBOL", ")")
            return expr
        raise SyntaxError(f"Unexpected token {token.value!r} at position {token.position}")

    def parse_identifier_based_expression(self) -> Expression:
        name = self.stream.expect("IDENT").value
        if self.stream.match("SYMBOL", "("):
            args: List[Expression] = []
            if not self.stream.match("SYMBOL", ")"):
                while True:
                    args.append(self.parse_expression())
                    if self.stream.match("SYMBOL", ")"):
                        break
                    self.stream.expect("SYMBOL", ",")
            expr: Expression = Call(name=name, args=args)
            if self.stream.peek().kind == "OP" and self.stream.peek().value in {"++", "--"}:
                raise SyntaxError("Increment/decrement cannot be applied to a function call")
            return expr
        if self.stream.match("SYMBOL", "["):
            index = self.parse_expression()
            self.stream.expect("SYMBOL", "]")
            expr = ArrayAccess(array=name, index=index)
        else:
            expr = Identifier(name=name)
        if self.stream.peek().kind == "OP" and self.stream.peek().value in {"++", "--"}:
            op = self.stream.advance().value
            return UnaryUpdate(target=expr, op=op)
        return expr


def parse_source(source: str) -> Program:
    return Parser(source).parse()
