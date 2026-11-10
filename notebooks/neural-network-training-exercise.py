import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="Neural Network Training (Exercise)")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    import anywidget
    import traitlets
    from wigglystuff import FloatingPanel

    return FloatingPanel, anywidget, mo, np, traitlets


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Neural Network Training (Exercise ✍️)

    /// tip | New to backpropagation?
    This exercise goes with [Neural Network Training Made Simple](../neural-network-training/), which explains every formula you'll use here, step by step. If you haven't read it yet, start there.
    ///

    In this exercise you train a small neural network **by hand**, for one full training step. You'll:

    1. run the **forward pass** and compute every node's activation,
    2. measure the **loss**,
    3. run the **backward pass** and compute every node's error signal,
    4. **update** every weight,
    5. check that the new prediction is closer to the target.

    Every node uses the **sigmoid** activation, the loss is $L = \frac{1}{2}(t - y)^2$, and bias nodes always output $1$.

    Each step unlocks once the previous one is correct. Round your answers to **4 decimal places**. If you get stuck, click **Show answer**.
    """)
    return


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
def _(mo):
    mo.md(r"""
    ## 1. Choose your network

    Pick how many inputs, hidden layers and nodes per hidden layer your network has. It always ends in a **single output node**, and every layer except the output gets a **bias node** that always outputs $1$. The inputs, target and weights are drawn at random from the **seed**: use the same seed to get the same exercise again, or click **New exercise** for a fresh one.

    /// attention | Choose before you start
    Changing any of these settings starts a new exercise and clears your answers, so pick your network before you begin section 3.
    ///
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    n_inputs = mo.ui.slider(1, 4, value=2, label="Inputs", show_value=True)
    n_hidden_layers = mo.ui.radio(
        ["1", "2"], value="1", label="Hidden layers", inline=True
    )
    mo.hstack([n_inputs, n_hidden_layers], justify="start", gap=3)
    return n_hidden_layers, n_inputs


@app.cell(hide_code=True)
def _(mo, n_hidden_layers):
    hidden_sizes = mo.ui.array(
        [
            mo.ui.slider(1, 4, value=2, label=f"Nodes in hidden layer {_i + 1}", show_value=True)
            for _i in range(int(n_hidden_layers.value))
        ]
    )
    mo.hstack(list(hidden_sizes), justify="start", gap=3)
    return (hidden_sizes,)


@app.cell(hide_code=True)
def _(mo):
    # Counts clicks; every click re-runs the cell below, which draws a new seed.
    new_exercise = mo.ui.button(value=0, on_click=lambda n: n + 1, label="🎲 New exercise")
    return (new_exercise,)


@app.cell(hide_code=True)
def _(mo, new_exercise, np):
    _start = 7 if new_exercise.value == 0 else int(np.random.default_rng().integers(0, 10000))
    seed_input = mo.ui.number(start=0, stop=9999, step=1, value=_start, label="Seed")
    mo.hstack([seed_input, new_exercise], justify="start", align="end", gap=1)
    return (seed_input,)


@app.cell(hide_code=True)
def _(mo, np):
    MU = 0.5  # learning rate
    LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


    def sigmoid(v):
        return 1 / (1 + np.exp(-v))


    def build_network(n_inputs, hidden_sizes):
        """Layers from input to output: [{"nodes": [...], "bias": letter or None}].
        Letters run through the network in order, each layer's bias node last."""
        sizes = [n_inputs, *hidden_sizes, 1]
        layers, i = [], 0
        for li, n in enumerate(sizes):
            nodes = list(LETTERS[i : i + n])
            i += n
            bias = None
            if li < len(sizes) - 1:
                bias = LETTERS[i]
                i += 1
            layers.append({"nodes": nodes, "bias": bias})
        return layers


    def sources(layer):
        """Nodes that send their output to the next layer (bias included)."""
        return layer["nodes"] + ([layer["bias"]] if layer["bias"] else [])


    def weight_keys(net, li):
        """Keys of the weights from layer li into layer li + 1, e.g. "AD"."""
        return [i + j for i in sources(net[li]) for j in net[li + 1]["nodes"]]


    def init_exercise(net, seed):
        rng = np.random.default_rng(seed)
        inputs = {n: round(float(rng.uniform(0, 1)), 1) for n in net[0]["nodes"]}
        weights = {
            k: round(float(rng.uniform(-0.5, 0.5)), 2)
            for li in range(len(net) - 1)
            for k in weight_keys(net, li)
        }
        target = float(rng.integers(0, 2))
        return inputs, weights, target


    def forward(net, w, inputs):
        """Weighted sums x and activations y of every node."""
        y = dict(inputs)
        x = {}
        for layer in net:
            if layer["bias"]:
                y[layer["bias"]] = 1.0
        for li in range(1, len(net)):
            for j in net[li]["nodes"]:
                x[j] = sum(y[i] * w[i + j] for i in sources(net[li - 1]))
                y[j] = float(sigmoid(x[j]))
        return x, y


    def backward(net, w, y, t):
        """Error signals: output first, then each hidden layer from back to front."""
        out = net[-1]["nodes"][0]
        d = {out: (t - y[out]) * y[out] * (1 - y[out])}
        for li in range(len(net) - 2, 0, -1):
            for i in net[li]["nodes"]:
                d[i] = sum(w[i + j] * d[j] for j in net[li + 1]["nodes"]) * y[i] * (1 - y[i])
        return d


    def updates(net, w, y, d, mu=MU):
        """Δw_ij = μ · δ_j · y_i for every weight."""
        return {k: mu * d[k[1]] * y[k[0]] for k in w}


    def loss(t, y_out):
        return 0.5 * (t - y_out) ** 2


    def check(raw, true):
        """Compare a typed answer with the true value. Returns ok / wrong / empty / invalid."""
        s = (raw or "").strip().replace(",", ".").replace("−", "-")
        if not s:
            return "empty"
        try:
            v = float(s)
        except ValueError:
            return "invalid"
        # Allow for rounding intermediate values to 4 decimal places.
        return "ok" if abs(v - true) <= max(2e-4, 0.01 * abs(true)) else "wrong"


    def layer_name(net, li, article=False):
        """"output layer", "hidden layer 2", ... With article=True, "the" is added
        where English needs it ("the output layer" but "hidden layer 2")."""
        if li == 0:
            name = "input layer"
        elif li == len(net) - 1:
            name = "output layer"
        else:
            name = "hidden layer" if len(net) == 3 else f"hidden layer {li}"
        return ("the " + name) if article and not name[-1].isdigit() else name


    def node_list(names, bias=None):
        parts = [f"${n}$" for n in names] + ([f"${bias}$ (bias)"] if bias else [])
        return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


    def weight_tables(net, w, digits=2, updated=None):
        """One markdown table per weight layer: rows = from, columns = to.
        Weights in `updated` are shown in bold."""
        updated = updated or set()
        out = []
        for li in range(len(net) - 1):
            to = net[li + 1]["nodes"]
            rows = [
                f"| **{i}**{' (bias)' if i == net[li]['bias'] else ''} | "
                + " | ".join(
                    (f"**{w[i + j]:+.{digits}f}**" if i + j in updated else f"{w[i + j]:+.{digits}f}")
                    for j in to
                )
                + " |"
                for i in sources(net[li])
            ]
            out.append(
                f"**Weights into {layer_name(net, li + 1, article=True)}**\n\n"
                "| from ↓ / to → | " + " | ".join(f"**{j}**" for j in to) + " |\n"
                "|---|" + "---|" * len(to) + "\n" + "\n".join(rows)
            )
        return "\n\n".join(out)


    LABEL_MAX = 9  # label edges only between layers with at most this many weights


    def labels_fit(net, li):
        return len(weight_keys(net, li)) <= LABEL_MAX


    def network_svg(
        net, w, y=None, x=None, delta=None, updated=None, target=None, loss=None, r=22
    ):
        """Draw the network with everything that is known so far.

        One column per layer, bias node at the bottom of each column.
        - edges: coloured by sign, labelled with their weight (only between
          sparse layers, see LABEL_MAX); weights in `updated` are drawn bold
        - node: activation y inside ("?" until known), weighted sum x and error
          signal δ underneath once known
        - output: target t and loss L next to it
        """
        y, x, delta, updated = y or {}, x or {}, delta or {}, updated or set()
        col_gap, row_gap, top, left = 160, 92, 50, 50
        max_rows = max(len(sources(layer)) for layer in net)
        H = top + (max_rows - 1) * row_gap + r + 42
        W = left + (len(net) - 1) * col_gap + r + (100 if target is not None else 30)
        pos = {}
        for li, layer in enumerate(net):
            col = sources(layer)
            offset = (max_rows - len(col)) * row_gap / 2
            for k, n in enumerate(col):
                pos[n] = (left + li * col_gap, top + offset + k * row_gap)

        halo = 'style="paint-order:stroke;stroke:Canvas;stroke-width:3px;stroke-linejoin:round"'
        parts = [
            f'<svg viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}" '
            'style="max-width:100%;height:auto;display:block;margin:0 auto;'
            'font-family:system-ui,sans-serif;color:inherit">',
            '<defs><marker id="wt-arrow" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerUnits="userSpaceOnUse" markerWidth="9" markerHeight="9" orient="auto-start-reverse">'
            '<path d="M0,0 L10,5 L0,10 z" fill="context-stroke"/></marker></defs>',
        ]
        labels = []  # drawn after all lines so no line crosses a label
        for li in range(len(net) - 1):
            for k in weight_keys(net, li):
                (x1, y1), (x2, y2) = pos[k[0]], pos[k[1]]
                dx, dy = x2 - x1, y2 - y1
                dist = (dx**2 + dy**2) ** 0.5
                ux, uy = dx / dist, dy / dist
                sx, sy = x1 + ux * r, y1 + uy * r
                ex_, ey_ = x2 - ux * (r + 2), y2 - uy * (r + 2)
                color = "#2563eb" if w[k] >= 0 else "#dc2626"
                sw = 0.75 + 2.5 * min(abs(w[k]), 1.5)
                parts.append(
                    f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex_:.1f}" y2="{ey_:.1f}" '
                    f'stroke="{color}" stroke-width="{sw:.2f}" stroke-opacity="0.75" '
                    'marker-end="url(#wt-arrow)"/>'
                )
                if not labels_fit(net, li):
                    continue
                # label near the start of the edge, where edges are still apart
                lx, ly = sx + (ex_ - sx) * 0.3, sy + (ey_ - sy) * 0.3
                weight = "700" if k in updated else "400"
                labels.append(
                    f'<text x="{lx:.1f}" y="{ly + 4:.1f}" font-size="11" font-weight="{weight}" '
                    f'text-anchor="middle" fill="{color}" {halo}>{w[k]:+.2f}</text>'
                )
        parts += labels
        for layer in net:
            for n in sources(layer):
                cx, cy = pos[n]
                is_bias = n == layer["bias"]
                if is_bias:
                    text = "1"
                elif n not in y:
                    text = "?"
                elif n in net[0]["nodes"]:
                    text = f"{y[n]:g}"
                else:
                    text = f"{y[n]:.3f}"
                dash = ' stroke-dasharray="4 3"' if is_bias else ""
                parts.append(
                    f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="currentColor" '
                    f'stroke-width="1.5"{dash}/>'
                    f'<text x="{cx}" y="{cy + 4}" font-size="12" text-anchor="middle" '
                    f'fill="currentColor">{text}</text>'
                    # bias labels go below the node, away from the edges
                    f'<text x="{cx}" y="{cy + r + 17 if is_bias else cy - r - 7}" font-size="13" '
                    f'font-weight="600" text-anchor="middle" fill="currentColor">'
                    f'{n}{" (bias)" if is_bias else ""}</text>'
                )
                below = []
                if n in x:
                    below.append(f"x = {x[n]:.3f}")
                if n in delta:
                    below.append(f"δ = {delta[n]:+.4f}")
                for i, line in enumerate(below):
                    parts.append(
                        f'<text x="{cx}" y="{cy + r + 13 + 12 * i}" font-size="10.5" '
                        f'text-anchor="middle" fill="currentColor" fill-opacity="0.8" {halo}>{line}</text>'
                    )
        if target is not None:
            out = net[-1]["nodes"][0]
            cx, cy = pos[out]
            parts.append(
                f'<text x="{cx + r + 10}" y="{cy + 4}" font-size="13" '
                f'fill="currentColor">t = {target:g}</text>'
            )
            if loss is not None:
                parts.append(
                    f'<text x="{cx + r + 10}" y="{cy + 22}" font-size="12" '
                    f'fill="currentColor">L = {loss:.4f}</text>'
                )
        parts.append("</svg>")
        return mo.Html("".join(parts))


    def panel_html(net, w, updated=None, **kw):
        """Floating-panel content: the diagram, plus weight tables whenever some
        connections are too crowded to be labelled."""
        html = network_svg(net, w, updated=updated, **kw).text
        if not all(labels_fit(net, li) for li in range(len(net) - 1)):
            html += mo.md(weight_tables(net, w, updated=updated)).text
        return html


    def svg_width(net, target=True):
        return 50 + (len(net) - 1) * 160 + 22 + (100 if target else 30)

    return (
        MU,
        backward,
        build_network,
        check,
        forward,
        init_exercise,
        layer_name,
        loss,
        network_svg,
        node_list,
        panel_html,
        sources,
        svg_width,
        updates,
        weight_keys,
    )


@app.cell(hide_code=True)
def _(
    MU,
    backward,
    build_network,
    forward,
    hidden_sizes,
    init_exercise,
    loss,
    n_inputs,
    seed_input,
    updates,
):
    # Build the exercise and work out every answer.
    net = build_network(n_inputs.value, list(hidden_sizes.value))
    _inputs, _weights, _target = init_exercise(net, int(seed_input.value))
    _x, _y = forward(net, _weights, _inputs)
    _d = backward(net, _weights, _y, _target)
    _dw = updates(net, _weights, _y, _d, MU)
    _new_w = {k: _weights[k] + _dw[k] for k in _weights}
    _x_new, _y_new = forward(net, _new_w, _inputs)
    _out = net[-1]["nodes"][0]
    ex = {
        "inputs": _inputs,
        "weights": _weights,
        "target": _target,
        "out": _out,
        "x": _x,
        "y": _y,
        "delta": _d,
        "dw": _dw,
        "new_weights": _new_w,
        "y_new": _y_new,
        "loss": loss(_target, _y[_out]),
        "loss_new": loss(_target, _y_new[_out]),
    }
    return ex, net


@app.cell(hide_code=True)
def _(MU, ex, mo, net, network_svg):
    _inputs = ", ".join(f"$y_{n} = {v:g}$" for n, v in ex["inputs"].items())
    mo.vstack(
        [
            mo.md("## 2. Your network"),
            network_svg(net, ex["weights"], y=ex["inputs"], target=ex["target"]),
            mo.md(
                f"**Inputs:** {_inputs}  \n"
                f"**Target:** $t = {ex['target']:g}$  \n"
                f"**Learning rate:** $\\mu = {MU:g}$  \n"
            ),
            mo.md(
                "While you work, you can view **Your network** in the panel in the top left corner (it fills in "
                "every value as you complete each step, and updated weights appear in **bold**). "
                "The **Sigmoid calculator** is top right."
            ),
        ],
        gap=1,
    )
    return


@app.cell(hide_code=True)
def _(FloatingPanel, anywidget, ex, mo, net, panel_html, svg_width, traitlets):
    # The panel holds a tiny widget whose SVG is swapped from Python as the
    # learner completes steps (see the exercise cell). Updating the widget,
    # rather than rebuilding the panel, keeps the panel where it was dragged.
    class _NetworkView(anywidget.AnyWidget):
        html = traitlets.Unicode("").tag(sync=True)
        _esm = """
        function render({ model, el }) {
          const draw = () => { el.innerHTML = model.get("html"); };
          model.on("change:html", draw);
          draw();
        }
        export default { render };
        """
        _css = """
        table { border-collapse: collapse; font: 12px system-ui, sans-serif; margin: 4px 0 10px; }
        th, td { padding: 2px 8px; border-bottom: 1px solid rgba(128, 128, 128, 0.3); text-align: right; }
        p { font: 12px system-ui, sans-serif; margin: 6px 0 2px; }
        """


    panel_view = _NetworkView(
        html=panel_html(net, ex["weights"], y=ex["inputs"], target=ex["target"])
    )
    FloatingPanel(
        mo.ui.anywidget(panel_view),
        corner="top-left",
        width=min(660, svg_width(net) + 24),
        collapsed=True,
        title="Your network",
    )
    return (panel_view,)


@app.cell(hide_code=True)
def _(MU, ex, layer_name, net, node_list, sources, weight_keys):
    # One stage per step of the training step. Each stage lists the values the
    # learner must compute ("fields") and a markdown answer template whose
    # {key} placeholders become text inputs. Templates must not contain other braces.

    def _w(i, j):
        return "w_{" + i + j + "}"

    def _field(key, tex, true):
        return {"key": key, "tex": tex, "true": true}

    _out = ex["out"]
    stages = []

    # 1. Forward pass, layer by layer
    for _li in range(1, len(net)):
        _prev, _layer = net[_li - 1], net[_li]
        _j = _layer["nodes"][0]
        _example = " + ".join(
            ("1 \\cdot " + _w(i, _j)) if i == _prev["bias"] else ("y_" + i + "\\," + _w(i, _j))
            for i in sources(_prev)
        )
        stages.append(
            {
                "kind": "forward",
                "items": _layer["nodes"],
                "title": f"Forward pass: {layer_name(net, _li)}",
                "explanation": (
                    f"For each node $j$ in {layer_name(net, _li, article=True)}, add up the activations "
                    f"of the nodes feeding into it ({node_list(_prev['nodes'], _prev['bias'])}), "
                    "each multiplied by its weight. Then pass the sum through the sigmoid:\n\n"
                    "$$\nx_j = \\sum_i y_i\\, w_{ij}, \\qquad y_j = \\sigma(x_j) = \\frac{1}{1 + e^{-x_j}}\n$$\n\n"
                    f"For example: $x_{_j} = {_example}$."
                ),
                "fields": [
                    f
                    for n in _layer["nodes"]
                    for f in (
                        _field(f"x_{n}", f"x_{n}", ex["x"][n]),
                        _field(f"y_{n}", f"y_{n}", ex["y"][n]),
                    )
                ],
                "template": "| Node | Weighted sum x | Activation y |\n|---|---|---|\n"
                + "\n".join(f"| **{n}** | {{x_{n}}} | {{y_{n}}} |" for n in _layer["nodes"]),
                "reference": "| Node | $x$ | $y$ |\n|---|---|---|\n"
                + "\n".join(
                    f"| ${n}$ | ${ex['x'][n]:.4f}$ | ${ex['y'][n]:.4f}$ |" for n in _layer["nodes"]
                ),
            }
        )

    # 2. Loss
    stages.append(
        {
            "kind": "loss",
            "items": [],
            "title": "Loss",
            "explanation": (
                f"Compare the prediction $y_{_out}$ with the target $t = {ex['target']:g}$ "
                "using the squared error loss:\n\n"
                f"$$\nL = \\tfrac{{1}}{{2}}\\,(t - y_{_out})^2\n$$"
            ),
            "fields": [_field("L", "L", ex["loss"])],
            "template": "| Quantity | Your answer |\n|---|---|\n| Loss L | {L} |",
            "reference": f"$L = {ex['loss']:.4f}$",
        }
    )

    # 3. Output error signal
    stages.append(
        {
            "kind": "delta",
            "items": [_out],
            "title": "Error signal of the output node",
            "explanation": (
                "Start the backward pass at the output. Its error signal combines how wrong "
                "the prediction is with how steep the sigmoid is there:\n\n"
                f"$$\n\\delta_{_out} = (t - y_{_out}) \\cdot y_{_out}(1 - y_{_out})\n$$"
            ),
            "fields": [_field(f"d_{_out}", f"\\delta_{_out}", ex["delta"][_out])],
            "template": f"| Quantity | Your answer |\n|---|---|\n| δ of {_out} | {{d_{_out}}} |",
            "reference": f"$\\delta_{_out} = {ex['delta'][_out]:.4f}$",
        }
    )

    # 4. Hidden error signals, from the last hidden layer back to the first
    for _li in range(len(net) - 2, 0, -1):
        _layer, _next = net[_li], net[_li + 1]
        _i = _layer["nodes"][0]
        _sum = " + ".join(_w(_i, j) + "\\,\\delta_" + j for j in _next["nodes"])
        stages.append(
            {
                "kind": "delta",
                "items": _layer["nodes"],
                "title": f"Error signals: {layer_name(net, _li)}",
                "explanation": (
                    "Pass the error signals one layer back. Each node collects the error "
                    "signals of the nodes it feeds, weighted by the connections, then "
                    "multiplies by its own sigmoid steepness:\n\n"
                    "$$\n\\delta_i = \\Bigl(\\sum_j w_{ij}\\,\\delta_j\\Bigr) \\cdot y_i(1 - y_i)\n$$\n\n"
                    f"where $j$ runs over the nodes of {layer_name(net, _li + 1, article=True)} "
                    f"({node_list(_next['nodes'])}). For example: "
                    f"$\\delta_{_i} = ({_sum}) \\cdot y_{_i}(1 - y_{_i})$.\n\n"
                    "Use the **original** weights: all error signals are computed before any weight changes."
                ),
                "fields": [_field(f"d_{n}", f"\\delta_{n}", ex["delta"][n]) for n in _layer["nodes"]],
                "template": "| Node | Error signal δ |\n|---|---|\n"
                + "\n".join(f"| **{n}** | {{d_{n}}} |" for n in _layer["nodes"]),
                "reference": "| Node | $\\delta$ |\n|---|---|\n"
                + "\n".join(f"| ${n}$ | ${ex['delta'][n]:.4f}$ |" for n in _layer["nodes"]),
            }
        )

    # 5. Weight updates, from the output side back to the inputs
    for _li in range(len(net) - 2, -1, -1):
        _from, _to = net[_li], net[_li + 1]
        _keys = weight_keys(net, _li)
        _k = _keys[0]
        stages.append(
            {
                "kind": "update",
                "items": _keys,
                "title": f"Weight updates: into {layer_name(net, _li + 1, article=True)}",
                "explanation": (
                    "Every weight is updated with the same rule: learning rate × error signal "
                    "of the node the weight goes **into** × activation of the node it comes **from**:\n\n"
                    f"$$\n\\Delta w_{{ij}} = \\mu \\cdot \\delta_j \\cdot y_i, \\qquad \\mu = {MU:g}\n$$\n\n"
                    f"For example: $\\Delta {_w(_k[0], _k[1])} = \\mu \\cdot \\delta_{_k[1]} \\cdot y_{_k[0]}$. "
                    "Bias nodes have $y = 1$. Enter the **change** $\\Delta w$, not the new weight."
                ),
                "fields": [
                    _field(f"dw_{k}", "\\Delta " + _w(k[0], k[1]), ex["dw"][k]) for k in _keys
                ],
                "template": "| from ↓ / to → | "
                + " | ".join(f"**{j}**" for j in _to["nodes"])
                + " |\n|---|"
                + "---|" * len(_to["nodes"])
                + "\n"
                + "\n".join(
                    f"| **{i}**{' (bias)' if i == _from['bias'] else ''} | "
                    + " | ".join(f"{{dw_{i}{j}}}" for j in _to["nodes"])
                    + " |"
                    for i in sources(_from)
                ),
                "reference": "| Weight | Old | $\\Delta w$ | New |\n|---|---|---|---|\n"
                + "\n".join(
                    f"| ${_w(k[0], k[1])}$ | ${ex['weights'][k]:+.4f}$ | ${ex['dw'][k]:+.4f}$ "
                    f"| ${ex['new_weights'][k]:+.4f}$ |"
                    for k in _keys
                ),
            }
        )

    # 6. New prediction with the updated weights
    stages.append(
        {
            "kind": "final",
            "items": [],
            "title": "Check: the new prediction",
            "explanation": (
                "Did it work? Run the forward pass again with the **updated** weights "
                "(the \"New\" column in the tables above) and compute the new prediction "
                "and the new loss."
            ),
            "fields": [
                _field("y_new", f"y_{_out}", ex["y_new"][_out]),
                _field("L_new", "L", ex["loss_new"]),
            ],
            "template": (
                "| Quantity | Your answer |\n|---|---|\n"
                f"| New prediction y of {_out} | {{y_new}} |\n| New loss L | {{L_new}} |"
            ),
            "reference": f"$y_{_out} = {ex['y_new'][_out]:.4f}$, $L = {ex['loss_new']:.4f}$",
        }
    )
    return (stages,)


@app.cell(hide_code=True)
def _(mo, stages):
    # Answer boxes and "Show answer" buttons, one per stage. Recreated (and so
    # reset) whenever the network or the seed changes.
    def _form(stage):
        boxes = {f["key"]: mo.ui.text(placeholder="?") for f in stage["fields"]}
        return mo.md(stage["template"]).batch(**boxes).form(submit_button_label="Check", bordered=False)


    answer_forms = mo.ui.array([_form(s) for s in stages])
    reveal_buttons = mo.ui.array(
        [
            mo.ui.button(value=False, on_click=lambda _: True, label="Show answer")
            for _ in stages
        ]
    )
    return answer_forms, reveal_buttons


@app.cell(hide_code=True)
def _(
    answer_forms,
    check,
    ex,
    mo,
    net,
    network_svg,
    panel_html,
    panel_view,
    reveal_buttons,
    stages,
):
    _blocks = [mo.md("## 3. One training step, by hand")]
    _all_done = True
    # Everything the learner has worked out so far, for the floating panel.
    _known = {"y": dict(ex["inputs"]), "x": {}, "delta": {}, "updated": set(), "loss": None}
    _final = False
    for _n, (_stage, _form, _btn) in enumerate(zip(stages, answer_forms, reveal_buttons), 1):
        _answers = _form.value
        _results = {
            f["key"]: check(_answers.get(f["key"]) if _answers else None, f["true"])
            for f in _stage["fields"]
        }
        _correct = _answers is not None and all(r == "ok" for r in _results.values())
        _revealed = bool(_btn.value)
        _done = _correct or _revealed

        _parts = [mo.md(f"### Step {_n} · {_stage['title']}\n\n{_stage['explanation']}"), _form]
        if _correct:
            _parts.append(mo.callout(mo.md("**All correct!**"), kind="success"))
        elif _answers is not None:
            _wrong = [f for f in _stage["fields"] if _results[f["key"]] != "ok"]
            _n_ok = len(_stage["fields"]) - len(_wrong)
            _parts.append(
                mo.callout(
                    mo.md(
                        f"{_n_ok} of {len(_stage['fields'])} correct. Check "
                        + ", ".join(f"${f['tex']}$" for f in _wrong)
                        + ". (Round to 4 decimal places.)"
                    ),
                    kind="danger",
                )
            )
        if _done:
            if _stage["kind"] == "forward":
                for _node in _stage["items"]:
                    _known["x"][_node] = ex["x"][_node]
                    _known["y"][_node] = ex["y"][_node]
            elif _stage["kind"] == "loss":
                _known["loss"] = ex["loss"]
            elif _stage["kind"] == "delta":
                for _node in _stage["items"]:
                    _known["delta"][_node] = ex["delta"][_node]
            elif _stage["kind"] == "update":
                _known["updated"].update(_stage["items"])
            elif _stage["kind"] == "final":
                _final = True
            _parts.append(
                mo.callout(
                    mo.md(
                        ("**Answer.** " if _revealed and not _correct else "")
                        + "Use these values in the next steps:\n\n"
                        + _stage["reference"]
                    ),
                    kind="info",
                )
            )
        else:
            _parts.append(_btn)
        _blocks.append(mo.vstack(_parts, gap=0.75))

        if not _done:
            _all_done = False
            _blocks.append(mo.md("🔒 _Finish this step (or show the answer) to unlock the next one._"))
            break

    if _all_done:
        _out = ex["out"]
        _blocks += [
            mo.md("## 🎉 One training step done"),
            mo.hstack(
                [
                    mo.stat(
                        f"{ex['y'][_out]:.4f} → {ex['y_new'][_out]:.4f}",
                        label=f"Prediction y_{_out}",
                        caption=f"target t = {ex['target']:g}",
                    ),
                    mo.stat(
                        f"{ex['loss_new']:.4f}",
                        label="Loss after the step",
                        caption=f"before: {ex['loss']:.4f}",
                        direction="decrease" if ex["loss_new"] < ex["loss"] else "increase",
                        target_direction="decrease",
                    ),
                ],
                justify="start",
                gap=2,
            ),
            mo.md("**Your network after the update**"),
            network_svg(
                net,
                ex["new_weights"],
                y=ex["y_new"],
                updated=set(ex["new_weights"]),
                target=ex["target"],
                loss=ex["loss_new"],
            ),
            mo.md(r"""
    You just did everything a neural network does in one training step:

    1. **Forward pass**: compute every activation, from the inputs to the output.
    2. **Loss**: measure how far the prediction is from the target.
    3. **Backward pass**: compute the error signals, from the output back to the first hidden layer.
    4. **Update**: change every weight by $\Delta w_{ij} = \mu\,\delta_j\,y_i$.

    Real training repeats this for many examples, many times over. Want more practice? Change the network size or click **New exercise**.
    """),
        ]

    # Update the floating panel in place (it keeps its position).
    if _final:
        panel_view.html = panel_html(
            net, ex["new_weights"], y=ex["y_new"], updated=set(ex["new_weights"]),
            target=ex["target"], loss=ex["loss_new"],
        )
    else:
        _w_now = {
            k: ex["new_weights"][k] if k in _known["updated"] else v
            for k, v in ex["weights"].items()
        }
        panel_view.html = panel_html(
            net, _w_now, y=_known["y"], x=_known["x"], delta=_known["delta"],
            updated=_known["updated"], target=ex["target"], loss=_known["loss"],
        )

    mo.vstack(_blocks, gap=2)
    return


if __name__ == "__main__":
    app.run()
