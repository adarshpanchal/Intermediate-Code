

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from basic_blocks import BasicBlock


@dataclass
class ControlFlowGraph:
    adjacency: Dict[int, Set[int]] = field(default_factory=dict)
    predecessors: Dict[int, Set[int]] = field(default_factory=dict)


def build_cfg(blocks: List[BasicBlock]) -> ControlFlowGraph:
    label_to_block: Dict[str, int] = {}
    for block in blocks:
        for label in block.labels:
            label_to_block[label] = block.block_id

    adjacency: Dict[int, Set[int]] = {block.block_id: set() for block in blocks}
    predecessors: Dict[int, Set[int]] = {block.block_id: set() for block in blocks}

    for index, block in enumerate(blocks):
        if not block.instructions:
            continue
        last = block.instructions[-1]
        if last.op == "goto" and last.result in label_to_block:
            target = label_to_block[last.result]
            adjacency[block.block_id].add(target)
            predecessors[target].add(block.block_id)
        elif last.op == "ifFalse":
            if last.result in label_to_block:
                target = label_to_block[last.result]
                adjacency[block.block_id].add(target)
                predecessors[target].add(block.block_id)
            if index + 1 < len(blocks):
                fallthrough = blocks[index + 1].block_id
                adjacency[block.block_id].add(fallthrough)
                predecessors[fallthrough].add(block.block_id)
        elif last.op != "return" and index + 1 < len(blocks):
            fallthrough = blocks[index + 1].block_id
            adjacency[block.block_id].add(fallthrough)
            predecessors[fallthrough].add(block.block_id)

    return ControlFlowGraph(adjacency=adjacency, predecessors=predecessors)


def format_cfg(cfg: ControlFlowGraph) -> str:
    lines: List[str] = []
    for block_id in sorted(cfg.adjacency):
        edges = ", ".join(f"B{target}" for target in sorted(cfg.adjacency[block_id]))
        lines.append(f"B{block_id} -> [{edges}]")
    return "\n".join(lines)
