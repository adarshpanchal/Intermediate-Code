

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from basic_blocks import format_basic_blocks, form_basic_blocks
from cfg import build_cfg, format_cfg
from dag_optimizer import flatten_blocks, optimize_blocks
from parser import parse_source
from ssa_converter import convert_to_ssa, format_ssa
from tac_generator import generate_tac


@dataclass
class OptimizationOutput:
    original_tac: str
    basic_blocks: str
    cfg: str
    optimized_tac: str
    ssa_form: str

    def as_dict(self) -> Dict[str, str]:
        return {
            "original_tac": self.original_tac,
            "basic_blocks": self.basic_blocks,
            "cfg": self.cfg,
            "optimized_tac": self.optimized_tac,
            "ssa_form": self.ssa_form,
        }


def process_code(input_code: str) -> Dict[str, str]:
    program = parse_source(input_code)
    tac = generate_tac(program)
    blocks = form_basic_blocks(tac)
    cfg = build_cfg(blocks)
    optimized_blocks = optimize_blocks(blocks)
    optimized_tac = flatten_blocks(optimized_blocks)
    ssa = convert_to_ssa(optimized_blocks, cfg)

    result = OptimizationOutput(
        original_tac="\n".join(str(instr) for instr in tac),
        basic_blocks=format_basic_blocks(blocks),
        cfg=format_cfg(cfg),
        optimized_tac="\n".join(str(instr) for instr in optimized_tac),
        ssa_form=format_ssa(ssa),
    )
    return result.as_dict()
