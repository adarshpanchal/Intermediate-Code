

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from tac_generator import TACInstruction


@dataclass
class BasicBlock:
    block_id: int
    instructions: List[TACInstruction] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)

    def title(self) -> str:
        label_part = f" ({', '.join(self.labels)})" if self.labels else ""
        return f"B{self.block_id}{label_part}"


def map_labels(instructions: List[TACInstruction]) -> Dict[str, int]:
    labels: Dict[str, int] = {}
    for index, instr in enumerate(instructions):
        if instr.op == "label":
            labels[instr.result] = index
    return labels


def identify_leaders(instructions: List[TACInstruction]) -> List[int]:
    if not instructions:
        return []
    labels = map_labels(instructions)
    leaders: Set[int] = {0}
    for index, instr in enumerate(instructions):
        if instr.op == "label":
            leaders.add(index)
    for index, instr in enumerate(instructions):
        if instr.op in {"goto", "ifFalse"} and instr.result in labels:
            leaders.add(labels[instr.result])
            if index + 1 < len(instructions):
                leaders.add(index + 1)
    return sorted(leaders)


def form_basic_blocks(instructions: List[TACInstruction]) -> List[BasicBlock]:
    leaders = identify_leaders(instructions)
    if not leaders:
        return []

    blocks: List[BasicBlock] = []
    for block_index, leader in enumerate(leaders):
        end = leaders[block_index + 1] if block_index + 1 < len(leaders) else len(instructions)
        block_instructions = instructions[leader:end]
        block = BasicBlock(block_id=block_index, instructions=block_instructions)
        for instr in block_instructions:
            if instr.op == "label":
                block.labels.append(instr.result)
        blocks.append(block)
    return blocks


def format_basic_blocks(blocks: List[BasicBlock]) -> str:
    lines: List[str] = []
    for block in blocks:
        lines.append(block.title())
        for instr in block.instructions:
            lines.append(f"  {instr}")
        lines.append("")
    return "\n".join(lines).strip()
