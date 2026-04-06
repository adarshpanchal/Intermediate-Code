"""
main.py

Simple CLI entry point for the academic optimization pipeline.
"""

from __future__ import annotations

from optimizer_engine import process_code


SAMPLE_PROGRAM = """function main() {
    int a;
    int b;
    int c;

    a = 2;
    b = 3;
    c = a + b;

    if (c > 4) {
        c = a + b;
    } else {
        c = a * b;
    }

    return c;
}"""


def main() -> None:
    result = process_code(SAMPLE_PROGRAM)
    for title, body in [
        ("Original TAC", result["original_tac"]),
        ("Basic Blocks", result["basic_blocks"]),
        ("CFG", result["cfg"]),
        ("Optimized TAC", result["optimized_tac"]),
        ("SSA Form", result["ssa_form"]),
    ]:
        print(f"\n=== {title} ===")
        print(body)


if __name__ == "__main__":
    main()
