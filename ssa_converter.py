

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from basic_blocks import BasicBlock
from cfg import ControlFlowGraph


ASSIGNING_OPS = {
    "=",
    "+",
    "-",
    "*",
    "/",
    "<",
    ">",
    "<=",
    ">=",
    "==",
    "!=",
    "call",
    "array_load",
}


@dataclass
class SSAResult:
    block_lines: Dict[int, List[str]]


def is_number(value: Optional[str]) -> bool:
    return value is not None and value.lstrip("-").isdigit()


def rename_read(value: Optional[str], env: Dict[str, str]) -> Optional[str]:
    if value is None or is_number(value):
        return value
    return env.get(value, value)


def rename_write(name: str, counters: Dict[str, int], env: Dict[str, str]) -> str:
    counters[name] += 1
    versioned = f"{name}_{counters[name]}"
    env[name] = versioned
    return versioned


def should_phi(name: str) -> bool:
    # Phi nodes for user variables keep the presentation cleaner than doing it
    # for every temporary.
    return not name.startswith("t")


def convert_to_ssa(blocks: List[BasicBlock], cfg: ControlFlowGraph) -> SSAResult:
    counters: Dict[str, int] = defaultdict(int)
    outgoing_envs: Dict[int, Dict[str, str]] = {}
    block_lines: Dict[int, List[str]] = {}

    for block in blocks:
        preds = sorted(cfg.predecessors.get(block.block_id, set()))
        if not preds:
            env: Dict[str, str] = {}
        elif len(preds) == 1:
            env = dict(outgoing_envs.get(preds[0], {}))
        elif any(pred not in outgoing_envs for pred in preds):
            # When a later block jumps back here, this is usually a loop header.
            # For this demo we keep phi insertion focused on forward if-else merges.
            first_known = next((pred for pred in preds if pred in outgoing_envs), None)
            env = dict(outgoing_envs.get(first_known, {})) if first_known is not None else {}
        else:
            env = {}
            candidate_vars: Set[str] = set()
            for pred in preds:
                candidate_vars.update(outgoing_envs.get(pred, {}).keys())

            phi_lines: List[str] = []
            for name in sorted(candidate_vars):
                incoming = [outgoing_envs.get(pred, {}).get(name, name) for pred in preds]
                distinct = set(incoming)
                if len(distinct) == 1:
                    env[name] = incoming[0]
                elif should_phi(name):
                    phi_name = rename_write(name, counters, env)
                    phi_lines.append(f"{phi_name} = phi({', '.join(incoming)})")
                else:
                    env[name] = incoming[-1]
            block_lines[block.block_id] = phi_lines

        lines = block_lines.setdefault(block.block_id, [])
        for instr in block.instructions:
            if instr.op in {"label", "goto"}:
                lines.append(str(instr))
                continue
            if instr.op == "ifFalse":
                cond = rename_read(instr.arg1, env)
                lines.append(f"ifFalse {cond} goto {instr.result}")
                continue
            if instr.op == "param":
                arg = rename_read(instr.arg1, env)
                lines.append(f"param {arg}")
                continue
            if instr.op == "call":
                result = rename_write(instr.result, counters, env)
                lines.append(f"{result} = call {instr.arg1}")
                continue
            if instr.op == "array_load":
                array_name = rename_read(instr.arg1, env)
                index = rename_read(instr.arg2, env)
                result = rename_write(instr.result, counters, env)
                lines.append(f"{result} = {array_name}[{index}]")
                continue
            if instr.op == "array_store":
                value = rename_read(instr.arg1, env)
                index = rename_read(instr.arg2, env)
                array_name = rename_write(instr.result, counters, env)
                lines.append(f"{array_name}[{index}] = {value}")
                continue
            if instr.op == "return":
                value = rename_read(instr.arg1, env)
                lines.append("return" if value is None else f"return {value}")
                continue
            if instr.op == "=":
                source = rename_read(instr.arg1, env)
                result = rename_write(instr.result, counters, env)
                lines.append(f"{result} = {source}")
                continue
            if instr.op in ASSIGNING_OPS:
                left = rename_read(instr.arg1, env)
                right = rename_read(instr.arg2, env)
                result = rename_write(instr.result, counters, env)
                lines.append(f"{result} = {left} {instr.op} {right}")
                continue
            lines.append(str(instr))

        outgoing_envs[block.block_id] = dict(env)

    return SSAResult(block_lines=block_lines)


def format_ssa(ssa_result: SSAResult) -> str:
    lines: List[str] = []
    for block_id in sorted(ssa_result.block_lines):
        lines.append(f"B{block_id}")
        for entry in ssa_result.block_lines[block_id]:
            lines.append(f"  {entry}")
        lines.append("")
    return "\n".join(lines).strip()
