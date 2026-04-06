# Intermediate Representation Optimization System

This project is an academic Python implementation of an intermediate representation optimization pipeline with a Flask frontend.

## Features

- Simplified C-like input
- Three Address Code generation
- Basic block formation
- Control Flow Graph construction
- DAG-style local optimization
- SSA conversion with simple phi insertion
- Clean Flask UI

## Project Structure

```text
project/
├── app.py
├── optimizer_engine.py
├── parser.py
├── tac_generator.py
├── basic_blocks.py
├── cfg.py
├── dag_optimizer.py
├── ssa_converter.py
├── main.py
├── requirements.txt
├── templates/
│   └── index.html
└── static/
    └── style.css
```

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run The Web App

```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Run The CLI Demo

```bash
python main.py
```

## Example Input

```c
function helper(int a, int b) {
    int c;
    c = a + b;
    return c;
}

function main() {
    int a;
    int b;
    int c;
    int arr[5];

    a = 4;
    b = 6;
    c = a + b;
    arr[0] = c;

    if (a < b) {
        c = a + b;
    } else {
        c = a * b;
    }

    while (a < 10) {
        a = a + 1;
        c = c + a;
    }

    c = helper(a, c);
    return c;
}
```

## Phase Explanation

1. `parser.py` reads simplified C-like syntax and builds an abstract syntax tree.
2. `tac_generator.py` lowers the AST to three-address code using temporaries like `t1`, `t2`, and labels like `L1`.
3. `basic_blocks.py` identifies leaders and splits TAC into basic blocks.
4. `cfg.py` builds an adjacency-list control flow graph from the basic blocks.
5. `dag_optimizer.py` performs local optimization inside each basic block using value numbering to model DAG behavior.
6. `ssa_converter.py` rewrites assignments into SSA-style versions and inserts simple phi nodes at merge points.

## Example Output Shape

The app displays these sections independently:

- Original TAC
- Basic Blocks
- CFG
- Optimized TAC
- SSA Form

This keeps each compiler phase visible for teaching and experimentation.
