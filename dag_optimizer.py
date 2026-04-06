"""
dag_optimizer.py

Per-basic-block local optimization using value numbering in the spirit of DAG
optimization. It performs:
- constant folding
- common subexpression elimination
- alias propagation for redundant temporaries
"""

from __future__ import annotations

from dataclasses import replace
from typing import Dict, List, Tuple

from basic_blocks import BasicBlock
from tac_generator import TACInstruction


COMMUTATIVE_OPS = {"+", "*", "==", "!="}
FOLDABLE_OPS = {"+", "-", "*", "/", "<", ">", "<=", ">=", "==", "!="}


def is_number(value: str | None) -> bool:
    return value is not None and value.lstrip("-").isdigit()


def compute_binary(op: str, left: int, right: int) -> int:
    if op == "+":
        return left + right
    if op == "-":
        return left - right
    if op == "*":
        return left * right
    if op == "/":
        if right == 0:
            raise ZeroDivisionError("Division by zero during constant folding")
        return left // right
    if op == "<":
        return int(left < right)
    if op == ">":
        return int(left > right)
    if op == "<=":
        return int(left <= right)
    if op == ">=":
        return int(left >= right)
    if op == "==":
        return int(left == right)
    if op == "!=":
        return int(left != right)
    raise ValueError(f"Unsupported fold operation: {op}")


def canonical_binary_key(op: str, left: str, right: str) -> Tuple[str, str, str]:
    if op in COMMUTATIVE_OPS and left > right:
        left, right = right, left
    return (op, left, right)


def optimize_block(block: BasicBlock) -> BasicBlock:
    constants: Dict[str, str] = {}
    aliases: Dict[str, str] = {}
    expr_table: Dict[Tuple[str, str, str], str] = {}
    optimized: List[TACInstruction] = []

    def resolve(value: str | None) -> str | None:
        if value is None:
            return None
        while value in aliases:
            value = aliases[value]
        return constants.get(value, value)

    def kill_name(name: str | None) -> None:
        if not name:
            return
        constants.pop(name, None)
        aliases.pop(name, None)
        stale_keys = [key for key, result in expr_table.items() if result == name or name in key]
        for key in stale_keys:
            expr_table.pop(key, None)

    for instr in block.instructions:
        if instr.op in {"label", "goto", "ifFalse", "param", "call", "return", "array_store", "array_load"}:
            new_instr = replace(instr, arg1=resolve(instr.arg1), arg2=resolve(instr.arg2))
            if instr.op in {"call", "array_load"}:
                kill_name(instr.result)
            elif instr.op == "array_store":
                expr_table.clear()
            optimized.append(new_instr)
            continue

        if instr.op == "=":
            source = resolve(instr.arg1)
            kill_name(instr.result)
            if source is None:
                continue
            if is_number(source):
                constants[instr.result] = source
            else:
                aliases[instr.result] = source
            optimized.append(TACInstruction(op="=", arg1=source, result=instr.result))
            continue

        if instr.op in FOLDABLE_OPS:
            left = resolve(instr.arg1)
            right = resolve(instr.arg2)
            kill_name(instr.result)
            if left is None or right is None:
                optimized.append(replace(instr, arg1=left, arg2=right))
                continue
            if is_number(left) and is_number(right):
                folded = str(compute_binary(instr.op, int(left), int(right)))
                constants[instr.result] = folded
                optimized.append(TACInstruction(op="=", arg1=folded, result=instr.result))
                continue
            key = canonical_binary_key(instr.op, left, right)
            if key in expr_table:
                aliases[instr.result] = expr_table[key]
                optimized.append(TACInstruction(op="=", arg1=expr_table[key], result=instr.result))
                continue
            expr_table[key] = instr.result
            optimized.append(TACInstruction(op=instr.op, arg1=left, arg2=right, result=instr.result))
            continue

        optimized.append(replace(instr, arg1=resolve(instr.arg1), arg2=resolve(instr.arg2)))

    return BasicBlock(block_id=block.block_id, instructions=optimized, labels=list(block.labels))


def optimize_blocks(blocks: List[BasicBlock]) -> List[BasicBlock]:
    return [optimize_block(block) for block in blocks]


def flatten_blocks(blocks: List[BasicBlock]) -> List[TACInstruction]:
    instructions: List[TACInstruction] = []
    for block in blocks:
        instructions.extend(block.instructions)
    return instructions
