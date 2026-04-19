"""
diagrams.py — Manim Diagram + Scene Template Library
=====================================================
Two registries:
  DIAGRAM_REGISTRY  — short animated inserts (existing pipeline)
  SCENE_REGISTRY    — full educational scenes (new Topic Video pipeline)

All templates are DATA-DRIVEN. AI provides content via params dicts.
Templates handle all rendering with proper spacing and clean visuals.
"""

import re
import math
import textwrap
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

_BG    = "#0F172A"
_BG2   = "#0d1525"
_COLORS = [
    "#00D9FF", "#FF6B6B", "#4ECDC4", "#FFE66D",
    "#A78BFA", "#34D399", "#FB923C", "#F472B6",
    "#60A5FA", "#FBBF24", "#E879F9", "#2DD4BF",
]
_WHITE  = "#F1F5F9"
_DIM    = "#94A3B8"
_DIMMER = "#475569"


# ════════════════════════════════════════════════════════════════════
# SHARED HELPERS
# ════════════════════════════════════════════════════════════════════

def _s(text: str, max_len: int = 35) -> str:
    cleaned = re.sub(r"[^\x20-\x7E]", "", str(text))
    cleaned = cleaned.replace('"', "'").replace("\\", "").replace("\n", " ")
    return cleaned[:max_len].strip()

def _c(params: dict, n: int, key: str = "colors") -> List[str]:
    provided = params.get(key, [])
    return [
        (provided[i] if i < len(provided) and provided[i] else _COLORS[i % len(_COLORS)])
        for i in range(n)
    ]

def _w(duration: int, anim_secs: float) -> int:
    return max(1, duration - int(anim_secs) - 1)

def _wrap_text(text: str, max_chars_per_line: int = 55) -> List[str]:
    """Wrap text into lines of max_chars_per_line characters."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars_per_line:
            current = (current + " " + word).strip()
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines if lines else [text[:max_chars_per_line]]

def _manim_text_group(var_prefix: str, lines: List[str], font_size: int,
                       color: str, center_x: float = 0.0, start_y: float = 0.0,
                       line_gap: float = 0.36) -> str:
    """Generate Manim code for a group of text lines, centered vertically."""
    n = len(lines)
    total_h = (n - 1) * line_gap
    code = f"        {var_prefix}_grp = VGroup()\n"
    for i, line in enumerate(lines):
        safe = line.replace('"', "'")
        y = round(start_y + total_h / 2 - i * line_gap, 3)
        code += (
            f'        {var_prefix}_l{i} = Text("{safe}", font_size={font_size},'
            f' color="{color}").move_to([{center_x},{y},0])\n'
            f'        {var_prefix}_grp.add({var_prefix}_l{i})\n'
        )
    return code


# ════════════════════════════════════════════════════════════════════
# ── DIAGRAM TEMPLATES (existing pipeline inserts) ──────────────────
# ════════════════════════════════════════════════════════════════════

# ── 1. BLOCK FLOW ──────────────────────────────────────────────────
def _render_block_flow(idx: int, params: dict, duration: int) -> str:
    title = _s(params.get("title", "Process Flow"), 52)
    boxes = [_s(b, 20) for b in params.get("boxes", ["Input", "Process", "Output"])[:6]]
    n = len(boxes)
    cols = _c(params, n)

    spacing = min(10.5 / n, 3.6)
    bw = round(min(spacing * 0.72, 2.8), 2)
    bh = round(1.1 if bw >= 2.2 else 1.0, 2)
    fs = max(13, min(22, int(bw * 8)))
    sx = round(-(n - 1) * spacing / 2.0, 3)
    wait = _w(duration, 0.7 + n * 0.9 + 0.7)

    box_code = ""
    for i, (box, col) in enumerate(zip(boxes, cols)):
        x = round(sx + i * spacing, 3)
        box_code += (
            f"\n        r{i} = RoundedRectangle(width={bw}, height={bh}, corner_radius=0.14,"
            f' color="{col}", fill_color="{col}", fill_opacity=0.18, stroke_width=2.5).move_to([{x}, 0, 0])'
            f'\n        lb{i} = Text("{box}", font_size={fs}, color="#FFFFFF", weight=BOLD).move_to([{x}, 0, 0])'
            f"\n        g{i} = VGroup(r{i}, lb{i})"
            f"\n        blist.append(g{i})"
            f"\n        self.play(FadeIn(g{i}, shift=UP*0.15), run_time=0.5)"
        )
        if i < n - 1:
            xr = round(x + bw / 2 + 0.12, 3)
            xl = round(sx + (i + 1) * spacing - bw / 2 - 0.12, 3)
            if xl - xr > 0.2:
                box_code += (
                    f'\n        self.play(GrowArrow(Arrow([{xr},0,0],[{xl},0,0],'
                    f' color="#667788", stroke_width=2.5, buff=0)), run_time=0.3)'
                )
    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        self.play(Write(title), run_time=0.7)
        blist = []
{box_code}
        if blist:
            self.play(Circumscribe(blist[-1], color="#FFE66D", fade_out=True), run_time=0.7)
        self.wait({wait})
"""


# ── 2. NEURAL NETWORK ──────────────────────────────────────────────
def _render_neural_network(idx: int, params: dict, duration: int) -> str:
    title = _s(params.get("title", "Neural Network"), 52)
    layer_sizes  = [int(x) for x in params.get("layer_sizes", [3, 4, 4, 2])[:5]]
    raw_labels   = params.get("layer_labels", [])
    layer_labels = [_s(raw_labels[i], 12) if i < len(raw_labels) else f"L{i+1}"
                    for i in range(len(layer_sizes))]
    layer_cols   = _c(params, len(layer_sizes), "layer_colors")
    n = len(layer_sizes)
    x_positions  = [round(-4.0 + i * (8.0 / max(n - 1, 1)), 2) for i in range(n)]
    wait = _w(duration, 0.7 + n * 0.5 + 1.5)

    layer_code = ""
    for i, (size, lbl, col, x) in enumerate(zip(layer_sizes, layer_labels, layer_cols, x_positions)):
        node_gap = round(min(1.0, 5.5 / max(size, 1)), 2)
        layer_code += (
            f"\n        nodes{i} = VGroup(*["
            f'\n            Circle(radius=0.23, color="{col}", fill_color="{col}",'
            f" fill_opacity=0.4, stroke_width=2.5"
            f"\n            ).move_to([{x},(j-({size}-1)/2.0)*{node_gap},0])"
            f"\n            for j in range({size})"
            f"\n        ])"
            f'\n        lbl{i} = Text("{lbl}", font_size=14, color="{_DIM}").next_to(nodes{i}, DOWN, buff=0.28)'
            f"\n        self.play(Create(nodes{i}), FadeIn(lbl{i}), run_time=0.45)"
            f"\n        layers.append(nodes{i})"
        )
    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        self.play(Write(title), run_time=0.7)
        layers = []
{layer_code}
        edges = VGroup()
        for a, b in zip(layers, layers[1:]):
            for na in a:
                for nb in b:
                    edges.add(Line(na.get_right(), nb.get_left(), stroke_width=0.6, color="#1e3a50"))
        self.play(Create(edges), run_time=1.2)
        self.wait({wait})
"""


# ── 3. BAR CHART ───────────────────────────────────────────────────
def _render_bar_chart(idx: int, params: dict, duration: int) -> str:
    title  = _s(params.get("title", "Bar Chart"), 52)
    raw_l  = params.get("labels", ["A","B","C","D"])
    raw_v  = params.get("values", [6, 9, 4, 8])
    data   = list(zip(raw_l, raw_v))[:8]
    labels = [_s(l, 12) for l, _ in data]
    values = [float(v) for _, v in data]
    n      = len(labels)
    cols   = _c(params, n)
    max_v  = max(values) if values else 1.0
    spacing = round(8.0 / n, 3)
    bw      = round(spacing * 0.72, 2)
    sx      = round(-(n - 1) * spacing / 2.0, 3)
    base_y  = -2.0
    max_h   = 3.6
    wait    = _w(duration, 0.7 + 0.4 + n * 0.55 + 0.5)

    bar_code = ""
    for i, (lbl, val, col) in enumerate(zip(labels, values, cols)):
        x   = round(sx + i * spacing, 3)
        h   = round(val / max_v * max_h, 3)
        y   = round(base_y + h / 2, 3)
        v_s = f"{val:.1f}".rstrip("0").rstrip(".")
        bar_code += (
            f"\n        bar{i} = Rectangle(width={bw}, height={h},"
            f' color="{col}", fill_color="{col}", fill_opacity=0.88, stroke_width=0)'
            f"\n        bar{i}.move_to([{x},{y},0])"
            f'\n        lbl{i} = Text("{lbl}", font_size=15, color="{_DIM}").next_to(bar{i}, DOWN, buff=0.15)'
            f'\n        vl{i}  = Text("{v_s}", font_size=14, color="{col}", weight=BOLD).next_to(bar{i}, UP, buff=0.1)'
            f"\n        self.play(GrowFromEdge(bar{i}, DOWN), FadeIn(lbl{i}), run_time=0.4)"
            f"\n        self.play(FadeIn(vl{i}), run_time=0.1)"
        )
    ax_l = round(sx - spacing * 0.6, 2)
    ax_r = round(sx + (n - 0.4) * spacing, 2)
    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        self.play(Write(title), run_time=0.7)
        baseline = Line([{ax_l},-2.0,0],[{ax_r},-2.0,0], color="#334155", stroke_width=2)
        self.play(Create(baseline), run_time=0.4)
{bar_code}
        self.wait({wait})
"""


# ── 4. LINE GRAPH ──────────────────────────────────────────────────
def _render_line_graph(idx: int, params: dict, duration: int) -> str:
    title   = _s(params.get("title", "Line Graph"), 52)
    curves  = params.get("curves", [{"label":"Data","color":"#00D9FF","values":[1,2,4,3,5]}])[:4]
    x_label = _s(params.get("x_label", "x"), 15)
    y_label = _s(params.get("y_label", "y"), 15)
    all_v   = [float(v) for c in curves for v in c.get("values", [0])]
    min_y   = min(all_v) if all_v else 0
    max_y   = max(all_v) if all_v else 1
    n_pts   = max(len(c.get("values",[])) for c in curves) if curves else 5
    pad     = max((max_y - min_y) * 0.12, 0.5)
    y_min   = round(min_y - pad, 1)
    y_max   = round(max_y + pad, 1)
    y_step  = round(max(0.1, (y_max - y_min) / 5), 1)
    x_step  = max(1, (n_pts - 1) // 5)
    wait    = _w(duration, 0.7 + 1.0 + len(curves) * 1.4)

    curve_code = ""
    for i, curve in enumerate(curves):
        lbl  = _s(curve.get("label", f"Curve {i+1}"), 18)
        col  = curve.get("color") or _COLORS[i % len(_COLORS)]
        vals = [float(v) for v in curve.get("values", [])]
        if not vals: continue
        curve_code += (
            f"\n        crv{i} = ax.plot_line_graph({list(range(len(vals)))},{vals},"
            f' line_color="{col}", vertex_dot_radius=0.07, stroke_width=3.5)'
            f'\n        ll{i} = Text("{lbl}", font_size=16, color="{col}", weight=BOLD)'
            f"\n        ll{i}.to_corner(UR, buff=0.5).shift(DOWN*{round(i*0.45,2)})"
            f"\n        self.play(Create(crv{i}), FadeIn(ll{i}), run_time=1.3)"
        )
    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        ax = Axes(x_range=[0,{n_pts-1},{x_step}],y_range=[{y_min},{y_max},{y_step}],
            x_length=9, y_length=4.5,
            axis_config={{"color":"#334155","stroke_width":2,"include_tip":True}},
        ).shift(DOWN*0.3)
        xlbl = ax.get_x_axis_label("{x_label}", font_size=18)
        ylbl = ax.get_y_axis_label("{y_label}", font_size=18)
        self.play(Write(title), run_time=0.7)
        self.play(Create(ax), FadeIn(xlbl), FadeIn(ylbl), run_time=1.0)
{curve_code}
        self.wait({wait})
"""


# ── 5. FORMULA ─────────────────────────────────────────────────────
def _render_formula(idx: int, params: dict, duration: int) -> str:
    title    = _s(params.get("title", "Formula"), 52)
    latex    = params.get("latex", r"\int_0^\infty f(x)\,dx")
    expl     = _s(params.get("explanation", ""), 70)
    expl_code = (
        f'\n        expl = Text("{expl}", font_size=20, color="{_DIM}").next_to(eq, DOWN, buff=0.65)'
        f"\n        self.play(FadeIn(expl, shift=UP*0.1), run_time=0.8)"
    ) if expl else ""
    wait = _w(duration, 0.7 + 0.5 + 2.5 + 1.0 + (0.9 if expl else 0))
    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        eq = MathTex(r"{latex}", font_size=64, color="#FFFFFF")
        eq.move_to(ORIGIN)
        box = SurroundingRectangle(eq, buff=0.55, color="#4ECDC4", stroke_width=2.5, corner_radius=0.12)
        self.play(Write(title), run_time=0.7)
        self.play(Create(box), run_time=0.5)
        self.play(Write(eq), run_time=2.5)
        self.play(Indicate(eq, color="#FFE66D", scale_factor=1.06), run_time=1.0){expl_code}
        self.wait({wait})
"""


# ── 6. TIMELINE ────────────────────────────────────────────────────
def _render_timeline(idx: int, params: dict, duration: int) -> str:
    title  = _s(params.get("title", "Timeline"), 52)
    events = params.get("events", [
        {"label":"Start","year":"2018"},{"label":"Phase 1","year":"2019"},
        {"label":"Phase 2","year":"2021"},{"label":"End","year":"2023"},
    ])[:7]
    n    = len(events)
    cols = _c(params, n)
    xs   = [round(-5.0 + i * (10.0 / max(n-1, 1)), 2) for i in range(n)]
    wait = _w(duration, 0.7 + 0.6 + n * 0.5)

    event_code = ""
    for i, (ev, x, col) in enumerate(zip(events, xs, cols)):
        lbl      = _s(ev.get("label", f"Event {i+1}"), 16)
        year     = _s(ev.get("year", ""), 8)
        direction = "UP" if i % 2 == 0 else "DOWN"
        full_lbl  = f"{year}: {lbl}" if year else lbl
        event_code += (
            f'\n        dot{i} = Dot([{x},0,0], radius=0.20, color="{col}", fill_opacity=1.0)'
            f'\n        ev{i}  = Text("{full_lbl}", font_size=15, color="{col}", weight=BOLD)'
            f"\n        ev{i}.next_to(dot{i}, {direction}, buff=0.38)"
            f"\n        self.play(FadeIn(dot{i}, scale=1.4), FadeIn(ev{i}), run_time=0.45)"
        )
    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        self.play(Write(title), run_time=0.7)
        tl = Line([-5.5,0,0],[5.5,0,0], color="#334155", stroke_width=3)
        self.play(Create(tl), run_time=0.6)
{event_code}
        self.wait({wait})
"""


# ── 7. PIE CHART ───────────────────────────────────────────────────
def _render_pie_chart(idx: int, params: dict, duration: int) -> str:
    title  = _s(params.get("title", "Distribution"), 52)
    slices = params.get("slices",[
        {"label":"A","value":40},{"label":"B","value":30},
        {"label":"C","value":20},{"label":"D","value":10},
    ])[:8]
    total  = sum(float(s.get("value",1)) for s in slices) or 1
    fracs  = [float(s.get("value",1)) / total for s in slices]
    labels = [_s(s.get("label",f"S{i+1}"), 14) for i, s in enumerate(slices)]
    cols   = [s.get("color") or _COLORS[i % len(_COLORS)] for i, s in enumerate(slices)]
    wait   = _w(duration, 0.7 + len(slices) * 0.55 + 0.5)

    sector_code = ""
    cum = 0.0
    for i, (frac, lbl, col) in enumerate(zip(fracs, labels, cols)):
        angle  = round(2 * math.pi * frac, 4)
        start  = round(cum, 4)
        mid    = round(cum + angle / 2, 4)
        lx     = round(2.2 * math.cos(mid), 3)
        ly     = round(2.2 * math.sin(mid), 3)
        pct    = round(frac * 100, 1)
        sector_code += (
            f'\n        sec{i} = AnnularSector(inner_radius=0, outer_radius=1.85, angle={angle},'
            f' start_angle={start}, color="{col}", fill_color="{col}", fill_opacity=0.9,'
            f' stroke_color="{_BG}", stroke_width=3)'
            f'\n        ll{i} = Text("{lbl}\\n{pct}%", font_size=13, color="#FFFFFF", weight=BOLD).move_to([{lx},{ly},0])'
            f"\n        self.play(FadeIn(sec{i}), FadeIn(ll{i}), run_time=0.5)"
        )
        cum += angle
    return f"""from manim import *
import math
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        self.play(Write(title), run_time=0.7)
{sector_code}
        self.wait({wait})
"""


# ── 8. CONCEPT MAP ─────────────────────────────────────────────────
def _render_concept_map(idx: int, params: dict, duration: int) -> str:
    title    = _s(params.get("title", "Concept Map"), 52)
    center   = _s(params.get("center", "Core Idea"), 20)
    branches = [
        _s(b.get("label",f"B{i+1}"),18) if isinstance(b,dict) else _s(str(b),18)
        for i, b in enumerate(params.get("branches",["A","B","C","D"])[:8])
    ]
    n    = len(branches)
    cols = _c(params, n)
    r    = 3.0
    wait = _w(duration, 0.7 + 0.6 + n * 0.55 + 0.5)

    bc = ""
    for i, (lbl, col) in enumerate(zip(branches, cols)):
        angle = round(2 * math.pi * i / n, 4)
        bx    = round(r * math.cos(angle), 3)
        by    = round(r * math.sin(angle), 3)
        mx    = round(bx * 0.52, 3)
        my    = round(by * 0.52, 3)
        bc += (
            f'\n        ln{i} = Line([{mx},{my},0],[{bx},{by},0], color="#1e3a50", stroke_width=2.5)'
            f'\n        bc{i} = Circle(radius=0.9, color="{col}", fill_color="{col}", fill_opacity=0.25, stroke_width=2.5).move_to([{bx},{by},0])'
            f'\n        bt{i} = Text("{lbl}", font_size=15, color="#FFFFFF", weight=BOLD).move_to([{bx},{by},0])'
            f"\n        self.play(Create(ln{i}), FadeIn(VGroup(bc{i},bt{i})), run_time=0.5)"
        )
    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        self.play(Write(title), run_time=0.7)
        core_c = Circle(radius=1.15, color="#00D9FF", fill_color="#00D9FF", fill_opacity=0.28, stroke_width=2.5)
        core_t = Text("{center}", font_size=20, color="#FFFFFF", weight=BOLD)
        core = VGroup(core_c, core_t)
        self.play(FadeIn(core, scale=0.7), run_time=0.6)
{bc}
        self.play(Circumscribe(core, color="#FFE66D", fade_out=True), run_time=0.5)
        self.wait({wait})
"""


# ── 9. VENN DIAGRAM ────────────────────────────────────────────────
def _render_venn_diagram(idx: int, params: dict, duration: int) -> str:
    title  = _s(params.get("title", "Venn Diagram"), 52)
    ca     = _s(params.get("circle_a", "Set A"), 18)
    cb     = _s(params.get("circle_b", "Set B"), 18)
    inter  = _s(params.get("intersection", "Both"), 20)
    items_a = [_s(x, 16) for x in params.get("items_a", [])[:3]]
    items_b = [_s(x, 16) for x in params.get("items_b", [])[:3]]
    wait   = _w(duration, 0.7 + 1.1 + 0.5 + 0.5 + 0.65 + len(items_a + items_b) * 0.3)

    ia = "".join(
        f'\n        Text("{item}", font_size=15, color="#B3D9FF").move_to([-3.0,{round(0.5 - i*0.6,2)},0]),'
        for i, item in enumerate(items_a)
    )
    ib = "".join(
        f'\n        Text("{item}", font_size=15, color="#FFB3B3").move_to([3.0,{round(0.5 - i*0.6,2)},0]),'
        for i, item in enumerate(items_b)
    )
    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        self.play(Write(title), run_time=0.7)
        c1 = Circle(radius=2.2, color="#0066FF", fill_color="#0066FF", fill_opacity=0.22, stroke_width=2.5).shift(LEFT*1.3)
        c2 = Circle(radius=2.2, color="#FF6B6B", fill_color="#FF6B6B", fill_opacity=0.22, stroke_width=2.5).shift(RIGHT*1.3)
        self.play(Create(c1), Create(c2), run_time=1.1)
        la = Text("{ca}", font_size=21, color="#4499FF", weight=BOLD).move_to([-3.5,0,0])
        lb = Text("{cb}", font_size=21, color="#FF6B6B", weight=BOLD).move_to([3.5,0,0])
        li = Text("{inter}", font_size=19, color="#FFFFFF", weight=BOLD).move_to([0,0,0])
        self.play(FadeIn(la), FadeIn(lb), run_time=0.5)
        self.play(Write(li), run_time=0.5)
        self.play(Circumscribe(li, color="#FFE66D", fade_out=True), run_time=0.65)
        items_a = VGroup({ia or 'Text("",font_size=1)'})
        items_b = VGroup({ib or 'Text("",font_size=1)'})
        self.play(LaggedStart(*[FadeIn(x) for x in items_a], lag_ratio=0.3), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(x) for x in items_b], lag_ratio=0.3), run_time=0.6)
        self.wait({wait})
"""


# ════════════════════════════════════════════════════════════════════
# ── NEW DIAGRAM TEMPLATES ──────────────────────────────────────────
# ════════════════════════════════════════════════════════════════════

# ── 10. STEP-BY-STEP ───────────────────────────────────────────────
def _render_step_by_step(idx: int, params: dict, duration: int) -> str:
    title = _s(params.get("title", "Steps"), 52)
    steps = [_s(s, 50) for s in params.get("steps", ["Step 1", "Step 2", "Step 3"])[:6]]
    n     = len(steps)
    cols  = _c(params, n)
    wait  = _w(duration, 0.7 + n * 0.75)

    step_code = ""
    y_start = 2.0
    y_gap   = min(1.0, 4.5 / max(n, 1))
    for i, (step, col) in enumerate(zip(steps, cols)):
        y = round(y_start - i * y_gap * 1.3, 3)
        step_code += (
            f'\n        num{i} = Text("{i+1}", font_size=22, color="{col}", weight=BOLD)'
            f'\n        circ{i} = Circle(radius=0.28, color="{col}", fill_color="{col}", fill_opacity=0.3, stroke_width=2)'
            f'\n        circ{i}.move_to([-5.5,{y},0])'
            f'\n        num{i}.move_to([-5.5,{y},0])'
            f'\n        txt{i} = Text("{step}", font_size=20, color="{_WHITE}").next_to(circ{i}, RIGHT, buff=0.35)'
            f"\n        txt{i}.align_to(circ{i}, UP).shift(DOWN*0.05)"
            f"\n        self.play(FadeIn(VGroup(circ{i},num{i})), Write(txt{i}), run_time=0.65)"
        )
        if i < n - 1:
            y2 = round(y - y_gap * 0.55, 3)
            step_code += f'\n        self.play(Create(Line([-5.5,{y-0.3},0],[-5.5,{y2},0],color="#334155",stroke_width=2)), run_time=0.1)'
    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        self.play(Write(title), run_time=0.7)
{step_code}
        self.wait({wait})
"""


# ── 11. COMPARISON TABLE ───────────────────────────────────────────
def _render_comparison_table(idx: int, params: dict, duration: int) -> str:
    title  = _s(params.get("title", "Comparison"), 52)
    col_a  = _s(params.get("col_a", "Option A"), 20)
    col_b  = _s(params.get("col_b", "Option B"), 20)
    rows   = [(
        _s(r.get("a", ""), 30), _s(r.get("b", ""), 30)
    ) for r in params.get("rows", [])[:6]]
    if not rows:
        rows = [("Feature 1","Feature 1"),("Feature 2","Feature 2")]
    n    = len(rows)
    wait = _w(duration, 0.7 + 0.8 + n * 0.5)

    row_code = ""
    for i, (a, b) in enumerate(rows):
        y = round(1.6 - i * 0.85, 3)
        bg_col = '"#0d1f35"' if i % 2 == 0 else '"#0a1828"'
        row_code += (
            f'\n        rb{i} = Rectangle(width=11, height=0.72, color={bg_col},'
            f' fill_color={bg_col}, fill_opacity=1, stroke_width=0).move_to([0,{y},0])'
            f'\n        ra{i} = Text("{a}", font_size=18, color="{_WHITE}").move_to([-2.6,{y},0])'
            f'\n        rc{i} = Text("{b}", font_size=18, color="{_WHITE}").move_to([2.6,{y},0])'
            f'\n        div{i} = Line([0,{round(y+0.36,3)},0],[0,{round(y-0.36,3)},0], color="#1e3a50", stroke_width=1.5)'
            f"\n        self.play(FadeIn(VGroup(rb{i},ra{i},rc{i},div{i})), run_time=0.4)"
        )
    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        self.play(Write(title), run_time=0.7)
        hdr_a = Text("{col_a}", font_size=22, color="#00D9FF", weight=BOLD).move_to([-2.6, 2.4, 0])
        hdr_b = Text("{col_b}", font_size=22, color="#FF6B6B", weight=BOLD).move_to([2.6, 2.4, 0])
        hdiv  = Line([-5.5, 2.1, 0],[5.5, 2.1, 0], color="#334155", stroke_width=2)
        vdiv  = Line([0, 2.6, 0],[0, {round(1.6 - (n-1)*0.85 - 0.36, 2)}, 0], color="#334155", stroke_width=2)
        self.play(FadeIn(hdr_a), FadeIn(hdr_b), Create(hdiv), Create(vdiv), run_time=0.8)
{row_code}
        self.wait({wait})
"""


# ── 12. MATH STEPS (multi-step derivation) ─────────────────────────
def _render_math_steps(idx: int, params: dict, duration: int) -> str:
    title  = _s(params.get("title", "Derivation"), 52)
    steps  = params.get("steps", [
        {"eq": r"f(x) = x^2", "note": "Starting function"},
        {"eq": r"f'(x) = 2x", "note": "Apply power rule"},
    ])[:5]
    n     = len(steps)
    cols  = _c(params, n)
    wait  = _w(duration, 0.7 + n * 1.5)

    step_code = ""
    ys = [round(1.8 - i * (3.8 / max(n, 1)), 2) for i in range(n)]
    for i, (step, col, y) in enumerate(zip(steps, cols, ys)):
        eq   = step.get("eq", r"x = x")
        note = _s(step.get("note", ""), 40)
        step_code += (
            f'\n        eq{i} = MathTex(r"{eq}", font_size=42, color="#FFFFFF")'
            f"\n        eq{i}.move_to([0,{y},0])"
            f"\n        self.play(Write(eq{i}), run_time=1.2)"
        )
        if note:
            step_code += (
                f'\n        nt{i} = Text("{note}", font_size=16, color="{col}")'
                f"\n        nt{i}.next_to(eq{i}, RIGHT, buff=0.6)"
                f"\n        self.play(FadeIn(nt{i}, shift=LEFT*0.1), run_time=0.3)"
            )
        if i < n - 1:
            ay = round(y - 0.55, 2)
            step_code += (
                f'\n        self.play(Create(Arrow([0,{ay+0.18},0],[0,{round(ys[i+1]+0.55,2)},0],'
                f' color="#334155", stroke_width=2, buff=0)), run_time=0.25)'
            )
    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        self.play(Write(title), run_time=0.7)
{step_code}
        self.wait({wait})
"""


# ── 13. DEFINITION BOX  (FIXED — multi-line text stays inside box) ──
def _render_definition_box(idx: int, params: dict, duration: int) -> str:
    title   = _s(params.get("title", "Definition"), 52)
    term    = _s(params.get("term", "Term"), 28)
    color   = params.get("color", "#00D9FF")
    example = _s(params.get("example", ""), 80)

    # Raw definition — clean it then wrap into lines that fit inside the box
    raw_defn = re.sub(r"[^\x20-\x7E]", "", str(params.get("definition", "The meaning of the term.")))
    raw_defn = raw_defn.replace('"', "'").replace("\\", "").replace("\n", " ").strip()
    # Box is ~10.5 wide. At font_size 18, ~55 chars per line comfortably
    defn_lines = _wrap_text(raw_defn, max_chars_per_line=52)[:4]   # max 4 lines inside box

    # Example wrapping
    ex_lines = _wrap_text(example, max_chars_per_line=60)[:2] if example else []

    # Build voiceover-friendly vertical layout
    # Box occupies centre: top=0.8, bottom=-1.2  (total h ~3.2 → fits term + 4 defn lines)
    BOX_TOP = 0.9
    BOX_BTM = -1.3
    box_h   = BOX_TOP - BOX_BTM  # 2.2
    n_defn  = len(defn_lines)

    # Term sits near top of box
    term_y = round(BOX_TOP - 0.45, 2)
    # Definition lines start below term
    defn_start_y = round(term_y - 0.55, 2)
    defn_gap     = 0.40

    defn_code = ""
    for i, line in enumerate(defn_lines):
        y = round(defn_start_y - i * defn_gap, 3)
        safe_line = line.replace('"', "'")
        defn_code += (
            f'\n        dl{i} = Text("{safe_line}", font_size=18, color="{_WHITE}").move_to([0,{y},0])'
            f"\n        self.play(FadeIn(dl{i}, shift=UP*0.08), run_time=0.35)"
        )

    # Example below box
    ex_code = ""
    if ex_lines:
        ex_label_y = round(BOX_BTM - 0.45, 2)
        ex_code += (
            f'\n        ex_lbl = Text("Example:", font_size=16, color="{_DIM}", weight=BOLD)'
            f'\n        ex_lbl.move_to([0,{ex_label_y},0])'
            f"\n        self.play(FadeIn(ex_lbl), run_time=0.3)"
        )
        for j, exl in enumerate(ex_lines):
            ey = round(ex_label_y - 0.38 - j * 0.35, 3)
            safe_exl = exl.replace('"', "'")
            ex_code += (
                f'\n        etxt{j} = Text("{safe_exl}", font_size=16, color="{_WHITE}").move_to([0,{ey},0])'
                f"\n        self.play(FadeIn(etxt{j}), run_time=0.25)"
            )

    box_center_y = round((BOX_TOP + BOX_BTM) / 2, 2)
    wait = _w(duration, 0.7 + 0.5 + 0.5 + 0.4 + n_defn * 0.4 + (0.6 if ex_lines else 0))

    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        self.play(Write(title), run_time=0.7)
        box = RoundedRectangle(
            width=11.0, height={round(box_h + 0.4, 2)}, corner_radius=0.2,
            color="{color}", fill_color="{color}", fill_opacity=0.08, stroke_width=2.5
        ).move_to([0, {box_center_y}, 0])
        self.play(Create(box), run_time=0.5)
        term_txt = Text("{term}", font_size=26, color="{color}", weight=BOLD)
        term_txt.move_to([0, {term_y}, 0])
        self.play(Write(term_txt), run_time=0.5)
        self.play(Indicate(term_txt, color="#FFE66D", scale_factor=1.07), run_time=0.4)
{defn_code}{ex_code}
        self.wait({wait})
"""


# ── 14. CALCULUS PLOT ──────────────────────────────────────────────
def _render_calculus_plot(idx: int, params: dict, duration: int) -> str:
    title      = _s(params.get("title", "Function Analysis"), 52)
    func_latex = params.get("func_latex", r"f(x) = x^2")
    func_expr  = params.get("func_expr", "x**2")
    x_range    = params.get("x_range", [-3, 3])
    y_range    = params.get("y_range", [-1, 9])
    show_area  = params.get("show_area", False)
    area_range = params.get("area_range", [0, 2])
    color      = params.get("color", "#00D9FF")
    wait       = _w(duration, 0.7 + 1.0 + 1.5 + 0.8 + (1.0 if show_area else 0))

    area_code = ""
    if show_area:
        a1, a2 = area_range[0], area_range[1]
        area_code = (
            f'\n        area = ax.get_area(curve, x_range=[{a1},{a2}], color="{color}", opacity=0.3)'
            f"\n        self.play(FadeIn(area), run_time=1.0)"
            f'\n        area_lbl = MathTex(r"\\\\int_{{{a1}}}^{{{a2}}}", font_size=28, color="{color}").next_to(area, RIGHT, buff=0.2)'
            f"\n        self.play(Write(area_lbl), run_time=0.5)"
        )
    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        ax = Axes(x_range=[{x_range[0]},{x_range[1]},1], y_range=[{y_range[0]},{y_range[1]},2],
            x_length=9, y_length=4.5,
            axis_config={{"color":"#334155","stroke_width":2,"include_tip":True}},
        ).shift(DOWN*0.2)
        func_lbl = MathTex(r"{func_latex}", font_size=28, color="{color}").to_corner(UR, buff=0.5)
        self.play(Write(title), run_time=0.7)
        self.play(Create(ax), run_time=1.0)
        curve = ax.plot(lambda x: {func_expr}, x_range=[{x_range[0]},{x_range[1]}],
            color="{color}", stroke_width=3)
        self.play(Create(curve), Write(func_lbl), run_time=1.5)
        self.play(Indicate(curve, color="#FFE66D", scale_factor=1.04), run_time=0.8){area_code}
        self.wait({wait})
"""


# ── 15. MATRIX DISPLAY ─────────────────────────────────────────────
def _render_matrix_display(idx: int, params: dict, duration: int) -> str:
    title   = _s(params.get("title", "Matrix"), 52)
    matrix  = params.get("matrix", [[1,0],[0,1]])
    m_latex = params.get("matrix_latex", "")
    label   = _s(params.get("label", "A"), 5)
    color   = params.get("color", "#00D9FF")
    note    = _s(params.get("note", ""), 70)
    wait    = _w(duration, 0.7 + 0.5 + 2.0 + 0.8 + (0.6 if note else 0))

    if not m_latex:
        rows = " \\\\\\\\ ".join(
            " & ".join(str(v) for v in row)
            for row in matrix
        )
        m_latex = f"\\\\begin{{bmatrix}} {rows} \\\\end{{bmatrix}}"

    note_code = ""
    if note:
        note_code = (
            f'\n        nt = Text("{note}", font_size=18, color="{_DIM}").next_to(full_eq, DOWN, buff=0.6)'
            f"\n        self.play(FadeIn(nt, shift=UP*0.1), run_time=0.6)"
        )
    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        self.play(Write(title), run_time=0.7)
        lbl = MathTex(r"{label} =", font_size=52, color="{color}")
        mat = MathTex(r"{m_latex}", font_size=52, color="#FFFFFF")
        full_eq = VGroup(lbl, mat).arrange(RIGHT, buff=0.3).move_to([0,0.2,0])
        box = SurroundingRectangle(full_eq, buff=0.45, color="{color}", stroke_width=2, corner_radius=0.12)
        self.play(Create(box), run_time=0.5)
        self.play(Write(full_eq), run_time=2.0)
        self.play(Indicate(full_eq, color="#FFE66D", scale_factor=1.05), run_time=0.8){note_code}
        self.wait({wait})
"""


# ── 16. TREE DIAGRAM ───────────────────────────────────────────────
def _render_tree_diagram(idx: int, params: dict, duration: int) -> str:
    title  = _s(params.get("title", "Tree Diagram"), 52)
    root   = _s(params.get("root", "Root"), 18)
    children = [_s(c, 16) for c in params.get("children", ["A","B","C"])[:5]]
    grandchildren = params.get("grandchildren", {})
    nc   = len(children)
    cols = _c(params, nc + 1)
    wait = _w(duration, 0.7 + 0.5 + nc * 0.5 + 0.5)

    child_xs = [round(-4.0 + i * (8.0 / max(nc-1, 1)), 2) for i in range(nc)]

    child_code = ""
    for i, (ch, col, cx) in enumerate(zip(children, cols[1:], child_xs)):
        child_code += (
            f'\n        cn{i} = RoundedRectangle(width=1.8, height=0.65, corner_radius=0.1,'
            f' color="{col}", fill_color="{col}", fill_opacity=0.2, stroke_width=2).move_to([{cx},-1.0,0])'
            f'\n        ct{i} = Text("{ch}", font_size=16, color="#FFFFFF", weight=BOLD).move_to([{cx},-1.0,0])'
            f"\n        edge{i} = Line([0,0.32,0],[{cx},-0.68,0], color=\"#334155\", stroke_width=2)"
            f"\n        self.play(Create(edge{i}), FadeIn(VGroup(cn{i},ct{i})), run_time=0.45)"
        )
        gc_list = grandchildren.get(i, grandchildren.get(str(i), []))
        for j, gc in enumerate(gc_list[:3]):
            gc_label = _s(gc, 12)
            gc_x = round(cx - 1.2 + j * 1.2, 2)
            child_code += (
                f'\n        gc{i}_{j} = RoundedRectangle(width=1.4, height=0.5, corner_radius=0.08,'
                f' color="#334155", fill_color="#1e3a50", fill_opacity=0.5, stroke_width=1.5).move_to([{gc_x},-2.3,0])'
                f'\n        gt{i}_{j} = Text("{gc_label}", font_size=13, color="{_DIM}").move_to([{gc_x},-2.3,0])'
                f"\n        ge{i}_{j} = Line([{cx},-1.33,0],[{gc_x},-2.05,0], color=\"#1e3a50\", stroke_width=1.5)"
                f"\n        self.play(Create(ge{i}_{j}), FadeIn(VGroup(gc{i}_{j},gt{i}_{j})), run_time=0.3)"
            )
    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        self.play(Write(title), run_time=0.7)
        root_c = RoundedRectangle(width=2.2, height=0.75, corner_radius=0.12,
            color="{cols[0]}", fill_color="{cols[0]}", fill_opacity=0.25, stroke_width=2.5).move_to([0, 1.5, 0])
        root_t = Text("{root}", font_size=19, color="#FFFFFF", weight=BOLD).move_to([0, 1.5, 0])
        self.play(FadeIn(VGroup(root_c, root_t)), run_time=0.5)
{child_code}
        self.wait({wait})
"""


# ── 17. GRADIENT DESCENT VIZ ───────────────────────────────────────
def _render_gradient_descent(idx: int, params: dict, duration: int) -> str:
    title   = _s(params.get("title", "Gradient Descent"), 52)
    n_steps = min(int(params.get("steps", 5)), 8)
    lr      = float(params.get("learning_rate", 0.3))
    color   = params.get("color", "#00D9FF")
    wait    = _w(duration, 0.7 + 1.0 + 1.5 + n_steps * 0.6)

    x = 2.5
    xs = [x]
    for _ in range(n_steps - 1):
        x = x - lr * 2 * x
        xs.append(round(x, 3))

    dot_code = ""
    for i, xv in enumerate(xs):
        yv = round(xv * xv, 3)
        col_i = _COLORS[i % len(_COLORS)]
        dot_code += (
            f'\n        pt{i} = Dot(ax.coords_to_point({round(xv,3)},{min(yv,8.0)}), radius=0.12,'
            f' color="{col_i}", fill_opacity=1.0)'
            f"\n        self.play(FadeIn(pt{i}, scale=1.5), run_time=0.4)"
        )
        if i < len(xs) - 1:
            xn = xs[i + 1]
            yn = round(xn * xn, 3)
            dot_code += (
                f'\n        arr{i} = Arrow(ax.coords_to_point({round(xv,3)},{min(yv,8.0)}),'
                f'ax.coords_to_point({round(xn,3)},{min(yn,8.0)}), color="#334155", stroke_width=2, buff=0.08)'
                f"\n        self.play(GrowArrow(arr{i}), run_time=0.2)"
            )
    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        ax = Axes(x_range=[-3,3,1], y_range=[-0.5,9,2], x_length=9, y_length=4.5,
            axis_config={{"color":"#334155","stroke_width":2,"include_tip":True}},
        ).shift(DOWN*0.2)
        func_lbl = MathTex(r"J(\\theta) = \\theta^2", font_size=26, color="{color}").to_corner(UR, buff=0.5)
        self.play(Write(title), run_time=0.7)
        self.play(Create(ax), FadeIn(func_lbl), run_time=1.0)
        curve = ax.plot(lambda x: x**2, x_range=[-3,3], color="{color}", stroke_width=3)
        self.play(Create(curve), run_time=1.5)
{dot_code}
        self.wait({wait})
"""


# ── 18. PROBABILITY DISTRIBUTION ───────────────────────────────────
def _render_probability_dist(idx: int, params: dict, duration: int) -> str:
    title  = _s(params.get("title", "Probability Distribution"), 52)
    mean   = float(params.get("mean", 0))
    std    = float(params.get("std", 1))
    color  = params.get("color", "#00D9FF")
    labels = params.get("labels", [])
    wait   = _w(duration, 0.7 + 1.0 + 1.5 + 0.8)

    label_code = ""
    for i, lbl in enumerate(labels[:3]):
        x_val  = _s(lbl.get("x", "0"), 5)
        lbl_s  = _s(lbl.get("label", ""), 15)
        label_code += (
            f'\n        vl{i} = DashedLine(ax.coords_to_point({x_val},-0.02),'
            f'ax.coords_to_point({x_val},0.38), color="#FFE66D", stroke_width=2)'
            f'\n        lt{i} = Text("{lbl_s}", font_size=14, color="#FFE66D")'
            f"\n        lt{i}.next_to(ax.coords_to_point({x_val},0), DOWN, buff=0.15)"
            f"\n        self.play(Create(vl{i}), FadeIn(lt{i}), run_time=0.4)"
        )

    return f"""from manim import *
import numpy as np
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        ax = Axes(x_range=[{mean-3.5*std},{mean+3.5*std},{std}], y_range=[-0.05, 0.45, 0.1],
            x_length=9, y_length=4.0,
            axis_config={{"color":"#334155","stroke_width":2,"include_tip":True}},
        ).shift(DOWN*0.2)
        self.play(Write(title), run_time=0.7)
        self.play(Create(ax), run_time=1.0)
        curve = ax.plot(
            lambda x: (1/(({std})*np.sqrt(2*np.pi)))*np.exp(-0.5*((x-{mean})/{std})**2),
            x_range=[{mean-3.5*std},{mean+3.5*std}], color="{color}", stroke_width=3.5
        )
        area = ax.get_area(curve, x_range=[{mean-std},{mean+std}], color="{color}", opacity=0.25)
        self.play(Create(curve), run_time=1.5)
        self.play(FadeIn(area), run_time=0.8)
{label_code}
        self.wait({wait})
"""


# ════════════════════════════════════════════════════════════════════
# ── FULL SCENE TEMPLATES (Topic Video pipeline) ────────────────────
# ════════════════════════════════════════════════════════════════════

# ── S1. TITLE CARD ─────────────────────────────────────────────────
def _render_title_card(idx: int, params: dict, duration: int) -> str:
    title    = _s(params.get("title", "Topic Title"), 55)
    subtitle = _s(params.get("subtitle", ""), 80)
    color    = params.get("color", "#00D9FF")
    wait     = _w(duration, 0.8 + 1.5 + (0.7 if subtitle else 0) + 0.5)

    sub_code = ""
    if subtitle:
        sub_code = (
            f'\n        sub = Text("{subtitle}", font_size=26, color="{_DIM}")'
            f'\n        sub.next_to(title_txt, DOWN, buff=0.55)'
            f"\n        self.play(FadeIn(sub, shift=UP*0.15), run_time=0.7)"
        )
    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        bg_rect = Rectangle(width=16, height=9, fill_color="{_BG}", fill_opacity=1, stroke_width=0)
        accent_line = Line([-7,0,0],[7,0,0], color="{color}", stroke_width=3)
        accent_line.shift(DOWN*0.55)
        self.add(bg_rect)
        title_txt = Text("{title}", font_size=52, color="{color}", weight=BOLD)
        title_txt.shift(UP*0.3)
        self.play(Write(title_txt), run_time=1.5){sub_code}
        self.play(Create(accent_line), run_time=0.5)
        self.wait({wait})
"""


# ── S2. BULLET LIST SCENE ──────────────────────────────────────────
def _render_bullet_list(idx: int, params: dict, duration: int) -> str:
    title   = _s(params.get("title", "Key Points"), 55)
    bullets = [_s(b, 75) for b in params.get("bullets", ["Point 1","Point 2","Point 3"])[:6]]
    color   = params.get("color", "#00D9FF")
    n       = len(bullets)
    wait    = _w(duration, 0.7 + n * 0.7 + 0.3)

    y_start = 1.8
    y_step  = min(1.1, 4.0 / max(n, 1))

    bullet_code = ""
    for i, b in enumerate(bullets):
        y     = round(y_start - i * y_step, 2)
        col   = _COLORS[i % len(_COLORS)]
        bullet_code += (
            f'\n        dot{i} = Dot([-5.6,{y},0], radius=0.1, color="{col}")'
            f'\n        bt{i}  = Text("{b}", font_size=21, color="{_WHITE}")'
            f'\n        bt{i}.next_to(dot{i}, RIGHT, buff=0.28).align_to(dot{i}, UP).shift(DOWN*0.06)'
            f"\n        self.play(FadeIn(dot{i}), Write(bt{i}), run_time=0.6)"
        )
    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="{color}", weight=BOLD).to_edge(UP, buff=0.35)
        uline = Line(title.get_left(), title.get_right(), color="{color}", stroke_width=2.5)
        uline.next_to(title, DOWN, buff=0.08)
        self.play(Write(title), Create(uline), run_time=0.7)
{bullet_code}
        self.wait({wait})
"""


# ── S3. WORKED EXAMPLE ─────────────────────────────────────────────
def _render_worked_example(idx: int, params: dict, duration: int) -> str:
    title    = _s(params.get("title", "Example"), 52)
    problem  = params.get("problem", r"Solve: x^2 = 4")
    solution_steps = params.get("solution_steps", [
        {"eq": r"x^2 = 4", "note": "Given"},
        {"eq": r"x = \pm\sqrt{4}", "note": "Take square root"},
        {"eq": r"x = \pm 2", "note": "Answer"},
    ])
    n    = len(solution_steps[:5])
    wait = _w(duration, 0.7 + 0.6 + 0.8 + n * 1.3)

    step_code = ""
    ys = [round(1.2 - i * (3.0 / max(n, 1)), 2) for i in range(n)]
    for i, (step, y) in enumerate(zip(solution_steps[:5], ys)):
        eq   = step.get("eq", r"x = x")
        note = _s(step.get("note", ""), 35)
        col  = _COLORS[i % len(_COLORS)]
        step_code += (
            f'\n        eq{i} = MathTex(r"{eq}", font_size=38, color="#FFFFFF").move_to([-1,{y},0])'
            f'\n        nt{i} = Text("{note}", font_size=15, color="{col}").next_to(eq{i}, RIGHT, buff=0.5)'
            f"\n        self.play(Write(eq{i}), FadeIn(nt{i}), run_time=0.9)"
        )
        if i < n - 1:
            step_code += (
                f'\n        self.play(Create(Arrow([0,{round(y-0.45,2)},0],[0,{round(ys[i+1]+0.45,2)},0],'
                f'color="#334155",stroke_width=2,buff=0)),run_time=0.2)'
            )

    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        prob  = MathTex(r"{problem}", font_size=28, color="#FFE66D")
        prob.to_edge(UP, buff=0.9)
        prob_box = SurroundingRectangle(prob, buff=0.2, color="#FFE66D", stroke_width=1.5, corner_radius=0.08)
        self.play(Write(title), run_time=0.7)
        self.play(Create(prob_box), Write(prob), run_time=0.8)
{step_code}
        self.wait({wait})
"""


# ── S4. SUMMARY CARD ───────────────────────────────────────────────
def _render_summary_card(idx: int, params: dict, duration: int) -> str:
    title   = _s(params.get("title", "Key Takeaways"), 52)
    points  = [_s(p, 65) for p in params.get("points", ["Point 1","Point 2","Point 3"])[:5]]
    color   = params.get("color", "#34D399")
    n       = len(points)
    wait    = _w(duration, 0.7 + 0.5 + n * 0.55 + 0.4)

    y_start = 1.6
    y_step  = min(0.95, 3.6 / max(n, 1))

    pt_code = ""
    for i, pt in enumerate(points):
        y   = round(y_start - i * y_step, 2)
        col = _COLORS[i % len(_COLORS)]
        pt_code += (
            f'\n        ic{i} = Text("checkmark", font_size=18, color="{col}", weight=BOLD).move_to([-5.5,{y},0])'
            f'\n        pt{i} = Text("{pt}", font_size=20, color="{_WHITE}").next_to(ic{i}, RIGHT, buff=0.3).align_to(ic{i}, UP).shift(DOWN*0.04)'
            f"\n        self.play(FadeIn(ic{i}), Write(pt{i}), run_time=0.5)"
        )

    # Use a simple check mark rendered as a Text "✓" — but since we restrict to ASCII in _s,
    # use a Circle + Line combo for the check instead
    pt_code2 = ""
    for i, pt in enumerate(points):
        y   = round(y_start - i * y_step, 2)
        col = _COLORS[i % len(_COLORS)]
        pt_code2 += (
            f'\n        ck{i} = Circle(radius=0.18, color="{col}", fill_color="{col}", fill_opacity=0.3, stroke_width=2).move_to([-5.5,{y},0])'
            f'\n        pt{i} = Text("{pt}", font_size=20, color="{_WHITE}").next_to(ck{i}, RIGHT, buff=0.3).align_to(ck{i}, UP).shift(DOWN*0.04)'
            f"\n        self.play(FadeIn(ck{i}), Write(pt{i}), run_time=0.5)"
        )

    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        bg_box = RoundedRectangle(width=12, height=7.5, corner_radius=0.3,
            color="{color}", fill_color="{color}", fill_opacity=0.05, stroke_width=2)
        bg_box.move_to([0,-0.2,0])
        self.add(bg_box)
        title = Text("{title}", font_size=34, color="{color}", weight=BOLD).to_edge(UP, buff=0.35)
        self.play(Write(title), run_time=0.7)
        sep = Line([-5.5,2.1,0],[5.5,2.1,0], color="{color}", stroke_width=1.5)
        self.play(Create(sep), run_time=0.5)
{pt_code2}
        self.wait({wait})
"""


# ── S5. PHYSICS FORCES ─────────────────────────────────────────────
def _render_physics_forces(idx: int, params: dict, duration: int) -> str:
    title   = _s(params.get("title", "Forces"), 52)
    body    = _s(params.get("body", "Object"), 14)
    forces  = params.get("forces", [
        {"label":"F_g","dx":0,"dy":-1.5,"color":"#FF6B6B"},
        {"label":"N","dx":0,"dy":1.5,"color":"#00D9FF"},
    ])[:6]
    n    = len(forces)
    wait = _w(duration, 0.7 + 0.5 + n * 0.6 + 0.5)

    force_code = ""
    for i, f in enumerate(forces):
        lbl  = _s(f.get("label","F"), 8)
        dx   = round(float(f.get("dx", 1)), 2)
        dy   = round(float(f.get("dy", 0)), 2)
        col  = f.get("color", _COLORS[i % len(_COLORS)])
        scale = math.sqrt(dx**2 + dy**2)
        if scale > 0.001:
            end_x = round(dx, 2)
            end_y = round(dy, 2)
            force_code += (
                f'\n        arr{i} = Arrow([0,0,0],[{end_x},{end_y},0], color="{col}",'
                f' stroke_width=4, buff=0, max_tip_length_to_length_ratio=0.25)'
                f'\n        lbl{i} = MathTex(r"{lbl}", font_size=28, color="{col}")'
                f"\n        lbl{i}.next_to(arr{i}.get_end(), RIGHT if {dx}>=0 else LEFT, buff=0.15)"
                f"\n        self.play(GrowArrow(arr{i}), Write(lbl{i}), run_time=0.55)"
            )
    return f"""from manim import *
class Slide{idx}(Scene):
    def construct(self):
        self.camera.background_color = "{_BG}"
        title = Text("{title}", font_size=32, color="#00D9FF", weight=BOLD).to_edge(UP, buff=0.35)
        self.play(Write(title), run_time=0.7)
        body_sq = RoundedRectangle(width=1.6, height=1.6, corner_radius=0.15,
            color="#4ECDC4", fill_color="#4ECDC4", fill_opacity=0.25, stroke_width=2.5)
        body_lbl = Text("{body}", font_size=18, color="#FFFFFF", weight=BOLD)
        body_g = VGroup(body_sq, body_lbl)
        self.play(FadeIn(body_g, scale=0.8), run_time=0.5)
{force_code}
        self.wait({wait})
"""


# ════════════════════════════════════════════════════════════════════
# REGISTRIES
# ════════════════════════════════════════════════════════════════════

DIAGRAM_REGISTRY: Dict[str, Any] = {
    "block_flow":           _render_block_flow,
    "neural_network":       _render_neural_network,
    "bar_chart":            _render_bar_chart,
    "line_graph":           _render_line_graph,
    "formula":              _render_formula,
    "timeline":             _render_timeline,
    "pie_chart":            _render_pie_chart,
    "concept_map":          _render_concept_map,
    "venn_diagram":         _render_venn_diagram,
    "step_by_step":         _render_step_by_step,
    "comparison_table":     _render_comparison_table,
    "math_steps":           _render_math_steps,
    "definition_box":       _render_definition_box,
    "calculus_plot":        _render_calculus_plot,
    "matrix_display":       _render_matrix_display,
    "tree_diagram":         _render_tree_diagram,
    "gradient_descent":     _render_gradient_descent,
    "probability_dist":     _render_probability_dist,
    "title_card":           _render_title_card,
    "bullet_list":          _render_bullet_list,
    "worked_example":       _render_worked_example,
    "summary_card":         _render_summary_card,
    "physics_forces":       _render_physics_forces,
}

AVAILABLE_DIAGRAM_TYPES = sorted(DIAGRAM_REGISTRY.keys())

SCENE_REGISTRY = DIAGRAM_REGISTRY
AVAILABLE_SCENE_TYPES = AVAILABLE_DIAGRAM_TYPES


DIAGRAM_SCHEMAS = """
AVAILABLE DIAGRAM / SCENE TYPES:

block_flow:       boxes: list[str], colors?: list[str]
neural_network:   layer_sizes: list[int], layer_labels: list[str], layer_colors?: list[str]
bar_chart:        labels: list[str], values: list[float], y_label?: str
line_graph:       curves: [{label,color?,values:[float]}], x_label?, y_label?
formula:          latex: str, explanation?: str
timeline:         events: [{label,year}]
pie_chart:        slices: [{label,value,color?}]
concept_map:      center: str, branches: [{label}]
venn_diagram:     circle_a, circle_b, intersection: str, items_a?, items_b?: list[str]
step_by_step:     steps: list[str], colors?: list[str]
comparison_table: col_a, col_b: str, rows: [{a,b}]
math_steps:       steps: [{eq: latex_str, note: str}]
definition_box:   term: str, definition: str (keep under 200 chars), example?: str (keep under 80 chars), color?: str
calculus_plot:    func_latex, func_expr: str, x_range, y_range: [min,max], show_area?: bool, area_range?: [a,b]
matrix_display:   label: str, matrix?: [[values]], matrix_latex?: str, note?: str
tree_diagram:     root: str, children: list[str], grandchildren?: {int: list[str]}
gradient_descent: steps?: int, learning_rate?: float
probability_dist: mean?: float, std?: float, labels?: [{x,label}]
title_card:       title: str, subtitle?: str, color?: str
bullet_list:      title: str, bullets: list[str], color?: str
worked_example:   problem: latex_str, solution_steps: [{eq: latex_str, note: str}]
summary_card:     title: str, points: list[str], color?: str
physics_forces:   body?: str, forces: [{label, dx, dy, color?}]
"""


def get_diagram_code(slide_idx: int, params: dict, duration: int) -> Optional[str]:
    dtype    = params.get("type", "block_flow")
    renderer = DIAGRAM_REGISTRY.get(dtype)
    if renderer is None:
        logger.warning(f"Unknown diagram type '{dtype}' → block_flow")
        renderer = _render_block_flow
    try:
        code = renderer(slide_idx, params, duration)
        logger.info(f"  Template '{dtype}' generated for slide {slide_idx+1}")
        return code
    except Exception as e:
        logger.error(f"  Template '{dtype}' failed: {e} → block_flow fallback")
        try:
            return _render_block_flow(slide_idx, params, duration)
        except Exception as e2:
            logger.error(f"  block_flow fallback failed: {e2}")
            return None


def get_scene_code(scene_idx: int, params: dict, duration: int) -> Optional[str]:
    """Alias for get_diagram_code — used by the Topic Video pipeline."""
    scene_type = params.get("type", "bullet_list")
    params_copy = dict(params)
    params_copy["type"] = scene_type
    return get_diagram_code(scene_idx, params_copy, duration)
