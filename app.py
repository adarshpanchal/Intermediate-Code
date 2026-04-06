"""
app.py

Flask frontend for the intermediate representation optimization system.
The web layer only calls process_code(input_code) from optimizer_engine.py.
"""

from __future__ import annotations

from flask import Flask, render_template, request

from optimizer_engine import process_code


app = Flask(__name__)


DEFAULT_SAMPLE = """function helper(int a, int b) {
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
}"""


@app.route("/", methods=["GET", "POST"])
def index():
    code = DEFAULT_SAMPLE
    results = None
    error = None

    if request.method == "POST":
        code = request.form.get("code", "")
        try:
            results = process_code(code)
        except Exception as exc:
            error = str(exc)

    return render_template("index.html", code=code, results=results, error=error)


if __name__ == "__main__":
    app.run(debug=True)
