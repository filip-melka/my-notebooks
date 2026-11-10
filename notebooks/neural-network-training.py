import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="Neural Network Training Made Simple")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    import anywidget
    import traitlets
    from wigglystuff import FloatingPanel

    return FloatingPanel, anywidget, mo, np, traitlets


@app.cell(hide_code=True)
def _(anywidget, traitlets):
    class SigmoidCalculator(anywidget.AnyWidget):
        """Computes σ(x) and σ'(x) in the browser, so the floating panel
        never re-renders (and never jumps back to its corner)."""

        x = traitlets.Float(0.0).tag(sync=True)
        sigmoid = traitlets.Float(0.5).tag(sync=True)
        derivative = traitlets.Float(0.25).tag(sync=True)

        _esm = """
        function sigmoid(x) {
          // numerically stable for large |x|
          if (x >= 0) return 1 / (1 + Math.exp(-x));
          const e = Math.exp(x);
          return e / (1 + e);
        }
        function fmt(v) {
          if (v === 0) return "0";
          const a = Math.abs(v);
          return a < 1e-4 || a >= 1e6 ? v.toExponential(4) : String(+v.toPrecision(6));
        }
        function render({ model, el }) {
          el.innerHTML = `
            <div class="sc">
              <label class="sc-in">x =
                <input type="number" step="any" value="${model.get("x")}">
              </label>
              <div class="sc-row"><span>σ(x)</span><code data-k="s"></code></div>
              <div class="sc-row"><span>σ′(x) = σ(x)(1 − σ(x))</span><code data-k="d"></code></div>
            </div>`;
          const input = el.querySelector("input");
          const out = (k) => el.querySelector(`[data-k="${k}"]`);
          function update() {
            const x = parseFloat(input.value);
            if (!Number.isFinite(x)) { out("s").textContent = out("d").textContent = "—"; return; }
            const s = sigmoid(x), d = s * (1 - s);
            out("s").textContent = fmt(s);
            out("d").textContent = fmt(d);
            model.set("x", x); model.set("sigmoid", s); model.set("derivative", d);
            model.save_changes();
          }
          input.addEventListener("input", update);
          update();

          async function copy(text) {
            try {
              await navigator.clipboard.writeText(text);
            } catch {
              // fallback for iframes where the Clipboard API is blocked
              const ta = document.createElement("textarea");
              ta.value = text;
              ta.style.cssText = "position:fixed;opacity:0";
              document.body.appendChild(ta);
              ta.select();
              document.execCommand("copy");
              ta.remove();
            }
          }
          el.querySelectorAll("code").forEach((c) => {
            c.title = "Click to copy";
            c.addEventListener("click", async () => {
              const text = c.textContent;
              if (text === "—" || c.classList.contains("copied")) return;
              await copy(text);
              c.classList.add("copied");
              c.textContent = "Copied!";
              setTimeout(() => {
                c.classList.remove("copied");
                update();
              }, 900);
            });
          });
        }
        export default { render };
        """

        _css = """
        .sc { display: flex; flex-direction: column; gap: 8px; min-width: 240px;
              font-family: system-ui, sans-serif; font-size: 14px; }
        .sc-in { display: flex; align-items: center; gap: 8px; font-weight: 600; }
        .sc-in input { flex: 1; padding: 4px 8px; font: inherit; font-weight: 400;
                       border: 1px solid #8884; border-radius: 6px;
                       background: transparent; color: inherit; }
        .sc-row { display: flex; justify-content: space-between; gap: 16px; }
        .sc-row code { font-variant-numeric: tabular-nums; cursor: pointer;
                       padding: 0 4px; border-radius: 4px;
                       transition: background 0.15s; }
        .sc-row code:hover { background: #8882; }
        .sc-row code.copied { color: #16a34a; }
        """

    return (SigmoidCalculator,)


@app.cell(hide_code=True)
def _(FloatingPanel, SigmoidCalculator, mo):
    sigmoid_calc = mo.ui.anywidget(SigmoidCalculator())

    calculator = FloatingPanel(
        sigmoid_calc, corner="top-right", title="Sigmoid calculator"
    )

    calculator
    return


@app.cell(hide_code=True)
def _(FloatingPanel, network_svg):
    # The network's structure (node names only), always one click away while
    # reading. Starts collapsed so it doesn't cover the text.
    _nodes = {
        "A": (60, 70, ""),
        "B": (60, 190, ""),
        "C (bias)": (150, 290, ""),
        "D": (290, 70, ""),
        "E": (290, 190, ""),
        "F (bias)": (390, 290, ""),
        "G": (460, 130, ""),
    }
    _edges = [
        (_src, _dst, 0, 0.5, 1)
        for _src, _dst in [
            ("A", "D"), ("A", "E"), ("B", "D"), ("B", "E"),
            ("C (bias)", "D"), ("C (bias)", "E"),
            ("D", "G"), ("E", "G"), ("F (bias)", "G"),
        ]
    ]

    FloatingPanel(
        network_svg(
            _nodes, _edges, width=510, height=330,
            show_weights=False, labels_inside=True,
        ),
        corner="top-left",
        width=360,
        collapsed=True,
        title="Network",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Neural Network Training Made Simple

    Every neural network learns the same way: it makes a guess, measures how wrong the guess is, and nudges every weight so the next guess is a little less wrong. In this notebook we'll do that once, by hand, on a tiny network with just 9 weights. All you need is high-school algebra and the idea of a slope. While you read, the **Network** panel (top left, click to expand) shows how the nodes are connected, and the **Sigmoid calculator** (top right) does the arithmetic for you.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    def network_svg(
        nodes, edges, target=None, width=600, height=340, r=24, clickable=False,
        highlight=None, show_weights=True, labels_inside=False,
    ):
        """Draw a small feed-forward network as an inline SVG.

        nodes: {name: (x, y, value_text)}
        edges: [(src, dst, weight, t, side)] - the weight label sits at fraction
               `t` along the edge, nudged to `side` (+1 / -1) of the line.
        clickable: add a wide invisible hit area to each edge, so a widget can
               make connections clickable. Every edge is wrapped in
               <g data-edge="AD"> (first letters of its two nodes) either way.
        highlight: optional set of edge keys (e.g. {"DG", "EG"}); all other
               edges are drawn faded.
        show_weights: False draws plain grey connections with no weight labels.
        labels_inside: write the node's letter inside its circle (and "bias"
               above bias nodes) instead of the name above and the value inside.
        """
        parts = [
            f'<svg viewBox="0 0 {width} {height}" width="100%" '
            f'style="max-width:{width}px;font-family:system-ui,sans-serif;color:inherit">',
            '<defs><marker id="nn-arrow" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            '<path d="M0,0 L10,5 L0,10 z" fill="context-stroke"/></marker></defs>',
        ]
        for src, dst, w, t, side in edges:
            x1, y1, _ = nodes[src]
            x2, y2, _ = nodes[dst]
            dx, dy = x2 - x1, y2 - y1
            d = (dx**2 + dy**2) ** 0.5
            ux, uy = dx / d, dy / d
            sx, sy = x1 + ux * r, y1 + uy * r
            ex, ey = x2 - ux * (r + 2), y2 - uy * (r + 2)
            if show_weights:
                color = "#2563eb" if w >= 0 else "#dc2626"
                stroke_w = 0.75 + 2.5 * min(abs(w), 1.5)
            else:
                color, stroke_w = "currentColor", 1.5
            key = f"{src[0]}{dst[0]}"
            faded = highlight is not None and key not in highlight
            fade_attr = ' opacity="0.25"' if faded else ""
            parts.append(f'<g data-edge="{key}"{fade_attr}>')
            if clickable:
                parts.append(
                    f'<line class="hit" x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex:.1f}" '
                    f'y2="{ey:.1f}" stroke="transparent" stroke-width="18"/>'
                )
            parts.append(
                f'<line class="edge" x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
                f'stroke="{color}" stroke-width="{stroke_w:.2f}" stroke-opacity="0.8" '
                f'marker-end="url(#nn-arrow)"/>'
            )
            lx = sx + (ex - sx) * t - uy * 11 * side
            ly = sy + (ey - sy) * t + ux * 11 * side
            if show_weights:
                parts.append(
                    f'<text x="{lx:.1f}" y="{ly + 4:.1f}" font-size="12" '
                    f'text-anchor="middle" fill="{color}">{w:+.2f}</text>'
                )
            parts.append("</g>")
        for name, (x, y, val) in nodes.items():
            if labels_inside:
                parts.append(
                    f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" '
                    f'stroke="currentColor" stroke-width="1.5"/>'
                    f'<text x="{x}" y="{y + 6}" font-size="17" font-weight="600" '
                    f'text-anchor="middle" fill="currentColor">{name[0]}</text>'
                )
                if "bias" in name:
                    parts.append(
                        f'<text x="{x}" y="{y - r - 8}" font-size="12" text-anchor="middle" '
                        f'fill="currentColor" fill-opacity="0.7">bias</text>'
                    )
                continue
            parts.append(
                f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" '
                f'stroke="currentColor" stroke-width="1.5"/>'
                f'<text x="{x}" y="{y + 4}" font-size="13" text-anchor="middle" '
                f'fill="currentColor">{val}</text>'
                f'<text x="{x}" y="{y - r - 8}" font-size="13" font-weight="600" '
                f'text-anchor="middle" fill="currentColor">{name}</text>'
            )
        if target is not None:
            gx, gy, _ = nodes["G"]
            parts.append(
                f'<text x="{gx + r + 12}" y="{gy + 4}" font-size="13" '
                f'fill="currentColor">target t = {target:g}</text>'
            )
        parts.append("</svg>")
        return mo.Html("".join(parts))

    return (network_svg,)


@app.cell(hide_code=True)
def _(np):
    # Small random weights keep the sigmoid out of its flat, saturated regions,
    # so gradients are healthy at the start of training. Fixed seed => the
    # article shows the same numbers on every run.
    _rng = np.random.default_rng(seed=7)
    _names = ["AD", "AE", "BD", "BE", "CD", "CE", "DG", "EG", "FG"]
    weights = dict(zip(_names, np.round(_rng.uniform(-0.5, 0.5, len(_names)), 2)))
    inputs = {"A": 1.0, "B": 0.0}
    target = 1.0
    learning_rate = 0.5  # μ: how big a step each update takes
    return inputs, learning_rate, target, weights


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The Setup

    Let's consider the following Neural Network. It has:

    - Two input nodes
    - Two hidden nodes
    - One output node
    - Two bias nodes

    Every connection between two nodes has an assigned weight. When we start, these weights are assigned randomly. The goal of training the Neural Network is to adjust these weights so that for each given input we get the desired output.

    A bias node always outputs 1. Its outgoing weights, called the **biases**, are learned just like any other weight. A bias lets a node shift its weighted sum up or down, whatever its inputs are. Without it, a node whose inputs are all 0 would always have a weighted sum of 0, no matter what its weights are.

    We'll be using a single example for out training and we'll walk through exactly one training step:

    - Compute a prediction
    - Measure the error
    - Update all weights

    Finally, we'll check that the network prediction's have improved.
    """)
    return


@app.cell(hide_code=True)
def _(inputs, network_svg, target, weights):
    _nodes = {
        "A": (60, 70, f"{inputs['A']:.1f}"),
        "B": (60, 190, f"{inputs['B']:.1f}"),
        "C (bias)": (150, 290, "1"),
        "D": (290, 70, ""),
        "E": (290, 190, ""),
        "F (bias)": (390, 290, "1"),
        "G": (460, 130, ""),
    }
    _edges = [
        ("A", "D", weights["AD"], 0.5, 1),
        ("A", "E", weights["AE"], 0.2, -1),
        ("B", "D", weights["BD"], 0.2, 1),
        ("B", "E", weights["BE"], 0.5, -1),
        ("C (bias)", "D", weights["CD"], 0.35, 1),
        ("C (bias)", "E", weights["CE"], 0.5, -1),
        ("D", "G", weights["DG"], 0.5, 1),
        ("E", "G", weights["EG"], 0.5, 1),
        ("F (bias)", "G", weights["FG"], 0.5, -1),
    ]
    network_svg(_nodes, _edges, target=target)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Forward Pass

    Before we can start adjusting, we need to know what's the current prediction of the network. We'll perform a **forward pass**.

    A network turns an input into a prediction by multiplying by weights, applying an activation function, and repeating layer by layer.

    ### Node's activation

    Each node, sometimes called a _unit_, has its own activation level. For any node in the hidden (and output) layer, this activation level ($y$) is given by the weighted sum of all connections going to this node, passed through an activation function.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Formally, computing a node's activation takes two steps.

    **1. Weighted sum.** For node $j$, multiply the activation $y_i$ of every node $i$ connected to it by the weight $w_{ij}$ of that connection, and add the results:

    $$
    x_j = \sum_{i} y_i \, w_{ij}
    $$

    A bias node is treated like any other node whose activation is always $y = 1$, so its weight is simply added to the sum.

    **2. Activation level.** Pass the weighted sum through the activation function. Here we use the **sigmoid** $\sigma$:

    $$
    y_j = \sigma(x_j) = \frac{1}{1 + e^{-x_j}}
    $$

    The sigmoid squashes any real number into the range $(0, 1)$: large positive sums give activations close to 1, large negative sums give activations close to 0.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Let's take a look at node $D$ in our network:
    """)
    return


@app.cell(hide_code=True)
def _(inputs, network_svg, weights):
    # Zoom in on hidden node D: only the three connections that feed into it.
    _nodes = {
        "A": (60, 50, f"{inputs['A']:.1f}"),
        "B": (60, 150, f"{inputs['B']:.1f}"),
        "C (bias)": (60, 250, "1"),
        "D": (320, 150, "?"),
    }
    _edges = [
        ("A", "D", weights["AD"], 0.5, -1),
        ("B", "D", weights["BD"], 0.5, -1),
        ("C (bias)", "D", weights["CD"], 0.5, 1),
    ]
    network_svg(_nodes, _edges, width=400, height=290)
    return


@app.cell(hide_code=True)
def _(inputs, mo, np, weights):
    _x_D = (
        inputs["A"] * weights["AD"]
        + inputs["B"] * weights["BD"]
        + 1.0 * weights["CD"]
    )
    _y_D = 1 / (1 + np.exp(-_x_D))

    mo.md(
        r"For node $D$, the weighted sum is"
        "\n\n$$\n"
        r"\begin{aligned}"
        r"x_D &= y_A w_{AD} + y_B w_{BD} + y_C w_{CD} \\"
        f"&= {inputs['A']:g} \\cdot ({weights['AD']:g}) "
        f"+ {inputs['B']:g} \\cdot ({weights['BD']:g}) "
        f"+ 1 \\cdot ({weights['CD']:g}) \\\\"
        f"&= {_x_D:.4f}"
        r"\end{aligned}"
        "\n$$\n\n"
        "and its activation level is"
        "\n\n$$\n"
        f"y_D = \\sigma({_x_D:.4f}) = {_y_D:.4f}"
        "\n$$\n\n"
        "You can check this with the sigmoid calculator in the top-right corner."
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Your turn. These are the connections that feed into node $E$:
    """)
    return


@app.cell(hide_code=True)
def _(inputs, network_svg, weights):
    # Zoom in on hidden node E: only the three connections that feed into it.
    _nodes = {
        "A": (60, 50, f"{inputs['A']:.1f}"),
        "B": (60, 150, f"{inputs['B']:.1f}"),
        "C (bias)": (60, 250, "1"),
        "E": (320, 150, "?"),
    }
    _edges = [
        ("A", "E", weights["AE"], 0.5, -1),
        ("B", "E", weights["BE"], 0.5, -1),
        ("C (bias)", "E", weights["CE"], 0.5, 1),
    ]
    network_svg(_nodes, _edges, width=400, height=290)
    return


@app.cell(hide_code=True)
def _(mo):
    # Quiz: the activation of node E (value updates on "Check").
    answer_form = (
        mo.md(
            r"""
    **Quick check: what is the activation level of node $E$? Round to at least 3 decimal places.**

    $y_E =$ {y_E}
    """
        )
        .batch(y_E=mo.ui.text(placeholder="e.g. 0.42"))
        .form(submit_button_label="Check", bordered=False)
    )
    answer_form
    return (answer_form,)


@app.cell(hide_code=True)
def _(answer_form, inputs, mo, np, weights):
    # Recompute node E from the actual network, so the check follows the weights.
    _x_E = (
        inputs["A"] * weights["AE"]
        + inputs["B"] * weights["BE"]
        + 1.0 * weights["CE"]
    )
    _y_E = 1 / (1 + np.exp(-_x_E))
    _tol = 0.005  # accept answers rounded to 2 decimal places

    _raw = answer_form.value["y_E"] if answer_form.value else None
    if _raw is None:
        _feedback = None
    else:
        try:
            _guess = float(_raw.strip().replace(",", "."))
        except ValueError:
            _guess = None

        if _guess is None:
            _feedback = mo.callout(
                mo.md(f"`{_raw}` isn't a number. Try again."), kind="warn"
            )
        elif abs(_guess - _y_E) <= _tol:
            _feedback = mo.callout(
                mo.md(
                    f"**Correct!** $x_E = {_x_E:.4f}$, so "
                    f"$y_E = \\sigma({_x_E:.4f}) = {_y_E:.4f}$."
                ),
                kind="success",
            )
        elif abs(_guess - _x_E) <= _tol:
            _feedback = mo.callout(
                mo.md(
                    "That's the **weighted sum** $x_E$. "
                    "Don't forget to pass it through the sigmoid."
                ),
                kind="warn",
            )
        else:
            _feedback = mo.callout(
                mo.md(
                    "Not quite. Compute the weighted sum $x_E$ first, "
                    "then apply $\\sigma$ to it."
                ),
                kind="danger",
            )

    _feedback
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now we have the activation levels of both hidden nodes. Finally, we do the same for the output node.
    """)
    return


@app.cell
def _(inputs, np, weights):
    def sigmoid(x):
        return 1 / (1 + np.exp(-x))


    def forward(w, inputs):
        """Forward pass through the whole network. Bias nodes C and F are always 1."""
        y = {"A": inputs["A"], "B": inputs["B"], "C": 1.0, "F": 1.0}
        y["D"] = sigmoid(y["A"] * w["AD"] + y["B"] * w["BD"] + y["C"] * w["CD"])
        y["E"] = sigmoid(y["A"] * w["AE"] + y["B"] * w["BE"] + y["C"] * w["CE"])
        y["G"] = sigmoid(y["D"] * w["DG"] + y["E"] * w["EG"] + y["F"] * w["FG"])
        return y


    activations = forward(weights, inputs)
    return activations, forward


@app.cell(hide_code=True)
def _(activations, network_svg, target, weights):
    # Same layout as the setup diagram, now with every activation filled in.
    _nodes = {
        "A": (60, 70, f"{activations['A']:.1f}"),
        "B": (60, 190, f"{activations['B']:.1f}"),
        "C (bias)": (150, 290, "1"),
        "D": (290, 70, f"{activations['D']:.3f}"),
        "E": (290, 190, f"{activations['E']:.3f}"),
        "F (bias)": (390, 290, "1"),
        "G": (460, 130, f"{activations['G']:.3f}"),
    }
    _edges = [
        ("A", "D", weights["AD"], 0.5, 1),
        ("A", "E", weights["AE"], 0.2, -1),
        ("B", "D", weights["BD"], 0.2, 1),
        ("B", "E", weights["BE"], 0.5, -1),
        ("C (bias)", "D", weights["CD"], 0.35, 1),
        ("C (bias)", "E", weights["CE"], 0.5, -1),
        ("D", "G", weights["DG"], 0.5, 1),
        ("E", "G", weights["EG"], 0.5, 1),
        ("F (bias)", "G", weights["FG"], 0.5, -1),
    ]
    network_svg(_nodes, _edges, target=target)
    return


@app.cell(hide_code=True)
def _(activations, mo, target):
    mo.md(rf"""
    ## Squared Error Loss

    The prediction of our network is ${activations["G"]:.3f}$. The actual value (_target_) is ${target:g}$.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    # Quiz: is the prediction too high or too low? (value updates on "Check")
    over_under_quiz = mo.ui.radio(
        options=[
            "Overestimating (the prediction is too high)",
            "Underestimating (the prediction is too low)",
            "Neither (the prediction is spot on)",
        ],
        label="**Quick check:** is the network overestimating or underestimating the target?",
    ).form(submit_button_label="Check", bordered=False)
    over_under_quiz
    return (over_under_quiz,)


@app.cell(hide_code=True)
def _(activations, mo, over_under_quiz, target):
    _y, _t = activations["G"], target
    _correct = "Over" if _y > _t else ("Under" if _y < _t else "Neither")
    _push = "down" if _y > _t else "up"
    _answer = over_under_quiz.value

    if _answer is None:
        _feedback = None
    elif _answer.startswith(_correct):
        _feedback = mo.callout(
            mo.md(
                f"**Correct!** The prediction $y_G = {_y:.3f}$ is "
                f"{'above' if _y > _t else 'below'} the target $t = {_t:g}$, "
                f"so training should push $y_G$ **{_push}**. Keep this in mind: "
                "the direction of the error will decide which way every weight moves."
            ),
            kind="success",
        )
    elif _answer.startswith("Neither"):
        _feedback = mo.callout(
            mo.md(
                f"Not quite. The prediction ${_y:.3f}$ and the target ${_t:g}$ are "
                f"{abs(_t - _y):.3f} apart, so there's still an error to fix."
            ),
            kind="danger",
        )
    else:
        _feedback = mo.callout(
            mo.md(
                f"Not quite. Compare the two numbers: the prediction ${_y:.3f}$ is "
                f"**{'larger' if _y > _t else 'smaller'}** than the target ${_t:g}$."
            ),
            kind="danger",
        )

    _feedback
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    To measure the error we use **squared error loss**. It measures how far the neural network's prediction is from the desired output.

    $$
    L=(t-y)^2
    $$

    Here:

    - $t$ = target (correct) output
    - $y$ = predicted output
    - $t-y$ = prediction error

    By squaring the prediction error we achieve two things:

    - It makes the error positive (no matter whether the network overestimates or underestimates)
    - It penalises larger errors more heavily

    For mathematical convenience, we also multiply the entire expression by $\frac{1}{2}$ (you'll see why in a moment):

    $$
    L=\frac{1}{2}(t-y)^2
    $$

    We call this the **loss** $L$. In our case, $y$ is the output node's activation $y_G$.

    ### Error as a function of weights

    We can view training as an _optimisation problem_. The goal is to find weights that make the error small.

    You can play around with the weights (which are still random) and see how the error changes.
    """)
    return


@app.cell(hide_code=True)
def _(mo, weights):
    # One slider per weight, starting at the network's random initial weights.
    weight_sliders = mo.ui.dictionary(
        {
            _k: mo.ui.slider(
                -3.0, 3.0, step=0.01, value=float(_w),
                label=f"$w_{{{_k}}}$", show_value=True,
            )
            for _k, _w in weights.items()
        }
    )
    return (weight_sliders,)


@app.cell(hide_code=True)
def _(activations, forward, inputs, mo, network_svg, target, weight_sliders):
    _w = weight_sliders.value

    # Forward pass with the slider weights.
    _y = forward(_w, inputs)
    _y_A, _y_B, _y_D, _y_E, _y_G = (_y[_k] for _k in "ABDEG")

    _error = 0.5 * (target - _y_G) ** 2
    _initial_error = 0.5 * (target - activations["G"]) ** 2

    _nodes = {
        "A": (60, 70, f"{_y_A:.1f}"),
        "B": (60, 190, f"{_y_B:.1f}"),
        "C (bias)": (150, 290, "1"),
        "D": (290, 70, f"{_y_D:.3f}"),
        "E": (290, 190, f"{_y_E:.3f}"),
        "F (bias)": (390, 290, "1"),
        "G": (460, 130, f"{_y_G:.3f}"),
    }
    _edges = [
        ("A", "D", _w["AD"], 0.5, 1),
        ("A", "E", _w["AE"], 0.2, -1),
        ("B", "D", _w["BD"], 0.2, 1),
        ("B", "E", _w["BE"], 0.5, -1),
        ("C (bias)", "D", _w["CD"], 0.35, 1),
        ("C (bias)", "E", _w["CE"], 0.5, -1),
        ("D", "G", _w["DG"], 0.5, 1),
        ("E", "G", _w["EG"], 0.5, 1),
        ("F (bias)", "G", _w["FG"], 0.5, -1),
    ]

    # Sliders grouped by the node they feed into.
    _groups = {"Into D": ["AD", "BD", "CD"], "Into E": ["AE", "BE", "CE"], "Into G": ["DG", "EG", "FG"]}
    _slider_grid = mo.hstack(
        [
            mo.vstack([mo.md(f"**{_title}**")] + [weight_sliders[_k] for _k in _keys])
            for _title, _keys in _groups.items()
        ],
        justify="space-between",
        widths="equal",
    )

    _stats = mo.hstack(
        [
            mo.stat(f"{_y_G:.4f}", label="Prediction y", caption=f"target t = {target:g}"),
            mo.stat(
                f"{_error:.4f}",
                label="Loss L = ½(t − y)²",
                caption=f"random weights: {_initial_error:.4f}",
                direction="decrease" if _error < _initial_error else (
                    "increase" if _error > _initial_error else None
                ),
                target_direction="decrease",
            ),
        ],
        justify="start",
        gap=2,
    )

    mo.vstack([_slider_grid, network_svg(_nodes, _edges, target=target), _stats], gap=1.5)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Which Way Should Each Weight Move?

    Moving sliders by hand doesn't scale. A real network has millions of weights. Training needs an automatic way to answer one question for every weight:

    > _If I increase this weight a tiny bit, does the loss go up or down, and how fast?_

    That answer is the **gradient** $\frac{\partial L}{\partial w}$: the slope of the loss when we change just that one weight and keep all the others fixed.

    - Slope **positive**: increasing $w$ increases the loss, so we should **decrease** $w$.
    - Slope **negative**: increasing $w$ decreases the loss, so we should **increase** $w$.
    - The **steeper** the slope, the more that weight matters right now, and the bigger the step.

    **Click any connection** in the network to pick a weight. The curve next to it shows the loss as that one weight changes, with all other weights kept at their random starting values.
    """)
    return


@app.cell(hide_code=True)
def _(anywidget, traitlets):
    class NetworkPicker(anywidget.AnyWidget):
        """Shows a network SVG and lets the reader click a connection to select
        it. `selected` holds the edge key, e.g. "DG"."""

        svg = traitlets.Unicode("").tag(sync=True)
        selected = traitlets.Unicode("").tag(sync=True)

        _esm = """
        function render({ model, el }) {
          const root = document.createElement("div");
          root.className = "np";
          el.appendChild(root);

          function apply() {
            const sel = model.get("selected");
            root.classList.toggle("has-sel", !!sel);
            root.querySelectorAll("[data-edge]").forEach((g) =>
              g.classList.toggle("sel", g.dataset.edge === sel)
            );
          }
          function pick(key) {
            model.set("selected", key);
            model.save_changes();
            apply();
          }
          function draw() {
            root.innerHTML = model.get("svg") +
              '<div class="np-hint">Click a connection to pick its weight</div>';
            root.querySelectorAll("[data-edge]").forEach((g) => {
              const key = g.dataset.edge;
              g.setAttribute("tabindex", "0");
              g.setAttribute("role", "button");
              g.setAttribute("aria-label", "weight w_" + key);
              g.addEventListener("click", () => pick(key));
              g.addEventListener("keydown", (e) => {
                if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pick(key); }
              });
            });
            apply();
          }
          model.on("change:svg", draw);
          model.on("change:selected", apply);
          draw();
        }
        export default { render };
        """

        _css = """
        .np [data-edge] { cursor: pointer; outline: none; transition: opacity 0.15s; }
        .np.has-sel [data-edge]:not(.sel) { opacity: 0.25; }
        .np.has-sel [data-edge]:not(.sel):hover { opacity: 0.7; }
        .np [data-edge].sel .edge { stroke: #f97316; stroke-opacity: 1; }
        .np [data-edge].sel text { fill: #f97316; font-weight: 700; }
        .np [data-edge]:focus-visible .hit { stroke: rgba(249, 115, 22, 0.25); }
        .np-hint { font-size: 12px; opacity: 0.6; text-align: center;
                   font-family: system-ui, sans-serif; margin-top: 4px; }
        """

    return (NetworkPicker,)


@app.cell(hide_code=True)
def _(NetworkPicker, activations, mo, network_svg, target, weights):
    _nodes = {
        "A": (60, 70, f"{activations['A']:.1f}"),
        "B": (60, 190, f"{activations['B']:.1f}"),
        "C (bias)": (150, 290, "1"),
        "D": (290, 70, f"{activations['D']:.3f}"),
        "E": (290, 190, f"{activations['E']:.3f}"),
        "F (bias)": (390, 290, "1"),
        "G": (460, 130, f"{activations['G']:.3f}"),
    }
    _edges = [
        ("A", "D", weights["AD"], 0.5, 1),
        ("A", "E", weights["AE"], 0.2, -1),
        ("B", "D", weights["BD"], 0.2, 1),
        ("B", "E", weights["BE"], 0.5, -1),
        ("C (bias)", "D", weights["CD"], 0.35, 1),
        ("C (bias)", "E", weights["CE"], 0.5, -1),
        ("D", "G", weights["DG"], 0.5, 1),
        ("E", "G", weights["EG"], 0.5, 1),
        ("F (bias)", "G", weights["FG"], 0.5, -1),
    ]
    weight_picker = mo.ui.anywidget(
        NetworkPicker(
            svg=network_svg(_nodes, _edges, target=target, clickable=True).text,
            selected="DG",
        )
    )
    return (weight_picker,)


@app.cell(hide_code=True)
def _(forward, inputs, mo, np, target, weight_picker, weights):
    _k = weight_picker.value["selected"] or "DG"


    def _loss(w_k):
        _y = forward({**weights, _k: w_k}, inputs)
        return 0.5 * (target - _y["G"]) ** 2


    _ws = np.linspace(-3, 3, 241)
    _Ls = np.array([_loss(_v) for _v in _ws])
    _w0 = float(weights[_k])
    _L0 = _loss(_w0)
    _h = 1e-5
    _slope = (_loss(_w0 + _h) - _loss(_w0 - _h)) / (2 * _h)

    # --- hand-drawn SVG plot (no plotting library needed) -------------------
    # Text never sits inside the plot area: the legend goes above it and the
    # "lower loss" arrow goes in its own strip below the x-axis tick labels.
    _W, _H = 520, 360
    _ml, _mr, _mt, _mb = 60, 16, 40, 78
    _Lmax = max(float(_Ls.max()) * 1.1, 1e-3)
    _ORANGE, _BLUE, _GREEN = "#f97316", "#2563eb", "#16a34a"
    _w_sym = (
        '<tspan font-style="italic">w</tspan>'
        f'<tspan baseline-shift="sub" font-size="0.75em">{_k}</tspan>'
    )

    def _px(w):
        return _ml + (w + 3) / 6 * (_W - _ml - _mr)

    def _py(L):
        return _H - _mb - L / _Lmax * (_H - _mt - _mb)

    _parts = [
        f'<svg viewBox="0 0 {_W} {_H}" width="100%" style="max-width:{_W}px;'
        'font-family:system-ui,sans-serif;color:inherit">',
        '<defs><marker id="curve-arrow" viewBox="0 0 10 10" refX="8" refY="5" '
        'markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="11" '
        f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{_GREEN}"/></marker></defs>',
    ]
    # legend (above the plot area)
    _parts.append(
        f'<circle cx="{_ml + 6}" cy="16" r="5" fill="{_ORANGE}"/>'
        f'<text x="{_ml + 16}" y="20" font-size="13" fill="currentColor">current {_w_sym} = {_w0:g}</text>'
        f'<line x1="{_ml + 190}" y1="16" x2="{_ml + 216}" y2="16" stroke="{_ORANGE}" '
        'stroke-width="2" stroke-dasharray="6 4"/>'
        f'<text x="{_ml + 222}" y="20" font-size="13" fill="currentColor">slope (gradient)</text>'
    )
    # axes + ticks
    _x0, _y0 = _ml, _H - _mb
    _parts.append(
        f'<line x1="{_x0}" y1="{_y0}" x2="{_W - _mr}" y2="{_y0}" stroke="currentColor" stroke-opacity="0.5"/>'
        f'<line x1="{_x0}" y1="{_mt}" x2="{_x0}" y2="{_y0}" stroke="currentColor" stroke-opacity="0.5"/>'
    )
    for _t in range(-3, 4):
        _parts.append(
            f'<text x="{_px(_t):.1f}" y="{_y0 + 16}" font-size="11" text-anchor="middle" '
            f'fill="currentColor" fill-opacity="0.7">{_t}</text>'
        )
    for _f in (0, 0.5, 1):
        _v = _Lmax / 1.1 * _f
        _parts.append(
            f'<text x="{_x0 - 6}" y="{_py(_v) + 4:.1f}" font-size="11" text-anchor="end" '
            f'fill="currentColor" fill-opacity="0.7">{_v:.3f}</text>'
        )
    _parts.append(
        f'<text x="{(_W + _ml) / 2}" y="{_H - 6}" font-size="13" text-anchor="middle" '
        f'fill="currentColor">{_w_sym}</text>'
        f'<text x="16" y="{(_mt + _y0) / 2}" font-size="13" text-anchor="middle" '
        f'fill="currentColor" transform="rotate(-90 16 {(_mt + _y0) / 2})">'
        '<tspan font-style="italic">L</tspan> (loss)</text>'
    )
    # loss curve
    _pts = " ".join(f"{_px(a):.1f},{_py(b):.1f}" for a, b in zip(_ws, _Ls))
    _parts.append(f'<polyline points="{_pts}" fill="none" stroke="{_BLUE}" stroke-width="2.5"/>')
    # tangent line (the gradient) around the current weight
    _ta, _tb = max(-3, _w0 - 0.8), min(3, _w0 + 0.8)
    _parts.append(
        f'<line x1="{_px(_ta):.1f}" y1="{_py(_L0 + _slope * (_ta - _w0)):.1f}" '
        f'x2="{_px(_tb):.1f}" y2="{_py(_L0 + _slope * (_tb - _w0)):.1f}" '
        f'stroke="{_ORANGE}" stroke-width="2" stroke-dasharray="6 4"/>'
    )
    # dotted guide from the current point down to the axis
    _parts.append(
        f'<line x1="{_px(_w0):.1f}" y1="{_py(_L0):.1f}" x2="{_px(_w0):.1f}" y2="{_y0}" '
        f'stroke="{_ORANGE}" stroke-opacity="0.6" stroke-dasharray="2 3"/>'
    )
    # "move this way" arrow, opposite to the slope, below the tick labels
    _ay = _y0 + 36
    if abs(_slope) > 1e-9:
        _dir = -1 if _slope > 0 else 1
        _ax = min(max(_px(_w0) + _dir * 70, _ml + 4), _W - _mr - 4)
        _parts.append(
            f'<line x1="{_px(_w0):.1f}" y1="{_ay}" x2="{_ax:.1f}" y2="{_ay}" '
            f'stroke="{_GREEN}" stroke-width="2.5" marker-end="url(#curve-arrow)"/>'
            f'<text x="{(_px(_w0) + _ax) / 2:.1f}" y="{_ay + 17}" font-size="12" '
            f'text-anchor="middle" fill="{_GREEN}">lower loss</text>'
        )
    # current weight
    _parts.append(
        f'<circle cx="{_px(_w0):.1f}" cy="{_py(_L0):.1f}" r="6" fill="{_ORANGE}"/>'
    )
    _parts.append("</svg>")

    if abs(_slope) < 1e-9:
        _note = (
            f"The slope is **0**: this weight multiplies node {_k[0]}, whose activation is 0 "
            "for this input. Changing it has no effect on the prediction, so the gradient "
            "says: leave it alone (for this example)."
        )
    else:
        _verb = "decrease" if _slope > 0 else "increase"
        _note = (
            f"At the current weight the slope (orange) is "
            f"$\\frac{{\\partial L}}{{\\partial w_{{{_k}}}}} \\approx {_slope:.4f}$. "
            f"It's {'positive' if _slope > 0 else 'negative'}, so we should **{_verb}** $w_{{{_k}}}$ "
            f"(green arrow)."
        )

    _plot = mo.vstack(
        [mo.md(f"**Loss as a function of $w_{{{_k}}}$**"), mo.Html("".join(_parts))],
        align="center",
    )
    mo.vstack(
        [
            mo.hstack([weight_picker, _plot], widths=[1, 1], align="center", gap=1.5),
            mo.md(_note),
        ],
        gap=1,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    So every training step does the same thing for every weight: take a small step **against** the slope.

    $$
    w \leftarrow w - \mu \, \frac{\partial L}{\partial w}
    $$

    The **learning rate** $\mu$ is a small number that controls the step size. Too small and training crawls; too big and we overshoot the bottom of the curve.

    Above, we measured the slope by brute force: change the weight a tiny bit and recompute the whole network. That works for one weight, but it's far too slow for millions. Next, we'll find a simple formula for it instead.
    """)
    return


@app.cell(hide_code=True)
def _(activations, mo, network_svg, target, weights):
    # The forward-pass diagram again, with only w_DG drawn at full strength.
    _nodes = {
        "A": (60, 70, f"{activations['A']:.1f}"),
        "B": (60, 190, f"{activations['B']:.1f}"),
        "C (bias)": (150, 290, "1"),
        "D": (290, 70, f"{activations['D']:.3f}"),
        "E": (290, 190, f"{activations['E']:.3f}"),
        "F (bias)": (390, 290, "1"),
        "G": (460, 130, f"{activations['G']:.3f}"),
    }
    _edges = [
        ("A", "D", weights["AD"], 0.5, 1),
        ("A", "E", weights["AE"], 0.2, -1),
        ("B", "D", weights["BD"], 0.2, 1),
        ("B", "E", weights["BE"], 0.5, -1),
        ("C (bias)", "D", weights["CD"], 0.35, 1),
        ("C (bias)", "E", weights["CE"], 0.5, -1),
        ("D", "G", weights["DG"], 0.5, 1),
        ("E", "G", weights["EG"], 0.5, 1),
        ("F (bias)", "G", weights["FG"], 0.5, -1),
    ]

    mo.vstack([
        mo.md(r"""
    ## Final Layer Update

    Let's start with the weights closest to the output: the three weights going into node $G$.

    Let's follow just one of them, $w_{DG}$ (the connection from $D$ to $G$).
    """),
        network_svg(_nodes, _edges, target=target, highlight={"DG"}),
        mo.md(r"""
    This weight doesn't touch the loss directly. Its effect travels through three steps:

    1. $w_{DG}$ changes the **weighted sum** of node $G$, called $x_G$
    2. $x_G$ changes the **prediction** $y_G = \sigma(x_G)$
    3. $y_G$ changes the **loss** $L = \frac{1}{2}(t - y_G)^2$

    Think of it as three gears in a row. Turn the first gear, and the last one turns too, by an amount that depends on the ratio of each pair of gears. So for every step we'll ask one simple question:

    > _If the input to this step goes up by a tiny amount, how much does its output move?_

    We'll call each answer a **rate**. Then we'll combine the three rates.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(activations, target, weights):
    # Everything the final-layer update needs, computed once from the network.
    _y = activations
    _x_G = _y["D"] * weights["DG"] + _y["E"] * weights["EG"] + _y["F"] * weights["FG"]
    output_grad = {
        "x_G": _x_G,
        "y_G": _y["G"],
        "rate2": _y["G"] * (1 - _y["G"]),  # sigmoid slope at x_G
        "rate3": -(target - _y["G"]),  # loss slope at y_G
    }
    output_grad["delta_G"] = -output_grad["rate2"] * output_grad["rate3"]
    return (output_grad,)


@app.cell(hide_code=True)
def _(activations, mo):
    _yD = activations["D"]
    mo.md(rf"""
    ### Step 1: weight → weighted sum

    The weighted sum of node $G$ is

    $$
    x_G = y_D\,w_{{DG}} + y_E\,w_{{EG}} + 1\cdot w_{{FG}}
    $$

    Only the first term contains $w_{{DG}}$. So if $w_{{DG}}$ goes up by some small amount, $x_G$ goes up by $y_D$ times that amount. The other terms don't change.

    In our network $y_D = {_yD:.3f}$, so every $+1$ on the weight adds ${_yD:.3f}$ to $x_G$.

    **Rate 1 = $y_D$ = {_yD:.3f}**
    """)
    return


@app.cell(hide_code=True)
def _(mo, output_grad):
    _x_G, _y_G, _r2 = output_grad["x_G"], output_grad["y_G"], output_grad["rate2"]
    mo.md(rf"""
    ### Step 2: weighted sum → prediction

    The prediction is the weighted sum passed through the sigmoid: $y_G = \sigma(x_G)$. How much $y_G$ moves depends on **how steep the sigmoid is** at $x_G$:

    - near the middle, the curve is steep, so a push on $x_G$ moves the prediction a lot
    - far to the left or right, it's almost flat, so the prediction barely moves

    The steepness of the sigmoid has a neat formula that only needs its output:

    $$
    \sigma'(x) = \sigma(x)\,\bigl(1 - \sigma(x)\bigr)
    \quad\Rightarrow\quad
    \text{{steepness at }} x_G = y_G(1 - y_G)
    $$

    In our network $x_G = {_x_G:.3f}$ and $y_G = {_y_G:.3f}$, so

    **Rate 2 = $y_G(1-y_G)$ = {_y_G:.3f} × {1 - _y_G:.3f} = {_r2:.3f}**

    _Check it yourself:_ type ${_x_G:.4f}$ into the sigmoid calculator (top right) and read off $\sigma'(x)$.
    """)
    return


@app.cell(hide_code=True)
def _(mo, np, output_grad):
    # Sigmoid with the current point x_G and its tangent (slope = rate 2).
    _x0, _y0, _s = output_grad["x_G"], output_grad["y_G"], output_grad["rate2"]
    _W, _H = 480, 270
    _ml, _mr, _mt, _mb = 48, 16, 36, 50
    _ORANGE, _BLUE = "#f97316", "#2563eb"

    def _px(x):
        return _ml + (x + 6) / 12 * (_W - _ml - _mr)

    def _py(y):
        return _H - _mb - y * (_H - _mt - _mb)

    _xs = np.linspace(-6, 6, 241)
    _pts = " ".join(f"{_px(a):.1f},{_py(1 / (1 + np.exp(-a))):.1f}" for a in _xs)
    _ta, _tb = _x0 - 1.6, _x0 + 1.6
    _sub = lambda base, s: (
        f'<tspan font-style="italic">{base}</tspan>'
        f'<tspan baseline-shift="sub" font-size="0.75em">{s}</tspan>'
    )
    _parts = [
        f'<svg viewBox="0 0 {_W} {_H}" width="{_W}" height="{_H}" style="max-width:100%;height:auto;'
        'display:block;margin:0 auto;font-family:system-ui,sans-serif;color:inherit">',
        # legend (outside the plot area)
        f'<circle cx="{_ml + 6}" cy="16" r="5" fill="{_ORANGE}"/>'
        f'<text x="{_ml + 16}" y="20" font-size="13" fill="currentColor">'
        f'our node: {_sub("x", "G")} = {_x0:.3f}, {_sub("y", "G")} = {_y0:.3f}</text>'
        f'<line x1="{_ml + 250}" y1="16" x2="{_ml + 276}" y2="16" stroke="{_ORANGE}" '
        'stroke-width="2" stroke-dasharray="6 4"/>'
        f'<text x="{_ml + 282}" y="20" font-size="13" fill="currentColor">steepness = {_s:.3f}</text>',
        # axes
        f'<line x1="{_ml}" y1="{_py(0)}" x2="{_W - _mr}" y2="{_py(0)}" stroke="currentColor" stroke-opacity="0.5"/>'
        f'<line x1="{_px(0)}" y1="{_mt}" x2="{_px(0)}" y2="{_py(0)}" stroke="currentColor" stroke-opacity="0.25"/>'
        f'<line x1="{_ml}" y1="{_mt}" x2="{_ml}" y2="{_py(0)}" stroke="currentColor" stroke-opacity="0.5"/>',
    ]
    for _t in range(-6, 7, 2):
        _parts.append(
            f'<text x="{_px(_t):.1f}" y="{_py(0) + 16:.1f}" font-size="11" text-anchor="middle" '
            f'fill="currentColor" fill-opacity="0.7">{_t}</text>'
        )
    for _v in (0, 0.5, 1):
        _parts.append(
            f'<text x="{_ml - 6}" y="{_py(_v) + 4:.1f}" font-size="11" text-anchor="end" '
            f'fill="currentColor" fill-opacity="0.7">{_v:g}</text>'
        )
    _parts += [
        f'<text x="{(_W + _ml) / 2}" y="{_H - 8}" font-size="13" text-anchor="middle" '
        f'fill="currentColor">{_sub("x", "G")} (weighted sum)</text>',
        f'<text x="14" y="{(_mt + _py(0)) / 2}" font-size="13" text-anchor="middle" '
        f'fill="currentColor" transform="rotate(-90 14 {(_mt + _py(0)) / 2})">{_sub("y", "G")} = σ({_sub("x", "G")})</text>',
        f'<polyline points="{_pts}" fill="none" stroke="{_BLUE}" stroke-width="2.5"/>',
        f'<line x1="{_px(_ta):.1f}" y1="{_py(_y0 + _s * (_ta - _x0)):.1f}" '
        f'x2="{_px(_tb):.1f}" y2="{_py(_y0 + _s * (_tb - _x0)):.1f}" '
        f'stroke="{_ORANGE}" stroke-width="2" stroke-dasharray="6 4"/>',
        f'<circle cx="{_px(_x0):.1f}" cy="{_py(_y0):.1f}" r="6" fill="{_ORANGE}"/>',
        "</svg>",
    ]
    mo.Html("".join(_parts))
    return


@app.cell(hide_code=True)
def _(mo, output_grad, target):
    _y_G, _r3 = output_grad["y_G"], output_grad["rate3"]
    _below = _y_G < target
    mo.md(rf"""
    ### Step 3: prediction → loss

    The loss is $L = \frac{{1}}{{2}}(t - y_G)^2$. Its slope with respect to the prediction is

    $$
    \frac{{\partial L}}{{\partial y_G}} = -(t - y_G)
    $$

    (The $2$ from the square cancels the $\frac{{1}}{{2}}$. That's exactly why we added it.)

    In words: the rate is the gap between the target and the prediction, with a minus sign. Our prediction ${_y_G:.3f}$ is **{"below" if _below else "above"}** the target ${target:g}$, so pushing the prediction up makes the loss go **{"down" if _below else "up"}**. Hence the {"negative" if _r3 < 0 else "positive"} rate.

    **Rate 3 = $-(t - y_G)$ = $-({target:g} - {_y_G:.3f})$ = {_r3:.3f}**
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Putting the three steps together

    Now turn the first gear. Nudge $w_{DG}$ by a small amount, and watch the change travel to the loss. Each arrow multiplies by its rate:
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    nudge = mo.ui.slider(
        -0.5, 0.5, step=0.01, value=0.1,
        label=r"Nudge $w_{DG}$ by", show_value=True,
    )
    nudge
    return (nudge,)


@app.cell(hide_code=True)
def _(
    activations,
    forward,
    inputs,
    mo,
    network_svg,
    nudge,
    output_grad,
    target,
    weights,
):
    _d = nudge.value
    _r1, _r2, _r3 = activations["D"], output_grad["rate2"], output_grad["rate3"]
    _dx = _r1 * _d
    _dy = _r2 * _dx
    _dL = _r3 * _dy

    # The real change, recomputing the whole network with the nudged weight.
    _w_nudged = {**weights, "DG": weights["DG"] + _d}
    _y_nudged = forward(_w_nudged, inputs)
    _L_before = 0.5 * (target - activations["G"]) ** 2
    _y_after = _y_nudged["G"]
    _dL_real = 0.5 * (target - _y_after) ** 2 - _L_before

    # The whole network with the nudged weight highlighted; activations update live.
    _nodes = {
        "A": (60, 70, f"{_y_nudged['A']:.1f}"),
        "B": (60, 190, f"{_y_nudged['B']:.1f}"),
        "C (bias)": (150, 290, "1"),
        "D": (290, 70, f"{_y_nudged['D']:.3f}"),
        "E": (290, 190, f"{_y_nudged['E']:.3f}"),
        "F (bias)": (390, 290, "1"),
        "G": (460, 130, f"{_y_nudged['G']:.3f}"),
    }
    _edges = [
        ("A", "D", _w_nudged["AD"], 0.5, 1),
        ("A", "E", _w_nudged["AE"], 0.2, -1),
        ("B", "D", _w_nudged["BD"], 0.2, 1),
        ("B", "E", _w_nudged["BE"], 0.5, -1),
        ("C (bias)", "D", _w_nudged["CD"], 0.35, 1),
        ("C (bias)", "E", _w_nudged["CE"], 0.5, -1),
        ("D", "G", _w_nudged["DG"], 0.5, 1),
        ("E", "G", _w_nudged["EG"], 0.5, 1),
        ("F (bias)", "G", _w_nudged["FG"], 0.5, -1),
    ]
    _network = network_svg(_nodes, _edges, target=target, highlight={"DG"})

    _box = {
        "border": "1.5px solid color-mix(in srgb, currentColor 30%, transparent)",
        "border-radius": "10px",
        "padding": "8px 14px",
        "min-width": "96px",
    }
    _loss_color = "#16a34a" if _dL < 0 else ("#dc2626" if _dL > 0 else "inherit")

    def _node(name, change, color="inherit", border=None):
        return mo.vstack(
            [mo.md(name), mo.md(f"**{change:+.4f}**").style({"color": color})],
            align="center",
            gap=0,
        ).style({**_box, **({"border-color": border} if border else {})})

    def _arrow(rate):
        return mo.vstack(
            [
                mo.md(f"× {rate:.3f}"),
                mo.Html(
                    '<svg width="70" height="12" viewBox="0 0 70 12" style="display:block;color:inherit">'
                    '<line x1="0" y1="6" x2="64" y2="6" stroke="currentColor" stroke-width="1.5"/>'
                    '<path d="M62,1 L70,6 L62,11" fill="none" stroke="currentColor" stroke-width="1.5"/>'
                    "</svg>"
                ),
                mo.md("&nbsp;"),
            ],
            align="center",
            gap=0,
        )

    _ripple = mo.hstack(
        [
            _node("$w_{DG}$", _d),
            _arrow(_r1),
            _node("$x_G$", _dx),
            _arrow(_r2),
            _node("$y_G$", _dy),
            _arrow(_r3),
            _node("$L$", _dL, color=_loss_color, border="#3b82f6"),
        ],
        justify="center",
        align="center",
        gap=0.5,
        wrap=True,
    )

    _check = mo.md(
        f"Recomputing the whole network with $w_{{DG}} = {weights['DG'] + _d:.2f}$ changes the loss by "
        f"**{_dL_real:+.4f}**. That's very close to the chain's estimate of {_dL:+.4f}. "
        "(The match is only approximate because the curves bend; the smaller the nudge, the closer it gets.)"
    )
    mo.vstack([_network, _ripple, _check], gap=1)
    return


@app.cell(hide_code=True)
def _(activations, mo, output_grad):
    _r1, _r2, _r3 = activations["D"], output_grad["rate2"], output_grad["rate3"]
    _slope = _r1 * _r2 * _r3
    mo.md(rf"""
    So **the loss moves by rate 1 × rate 2 × rate 3 per unit of nudge**. That product is exactly the slope we were after:

    $$
    \frac{{\partial L}}{{\partial w_{{DG}}}}
    = \underbrace{{y_D}}_{{\text{{rate 1}}}}
    \cdot \underbrace{{y_G(1-y_G)}}_{{\text{{rate 2}}}}
    \cdot \underbrace{{-(t-y_G)}}_{{\text{{rate 3}}}}
    = {_r1:.3f} \times {_r2:.3f} \times ({_r3:.3f})
    = {_slope:.4f}
    $$

    It's the same slope we measured on the loss curve for $w_{{DG}}$ earlier, but this time from three multiplications instead of re-running the network.

    Multiplying rates along a path like this is called the **chain rule**. It's the core idea of **backpropagation**.
    """)
    return


@app.cell(hide_code=True)
def _(activations, mo, network_svg, output_grad, target, weights):
    _r2, _r3, _delta = output_grad["rate2"], output_grad["rate3"], output_grad["delta_G"]
    _rows = []
    for _k in "DEF":
        _r1 = activations[_k]
        _input = "$1$ (bias)" if _k == "F" else f"$y_{_k} = {_r1:.3f}$"
        _rows.append(
            f"| $w_{{{_k}G}}$ | {_input} | ${_r2:.3f}$ | ${_r3:.3f}$ "
            f"| ${_r1 * _r2 * _r3:.4f}$ |"
        )
    _table = "\n".join(_rows)

    # The forward-pass diagram again, with w_EG and w_FG drawn at full strength.
    _nodes = {
        "A": (60, 70, f"{activations['A']:.1f}"),
        "B": (60, 190, f"{activations['B']:.1f}"),
        "C (bias)": (150, 290, "1"),
        "D": (290, 70, f"{activations['D']:.3f}"),
        "E": (290, 190, f"{activations['E']:.3f}"),
        "F (bias)": (390, 290, "1"),
        "G": (460, 130, f"{activations['G']:.3f}"),
    }
    _edges = [
        ("A", "D", weights["AD"], 0.5, 1),
        ("A", "E", weights["AE"], 0.2, -1),
        ("B", "D", weights["BD"], 0.2, 1),
        ("B", "E", weights["BE"], 0.5, -1),
        ("C (bias)", "D", weights["CD"], 0.35, 1),
        ("C (bias)", "E", weights["CE"], 0.5, -1),
        ("D", "G", weights["DG"], 0.5, 1),
        ("E", "G", weights["EG"], 0.5, 1),
        ("F (bias)", "G", weights["FG"], 0.5, -1),
    ]

    mo.vstack([
        mo.md(r"""
    ### The other two weights

    $w_{EG}$ and $w_{FG}$ travel along the same path. Steps 2 and 3 are about node $G$, not about the weight, so **their rates are identical**. Only rate 1 changes: it's the activation of the node the weight comes from.
    """),
        network_svg(_nodes, _edges, target=target, highlight={"EG", "FG"}),
        mo.md(
        rf"""
    | Weight | Rate 1 (input activation) | Rate 2 | Rate 3 | Slope $\frac{{\partial L}}{{\partial w}}$ |
    |---|---|---|---|---|
    """
        + _table
        + rf"""

    Because rates 2 and 3 are shared, it's handy to give their product a name. With the sign flipped, it's called the **error signal** of node $G$, written $\delta_G$ (delta):

    $$
    \delta_G = (t - y_G)\,y_G(1 - y_G)
    $$
    """
        ),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    # Quiz: the sign of δ_G (value updates on "Check").
    delta_g_quiz = mo.ui.radio(
        options=["Positive", "Negative", "Zero"],
        label=(
            r"**Quick check:** our prediction is below the target. "
            r"Will $\delta_G$ be positive, negative or zero?"
        ),
    ).form(submit_button_label="Check", bordered=False)
    delta_g_quiz
    return (delta_g_quiz,)


@app.cell(hide_code=True)
def _(activations, delta_g_quiz, mo, output_grad, target):
    _y, _t, _delta = activations["G"], target, output_grad["delta_G"]
    _err, _slope = _t - _y, _y * (1 - _y)
    _correct = "Positive" if _delta > 0 else ("Negative" if _delta < 0 else "Zero")
    _answer = delta_g_quiz.value

    if _answer is None:
        _feedback = None
    elif _answer == _correct:
        _feedback = mo.callout(
            mo.md(
                f"**Correct!** $t - y_G = {_err:.3f}$ is positive, and $y_G(1 - y_G) = {_slope:.3f}$ "
                "is **always** positive, because a sigmoid's output lies between 0 and 1. "
                "So the sign of $\\delta_G$ comes only from the error: the prediction is too low, "
                "so $\\delta_G > 0$ and node $G$ wants its weighted sum to go **up**."
            ),
            kind="success",
        )
    elif _answer == "Zero":
        _feedback = mo.callout(
            mo.md(
                "Not quite. $\\delta_G$ is zero only when the prediction is exactly right "
                f"($t = y_G$). Here $t - y_G = {_err:.3f}$, so there's still an error to pass back."
            ),
            kind="danger",
        )
    else:
        _feedback = mo.callout(
            mo.md(
                f"Not quite. Check each factor's sign: the prediction is below the target, so "
                f"$t - y_G = {_err:.3f}$ is positive. And $y_G(1 - y_G)$ can never be negative, "
                "because $y_G$ lies between 0 and 1."
            ),
            kind="danger",
        )

    _feedback
    return


@app.cell(hide_code=True)
def _(activations, mo, output_grad, target):
    _y, _delta = activations["G"], output_grad["delta_G"]
    mo.md(rf"""
    For our network:

    $$
    \delta_G = ({target:g} - {_y:.3f}) \times {_y * (1 - _y):.3f} = {_delta:.4f}
    $$

    Then the slope for any of the three weights is simply $-\delta_G \times$ (the activation the weight comes from). You can read $\delta_G$ as _"which way, and how strongly, node $G$ wants its weighted sum to change"_.
    """)
    return


@app.cell(hide_code=True)
def _(learning_rate, mo):
    mo.md(rf"""
    ### Updating the weights

    Remember the update rule: step **against** the slope, scaled by the learning rate $\mu$:

    $$
    w \leftarrow w - \mu \cdot \frac{{\partial L}}{{\partial w}}
    $$

    The slope is $-\delta_G \cdot y_k$, where $y_k$ is the activation of the node the weight comes from. The two minus signs cancel, so

    $$
    \Delta w_k = \mu \cdot \delta_G \cdot y_k
    $$

    In plain words: **each weight changes by (learning rate) × (node $G$'s error signal) × (how active its input node was)**. A connection from a barely active node hardly changes, because it barely contributed to the mistake.

    We'll use a learning rate of $\mu = {learning_rate:g}$.
    """)
    return


@app.cell(hide_code=True)
def _(
    activations,
    forward,
    inputs,
    learning_rate,
    mo,
    network_svg,
    output_grad,
    target,
    weights,
):
    _mu = learning_rate
    _y_G = activations["G"]
    _delta_G = output_grad["delta_G"]

    _new = dict(weights)
    _rows = []
    for _k in "DEF":
        _name = f"{_k}G"
        _dw = _mu * _delta_G * activations[_k]
        _new[_name] = weights[_name] + _dw
        _rows.append(
            f"| $w_{{{_name}}}$ | ${weights[_name]:.4f}$ | "
            f"${_mu:g} \\times {_delta_G:.4f} \\times {activations[_k]:.4f} = {_dw:+.4f}$ | "
            f"${_new[_name]:.4f}$ |"
        )

    _loss_before = 0.5 * (target - _y_G) ** 2
    _y_after = forward(_new, inputs)
    _y_G_after = _y_after["G"]
    _loss_after = 0.5 * (target - _y_G_after) ** 2

    _table = mo.md(
        "| Weight | Old | $\\Delta w = \\mu \\cdot \\delta_G \\cdot y_k$ | New |\n"
        "|---|---|---|---|\n" + "\n".join(_rows)
    )

    _stats = mo.hstack(
        [
            mo.stat(f"{_y_G:.4f} → {_y_G_after:.4f}", label="Prediction y_G", caption=f"target t = {target:g}"),
            mo.stat(
                f"{_loss_after:.4f}",
                label="Loss after one update",
                caption=f"before: {_loss_before:.4f}",
                direction="decrease" if _loss_after < _loss_before else "increase",
                target_direction="decrease",
            ),
        ],
        justify="start",
        gap=2,
    )

    # The network after the update: new last-layer weights (highlighted) and
    # the activations recomputed with them. Hidden-layer weights are unchanged.
    _nodes = {
        "A": (60, 70, f"{_y_after['A']:.1f}"),
        "B": (60, 190, f"{_y_after['B']:.1f}"),
        "C (bias)": (150, 290, "1"),
        "D": (290, 70, f"{_y_after['D']:.3f}"),
        "E": (290, 190, f"{_y_after['E']:.3f}"),
        "F (bias)": (390, 290, "1"),
        "G": (460, 130, f"{_y_G_after:.3f}"),
    }
    _edges = [
        ("A", "D", _new["AD"], 0.5, 1),
        ("A", "E", _new["AE"], 0.2, -1),
        ("B", "D", _new["BD"], 0.2, 1),
        ("B", "E", _new["BE"], 0.5, -1),
        ("C (bias)", "D", _new["CD"], 0.35, 1),
        ("C (bias)", "E", _new["CE"], 0.5, -1),
        ("D", "G", _new["DG"], 0.5, 1),
        ("E", "G", _new["EG"], 0.5, 1),
        ("F (bias)", "G", _new["FG"], 0.5, -1),
    ]
    _network = mo.vstack(
        [
            mo.md("**The network after one update** (updated weights highlighted)"),
            network_svg(_nodes, _edges, target=target, highlight={"DG", "EG", "FG"}),
        ],
        align="center",
    )

    mo.vstack([_table, _network, _stats], gap=1.5)
    return


@app.cell(hide_code=True)
def _(activations, mo, target):
    _below = activations["G"] < target
    _by_input = sorted("DEF", key=lambda k: activations[k])
    _least, _most = _by_input[0], _by_input[-1]
    _name = {"D": "node $D$", "E": "node $E$", "F": "the bias node $F$ (always $1$)"}

    mo.md(
        f"The prediction is {'below' if _below else 'above'} the target, so $\\delta_G$ is "
        f"{'positive' if _below else 'negative'} and every last-layer weight "
        f"{'grows' if _below else 'shrinks'}. This pushes $y_G$ "
        f"{'up' if _below else 'down'} toward $t$. "
        f"The weight from {_name[_most]} changes the most, and the weight from "
        f"{_name[_least]} changes the least, because that node was the least active input."
        "\n\n"
        "The hidden-layer weights (faded in the diagram) haven't changed yet. "
        "Updating them follows the same idea, just with a longer chain."
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Updating Hidden Layers

    For the output node, we knew exactly what it _should_ have produced: the target $t$. For a hidden node like $D$ there is no target. Nobody tells us what $D$ should have output.

    But we don't actually need one. We know how $D$ affects the loss: **through $G$**. So we can do the same thing as before and follow the chain, it's just a bit longer.

    Let's follow the weight $w_{AD}$ (from input $A$ to hidden node $D$):

    1. $w_{AD}$ changes the weighted sum $x_D$. **Rate: $y_A$**, the input it multiplies (same idea as step 1 before).
    2. $x_D$ changes $D$'s output $y_D = \sigma(x_D)$. **Rate: $y_D(1-y_D)$**, the sigmoid's steepness at $D$ (same idea as step 2 before).
    3. $y_D$ changes $G$'s weighted sum $x_G$. **Rate: $w_{DG}$**. This one is new: $D$'s output enters $x_G$ multiplied by $w_{DG}$.
    4. $x_G$ changes the loss $L$. We've already done this part! It's rate 2 × rate 3 from the final layer, which is $-\delta_G$.
    """)
    return


@app.cell(hide_code=True)
def _(activations, output_grad, weights):
    # Error signals for every non-input node. Hidden deltas use the weights from
    # the forward pass (the old ones), not the freshly updated output weights.
    deltas = {"G": output_grad["delta_G"]}
    for _h in "DE":
        _y = activations[_h]
        deltas[_h] = weights[f"{_h}G"] * deltas["G"] * _y * (1 - _y)
    return (deltas,)


@app.cell(hide_code=True)
def _(mo):
    hidden_nudge = mo.ui.slider(
        -0.5, 0.5, step=0.01, value=0.1,
        label=r"Nudge $w_{AD}$ by", show_value=True,
    )
    hidden_nudge
    return (hidden_nudge,)


@app.cell(hide_code=True)
def _(
    activations,
    deltas,
    forward,
    hidden_nudge,
    inputs,
    mo,
    network_svg,
    target,
    weights,
):
    _d = hidden_nudge.value
    _yD = activations["D"]
    _rates = [activations["A"], _yD * (1 - _yD), weights["DG"], -deltas["G"]]
    _changes = [_d]
    for _r in _rates:
        _changes.append(_changes[-1] * _r)

    # The real change, recomputing the whole network with the nudged weight.
    _w_nudged = {**weights, "AD": weights["AD"] + _d}
    _y_nudged = forward(_w_nudged, inputs)
    _L_before = 0.5 * (target - activations["G"]) ** 2
    _y_after = _y_nudged["G"]
    _dL_real = 0.5 * (target - _y_after) ** 2 - _L_before

    # The whole network with the nudge's path (A → D → G) highlighted;
    # activations update live.
    _nodes = {
        "A": (60, 70, f"{_y_nudged['A']:.1f}"),
        "B": (60, 190, f"{_y_nudged['B']:.1f}"),
        "C (bias)": (150, 290, "1"),
        "D": (290, 70, f"{_y_nudged['D']:.3f}"),
        "E": (290, 190, f"{_y_nudged['E']:.3f}"),
        "F (bias)": (390, 290, "1"),
        "G": (460, 130, f"{_y_nudged['G']:.3f}"),
    }
    _edges = [
        ("A", "D", _w_nudged["AD"], 0.5, 1),
        ("A", "E", _w_nudged["AE"], 0.2, -1),
        ("B", "D", _w_nudged["BD"], 0.2, 1),
        ("B", "E", _w_nudged["BE"], 0.5, -1),
        ("C (bias)", "D", _w_nudged["CD"], 0.35, 1),
        ("C (bias)", "E", _w_nudged["CE"], 0.5, -1),
        ("D", "G", _w_nudged["DG"], 0.5, 1),
        ("E", "G", _w_nudged["EG"], 0.5, 1),
        ("F (bias)", "G", _w_nudged["FG"], 0.5, -1),
    ]
    _network = network_svg(_nodes, _edges, target=target, highlight={"AD", "DG"})

    _box = {
        "border": "1.5px solid color-mix(in srgb, currentColor 30%, transparent)",
        "border-radius": "10px",
        "padding": "8px 12px",
        "min-width": "88px",
    }

    def _node(name, change, color="inherit", border=None):
        return mo.vstack(
            [mo.md(name), mo.md(f"**{change:+.4f}**").style({"color": color})],
            align="center",
            gap=0,
        ).style({**_box, **({"border-color": border} if border else {})})

    def _arrow(rate, note):
        return mo.vstack(
            [
                mo.md(f"× {rate:.3f}"),
                mo.Html(
                    '<svg width="56" height="12" viewBox="0 0 56 12" style="display:block;color:inherit">'
                    '<line x1="0" y1="6" x2="50" y2="6" stroke="currentColor" stroke-width="1.5"/>'
                    '<path d="M48,1 L56,6 L48,11" fill="none" stroke="currentColor" stroke-width="1.5"/>'
                    "</svg>"
                ),
                mo.md(note).style({"font-size": "0.8em", "opacity": "0.7"}),
            ],
            align="center",
            gap=0,
        )

    _dL = _changes[-1]
    _loss_color = "#16a34a" if _dL < 0 else ("#dc2626" if _dL > 0 else "inherit")
    _ripple = mo.hstack(
        [
            _node("$w_{AD}$", _changes[0]),
            _arrow(_rates[0], "$y_A$"),
            _node("$x_D$", _changes[1]),
            _arrow(_rates[1], "$y_D(1-y_D)$"),
            _node("$y_D$", _changes[2]),
            _arrow(_rates[2], "$w_{DG}$"),
            _node("$x_G$", _changes[3]),
            _arrow(_rates[3], r"$-\delta_G$"),
            _node("$L$", _dL, color=_loss_color, border="#3b82f6"),
        ],
        justify="center",
        align="center",
        gap=0.25,
        wrap=True,
    )
    _check = mo.md(
        f"Recomputing the whole network with $w_{{AD}} = {weights['AD'] + _d:.2f}$ changes the loss by "
        f"**{_dL_real:+.5f}**, compared with the chain's estimate of {_dL:+.5f}."
    )
    mo.vstack([_network, _ripple, _check], gap=1)
    return


@app.cell(hide_code=True)
def _(activations, deltas, forward, inputs, mo, target, weights):
    _yD = activations["D"]
    _slope = -deltas["D"] * activations["A"]
    _slope_DG = -deltas["G"] * activations["D"]


    # Brute-force check: nudge w_AD both ways and re-run the whole network.
    def _loss(w_AD):
        return 0.5 * (target - forward({**weights, "AD": w_AD}, inputs)["G"]) ** 2


    _h = 1e-5
    _brute = (_loss(weights["AD"] + _h) - _loss(weights["AD"] - _h)) / (2 * _h)
    _check = "✓" if abs(_brute - _slope) < 1e-6 else "✗"
    _ratio = abs(_slope_DG) / abs(_slope)
    mo.md(rf"""
    Multiplying the four rates gives the slope:

    $$
    \frac{{\partial L}}{{\partial w_{{AD}}}}
    = y_A \cdot y_D(1-y_D) \cdot w_{{DG}} \cdot (-\delta_G)
    = {activations["A"]:g} \times {_yD * (1 - _yD):.3f} \times ({weights["DG"]:g}) \times ({-deltas["G"]:.4f})
    = {_slope:.4f}
    $$

    To check it, we measure the slope by brute force again: nudge $w_{{AD}}$ by a tiny amount and re-run the whole network.

    **Chain rule:** ${_slope:.4f}$ · **Brute force:** ${_brute:.4f}$ {_check}

    This slope is about {_ratio:.0f} times smaller than the one for $w_{{DG}}$ (${_slope_DG:.4f}$). Each step back multiplies the signal by a sigmoid slope, which is at most $0.25$, and by a weight. Here the sigmoid slope is ${_yD * (1 - _yD):.3f}$ and $w_{{DG}} = {weights["DG"]:g}$, both well below 1 in size, so the signal shrinks on its way back. With small weights like ours, it tends to fade the further it travels from the output. In deep networks with many layers, this is called the _vanishing gradient_ problem.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Passing the blame backwards

    Look at the last three rates again: $y_D(1-y_D) \cdot w_{DG} \cdot (-\delta_G)$. None of them depend on which weight _into_ $D$ we picked. They only describe node $D$ itself and where it sends its output. So, just as we did for $G$, we flip the sign and bundle them into **node $D$'s error signal**:

    $$
    \delta_D = w_{DG}\,\delta_G \cdot y_D(1 - y_D)
    $$
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    # Quiz: the sign of δ_D (value updates on "Check").
    delta_d_quiz = mo.ui.radio(
        options=[
            "Positive: D should become more active",
            "Negative: D should become less active",
            "Zero: D isn't to blame",
        ],
        label=(
            r"**Quick check:** $\delta_G$ is positive, but $w_{DG}$ is negative. "
            r"Will $\delta_D$ be positive, negative or zero?"
        ),
    ).form(submit_button_label="Check", bordered=False)
    delta_d_quiz
    return (delta_d_quiz,)


@app.cell(hide_code=True)
def _(activations, delta_d_quiz, deltas, mo, weights):
    _yD, _w, _dG, _dD = activations["D"], weights["DG"], deltas["G"], deltas["D"]
    _correct = "Positive" if _dD > 0 else ("Negative" if _dD < 0 else "Zero")
    _answer = delta_d_quiz.value
    _signs = (
        f"$w_{{DG}} = {_w:g}$ is negative, $\\delta_G = {_dG:.4f}$ is positive, and "
        f"$y_D(1 - y_D) = {_yD * (1 - _yD):.3f}$ is always positive. "
        "Negative × positive × positive is **negative**"
    )

    if _answer is None:
        _feedback = None
    elif _answer.startswith(_correct):
        _feedback = mo.callout(
            mo.md(
                f"**Correct!** {_signs}: $\\delta_D = {_dD:.4f}$. "
                "$D$ feeds $G$ through a negative weight, so the more active $D$ is, the lower "
                "$G$ goes. Since $G$ needs to go **up**, $D$ should become **less** active."
            ),
            kind="success",
        )
    elif _answer.startswith("Zero"):
        _feedback = mo.callout(
            mo.md(
                "Not quite. $\\delta_D$ would only be zero if $D$ had no influence on $G$ "
                f"(a weight of 0) or $G$ had no error. Here $w_{{DG}} = {_w:g}$ and "
                f"$\\delta_G = {_dG:.4f}$, so $D$ shares part of the blame."
            ),
            kind="danger",
        )
    else:
        _feedback = mo.callout(
            mo.md(f"Not quite. Multiply the signs: {_signs}."),
            kind="danger",
        )

    _feedback
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    You can read this as **"how much of $G$'s mistake is $D$'s fault"**:

    - **$\delta_G$**: how wrong $G$ was, and in which direction.
    - **$\times\, w_{DG}$**: $D$ is responsible in proportion to how strongly it's connected to $G$. A weak connection means little influence, so little blame. A negative weight flips the direction: if $G$ needs to go up, $D$ should go _down_.
    - **$\times\, y_D(1-y_D)$**: how easily $D$ can change its output right now. If $D$'s sigmoid is flat, pushing on it does little.

    The error signal travels **backwards** through the same weights the activations travelled forwards. That's where the name **backpropagation** comes from.
    """)
    return


@app.cell(hide_code=True)
def _(activations, deltas, mo, weights):
    # Backward pass: error signals flow from G back to D and E.
    _pos = {"D": (230, 95), "E": (230, 295), "G": (480, 195)}
    _r = 42
    _ORANGE = "#f97316"

    def _color(v):
        return "#2563eb" if v >= 0 else "#dc2626"

    def _sub(base, s):
        return (
            f'<tspan font-style="italic">{base}</tspan>'
            f'<tspan baseline-shift="sub" font-size="0.75em">{s}</tspan>'
        )

    # Fixed pixel size (shrinks on narrow screens via max-width), so the
    # diagram never collapses inside a shrink-to-fit container.
    _parts = [
        '<svg viewBox="0 0 580 360" width="580" height="360" style="max-width:100%;height:auto;'
        'display:block;margin:0 auto;font-family:system-ui,sans-serif;color:inherit">',
        '<defs><marker id="bp-arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerUnits="userSpaceOnUse" markerWidth="14" markerHeight="14" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{_ORANGE}"/></marker></defs>',
        f'<text x="290" y="22" font-size="16" font-weight="600" text-anchor="middle" fill="{_ORANGE}">'
        "◀ error signals flow backwards</text>",
    ]
    _gx, _gy = _pos["G"]
    for _h in "DE":
        _hx, _hy = _pos[_h]
        _dx, _dy = _hx - _gx, _hy - _gy
        _len = (_dx**2 + _dy**2) ** 0.5
        _ux, _uy = _dx / _len, _dy / _len
        _sx, _sy = _gx + _ux * _r, _gy + _uy * _r
        _ex, _ey = _hx - _ux * (_r + 3), _hy - _uy * (_r + 3)
        _parts.append(
            f'<line x1="{_sx:.1f}" y1="{_sy:.1f}" x2="{_ex:.1f}" y2="{_ey:.1f}" '
            f'stroke="{_ORANGE}" stroke-width="3" stroke-dasharray="8 5" marker-end="url(#bp-arrow)"/>'
        )
        # label sits beside the arrow: above it for D, below it for E
        _side = -1 if _h == "D" else 1
        _nx, _ny = -_uy, _ux
        if _ny * _side < 0:
            _nx, _ny = -_nx, -_ny
        _mx = (_sx + _ex) / 2 + _nx * 30
        _my = (_sy + _ey) / 2 + _ny * 30 + 6
        _w = weights[f"{_h}G"]
        _parts.append(
            f'<text x="{_mx:.1f}" y="{_my:.1f}" font-size="16" text-anchor="middle" '
            f'fill="currentColor">× {_sub("w", _h + "G")} = {_w:g}</text>'
        )
        # sigmoid steepness, written to the left of the hidden node
        _yh = activations[_h]
        _parts.append(
            f'<text x="{_hx - _r - 12}" y="{_hy + 6}" font-size="16" text-anchor="end" '
            f'fill="currentColor">× {_sub("y", _h)}(1−{_sub("y", _h)}) = {_yh * (1 - _yh):.3f}</text>'
        )
    for _n, (_x, _y) in _pos.items():
        _d = deltas[_n]
        _parts.append(
            f'<circle cx="{_x}" cy="{_y}" r="{_r}" fill="none" stroke="currentColor" stroke-width="2"/>'
            f'<text x="{_x}" y="{_y - _r - 10}" font-size="17" font-weight="700" text-anchor="middle" '
            f'fill="currentColor">{_n}</text>'
            f'<text x="{_x}" y="{_y - 4}" font-size="15" text-anchor="middle" fill="currentColor" '
            f'fill-opacity="0.75">{_sub("δ", _n)}</text>'
            f'<text x="{_x}" y="{_y + 17}" font-size="16" font-weight="700" text-anchor="middle" '
            f'fill="{_color(_d)}">{_d:+.4f}</text>'
        )
    _parts.append("</svg>")
    mo.Html("".join(_parts))
    return


@app.cell(hide_code=True)
def _(deltas, mo, weights):
    _dir = lambda v: "up" if v > 0 else "down"
    mo.md(rf"""
    In our network, $\delta_G = {deltas["G"]:.4f}$ is positive: $G$ should have been higher. The two hidden nodes receive different messages:

    - $w_{{DG}} = {weights["DG"]:g}$, so $\delta_D = {deltas["D"]:.4f}$. $D$ should push its weighted sum **{_dir(deltas["D"])}**{" (the negative weight flips the direction: lower $D$ means higher $G$)" if weights["DG"] < 0 else ""}.
    - $w_{{EG}} = {weights["EG"]:g}$, so $\delta_E = {deltas["E"]:.4f}$. $E$ should push its weighted sum **{_dir(deltas["E"])}**.

    In our network each hidden node feeds just one node, $G$. In bigger networks a hidden node usually feeds several nodes in the next layer. It then collects blame from all of them, so we **add up** their contributions:

    $$
    \delta_i = \Bigl(\sum_{{j}} w_{{ij}}\,\delta_j\Bigr) \cdot y_i(1 - y_i)
    $$

    where $j$ runs over every node that $i$ sends its output to. Weight each downstream error signal by its connection, add them up, then multiply by the node's own sigmoid steepness.
    """)
    return


@app.cell(hide_code=True)
def _(learning_rate, mo):
    mo.md(rf"""
    ### One rule for every weight

    Now every non-input node has an error signal, and **every weight is updated with the same rule**, whichever layer it's in:

    $$
    \Delta w_{{ij}} = \mu \cdot \delta_j \cdot y_i
    $$

    In words: _(learning rate) × (error signal of the node the weight goes **into**) × (activation of the node it comes **from**)_. It's exactly the rule we used for the final layer, with $\delta_G$ replaced by $\delta_D$ or $\delta_E$.

    One detail: we compute **all** the error signals first, using the weights from the forward pass, and only then update. (That's why $\delta_D$ above uses the old $w_{{DG}}$, not the updated one.)

    With $\mu = {learning_rate:g}$, the hidden-layer updates are:
    """)
    return


@app.cell(hide_code=True)
def _(activations, deltas, learning_rate, mo, weights):
    _rows = []
    for _i in "ABC":
        for _j in "DE":
            _name = f"{_i}{_j}"
            _y_i = activations[_i]
            _dw = learning_rate * deltas[_j] * _y_i
            _src = "1 \\text{ (bias)}" if _i == "C" else f"{_y_i:g}"
            _delta = f"({deltas[_j]:.4f})" if deltas[_j] < 0 else f"{deltas[_j]:.4f}"
            _dw_txt = "0" if _dw == 0 else f"{_dw:+.4f}"
            _rows.append(
                f"| $w_{{{_name}}}$ | ${weights[_name]:.4f}$ | "
                f"${learning_rate:g} \\times {_delta} \\times {_src} = {_dw_txt}$ | "
                f"${weights[_name] + _dw:.4f}$ |"
            )
    mo.md(
        "| Weight | Old | $\\Delta w_{ij} = \\mu \\cdot \\delta_j \\cdot y_i$ | New |\n"
        "|---|---|---|---|\n" + "\n".join(_rows)
        + "\n\nThe weights from input $B$ don't change at all: $B = 0$, so they had no influence on "
        "this prediction. That's the same flat curve we saw for $w_{BD}$ and $w_{BE}$ earlier."
    )
    return


@app.cell(hide_code=True)
def _(
    activations,
    deltas,
    forward,
    inputs,
    learning_rate,
    mo,
    network_svg,
    target,
    weights,
):
    # One complete training step: every weight updated with Δw_ij = μ δ_j y_i.
    full_update = {
        _name: weights[_name] + learning_rate * deltas[_name[1]] * activations[_name[0]]
        for _name in weights
    }
    _y = forward(full_update, inputs)
    _loss_before = 0.5 * (target - activations["G"]) ** 2
    _loss_after = 0.5 * (target - _y["G"]) ** 2

    _nodes = {
        "A": (60, 70, f"{_y['A']:.1f}"),
        "B": (60, 190, f"{_y['B']:.1f}"),
        "C (bias)": (150, 290, "1"),
        "D": (290, 70, f"{_y['D']:.3f}"),
        "E": (290, 190, f"{_y['E']:.3f}"),
        "F (bias)": (390, 290, "1"),
        "G": (460, 130, f"{_y['G']:.3f}"),
    }
    _edges = [
        ("A", "D", full_update["AD"], 0.5, 1),
        ("A", "E", full_update["AE"], 0.2, -1),
        ("B", "D", full_update["BD"], 0.2, 1),
        ("B", "E", full_update["BE"], 0.5, -1),
        ("C (bias)", "D", full_update["CD"], 0.35, 1),
        ("C (bias)", "E", full_update["CE"], 0.5, -1),
        ("D", "G", full_update["DG"], 0.5, 1),
        ("E", "G", full_update["EG"], 0.5, 1),
        ("F (bias)", "G", full_update["FG"], 0.5, -1),
    ]
    _stats = mo.hstack(
        [
            mo.stat(
                f"{activations['G']:.4f} → {_y['G']:.4f}",
                label="Prediction y_G",
                caption=f"target t = {target:g}",
            ),
            mo.stat(
                f"{_loss_after:.4f}",
                label="Loss after one training step",
                caption=f"before: {_loss_before:.4f}",
                direction="decrease" if _loss_after < _loss_before else "increase",
                target_direction="decrease",
            ),
        ],
        justify="start",
        gap=2,
    )
    mo.vstack(
        [
            mo.md(
                "## The Result\n\n"
                "We've now updated all nine weights: the three going into $G$ and the six going "
                "into the hidden layer. That completes one full training step. Let's run the "
                "forward pass again with the new weights and see whether the prediction has "
                f"moved towards the target $t = {target:g}$."
            ),
            network_svg(_nodes, _edges, target=target),
            _stats,
        ],
        gap=1.5,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Recap: One Training Step

    That's the whole backpropagation algorithm. For each training example:

    1. **Forward pass**: compute every node's activation, from the inputs to the output.
    2. **Output error signal**: $\delta_G = (t - y_G)\,y_G(1 - y_G)$.
    3. **Backward pass**: pass the error signals back, layer by layer: $\delta_i = \bigl(\sum_j w_{ij}\,\delta_j\bigr)\, y_i(1-y_i)$.
    4. **Update every weight**: $\Delta w_{ij} = \mu\,\delta_j\,y_i$.

    One step only nudges the prediction a little toward the target. Training repeats these four steps many times, until the loss is small.

    /// tip | Try it yourself
    In [Neural Network Training (Exercise)](../neural-network-training-exercise/) you do a full training step by hand on a network you choose, with instant feedback on every answer.
    ///
    """)
    return


if __name__ == "__main__":
    app.run()
