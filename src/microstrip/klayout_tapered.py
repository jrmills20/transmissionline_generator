"""
Dual Tapered CPW (Attacker + Victim) Layout Generator for KLayout
3 equal-width traces: attacker signal | GND trace | victim signal
All three traces share the same width (W_WIDE/W_NARROW) and equal gaps.

Dimensions from PCB image annotations:
  Wide   section : signal/gnd = 0.293 mm, gap = 0.204 mm
  Narrow section : signal/gnd = 0.206 mm, gap = 0.140 mm
"""

import pya
import math

# ===========================================================================
# PARAMETERS
# ===========================================================================

LAYER_M1    = (1, 0)
LAYER_M2    = (2, 0)
LAYER_VIA1  = (1, 1)
LAYER_LABEL = (10, 0)

# All three traces share the same width at each section
W_WIDE      = 0.293   # mm — wide-section trace width (signal AND gnd trace)
W_NARROW    = 0.206   # mm — narrow-section trace width (signal AND gnd trace)

# Equal gap between every adjacent trace pair
G_WIDE      = 0.204   # mm — gap at wide section
G_NARROW    = 0.140   # mm — gap at narrow section

# Section lengths
L_WIDE      = 3.0     # mm
L_TAPER     = 2.0     # mm
L_NARROW    = 3.0     # mm

# Outer ground copper margin beyond the outer trace
GND_MARGIN  = 1.0     # mm

# Via plane strip width (solid fill on outer edges)
VIA_PLANE_WIDTH = 0.3  # mm

# ===========================================================================
# DERIVED
# ===========================================================================
TOTAL_LENGTH = L_WIDE + L_TAPER + L_NARROW   # 8.0 mm

# Wide section Y layout — all three traces same width, equal gaps
# Structure (bottom to top):
#   outer gnd fill | gap | attacker | gap | GND trace | gap | victim | gap | outer gnd fill
yw0 = 0.0
yw1 = GND_MARGIN                             # 1.000 — bottom outer fill top / attacker gap bot
yw2 = yw1 + G_WIDE                           # 1.204 — attacker bottom
yw3 = yw2 + W_WIDE                           # 1.497 — attacker top
yw4 = yw3 + G_WIDE                           # 1.701 — GND trace bottom
yw5 = yw4 + W_WIDE                           # 1.994 — GND trace top   ← same width as signal
yw6 = yw5 + G_WIDE                           # 2.198 — victim bottom
yw7 = yw6 + W_WIDE                           # 2.491 — victim top
yw8 = yw7 + G_WIDE                           # 2.695 — top outer fill bot
yw9 = yw8 + GND_MARGIN                       # 3.695 — top outer fill top

# Narrow section Y layout
yn0 = 0.0
yn1 = GND_MARGIN                             # 1.000
yn2 = yn1 + G_NARROW                         # 1.140 — attacker bottom
yn3 = yn2 + W_NARROW                         # 1.346 — attacker top
yn4 = yn3 + G_NARROW                         # 1.486 — GND trace bottom
yn5 = yn4 + W_NARROW                         # 1.692 — GND trace top   ← same width as signal
yn6 = yn5 + G_NARROW                         # 1.832 — victim bottom
yn7 = yn6 + W_NARROW                         # 2.038 — victim top
yn8 = yn7 + G_NARROW                         # 2.178 — top outer fill bot
yn9 = yn8 + GND_MARGIN                       # 3.178 — top outer fill top

TOTAL_HEIGHT = yw9   # 3.695 mm — bounding box height (wide end)

x0 = 0.0
x1 = L_WIDE                                  # 3.0
x2 = L_WIDE + L_TAPER                        # 5.0
x3 = TOTAL_LENGTH                            # 8.0

# Via plane Y — outer edges only, anchored to narrow end so always inside copper
via_bot_y0 = yw0
via_bot_y1 = yw0 + VIA_PLANE_WIDTH           # 0.300
via_top_y0 = yn9 - VIA_PLANE_WIDTH           # 2.878
via_top_y1 = yn9                             # 3.178

# Port label centres
cy_attk_w = (yw2 + yw3) / 2                  # attacker centre — wide end
cy_attk_n = (yn2 + yn3) / 2                  # attacker centre — narrow end
cy_vict_w = (yw6 + yw7) / 2                  # victim centre — wide end
cy_vict_n = (yn6 + yn7) / 2                  # victim centre — narrow end

# ===========================================================================
# HELPERS
# ===========================================================================
def to_dbu(mm, u):
    return int(round(mm / u))

def box(x1, y1, x2, y2, u):
    return pya.Box(to_dbu(x1, u), to_dbu(y1, u),
                   to_dbu(x2, u), to_dbu(y2, u))

def trapezoid(x1, y_bot1, y_top1, x2, y_bot2, y_top2, u):
    pts = [
        pya.Point(to_dbu(x1, u), to_dbu(y_bot1, u)),
        pya.Point(to_dbu(x2, u), to_dbu(y_bot2, u)),
        pya.Point(to_dbu(x2, u), to_dbu(y_top2, u)),
        pya.Point(to_dbu(x1, u), to_dbu(y_top1, u)),
    ]
    return pya.Polygon(pts)

def label(text, x, y, u, shapes, layer):
    t = pya.Text(text, to_dbu(x, u), to_dbu(y, u))
    shapes(layer).insert(t)

# ===========================================================================
# MAIN
# ===========================================================================
def run():
    app = pya.Application.instance()
    mw  = app.main_window()

    cv = mw.current_view().active_cellview()
    if cv is None or not cv.is_valid():
        raise RuntimeError("No layout open.")

    layout = cv.layout()
    u = layout.dbu
    print(f"DBU          = {u} mm")
    print(f"TOTAL_LENGTH = {TOTAL_LENGTH} mm")
    print(f"TOTAL_HEIGHT = {TOTAL_HEIGHT:.4f} mm  (wide end)")
    print(f"Attacker : wide=[{yw2:.4f},{yw3:.4f}]  narrow=[{yn2:.4f},{yn3:.4f}]  W={W_WIDE}/{W_NARROW}")
    print(f"GND trace: wide=[{yw4:.4f},{yw5:.4f}]  narrow=[{yn4:.4f},{yn5:.4f}]  W={W_WIDE}/{W_NARROW}")
    print(f"Victim   : wide=[{yw6:.4f},{yw7:.4f}]  narrow=[{yn6:.4f},{yn7:.4f}]  W={W_WIDE}/{W_NARROW}")

    if layout.cells() > 0:
        cell = layout.cell(layout.top_cells()[0].cell_index())
        cell.clear()
        print(f"Cleared cell: {cell.name}")
    else:
        cell = layout.create_cell("DUAL_TAPERED_CPW")
        cv.cell_name = cell.name

    lm1  = layout.layer(*LAYER_M1)
    lm2  = layout.layer(*LAYER_M2)
    lvia = layout.layer(*LAYER_VIA1)
    llbl = layout.layer(*LAYER_LABEL)

    n = 0

    # ── M1: Full ground plane ─────────────────────────────────────
    cell.shapes(lm1).insert(box(x0, yw0, x3, TOTAL_HEIGHT, u))
    n += 1

    # ── M2: Bottom outer ground fill (constant, no taper) ─────────
    cell.shapes(lm2).insert(box(x0, yw0, x3, yw1, u))
    n += 1

    # ── M2: Attacker signal trace (wide + taper + narrow) ─────────
    cell.shapes(lm2).insert(box(x0, yw2, x1, yw3, u))
    cell.shapes(lm2).insert(trapezoid(x1, yw2, yw3, x2, yn2, yn3, u))
    cell.shapes(lm2).insert(box(x2, yn2, x3, yn3, u))
    n += 3

    # ── M2: GND trace — same width as signal (wide + taper + narrow)
    cell.shapes(lm2).insert(box(x0, yw4, x1, yw5, u))
    cell.shapes(lm2).insert(trapezoid(x1, yw4, yw5, x2, yn4, yn5, u))
    cell.shapes(lm2).insert(box(x2, yn4, x3, yn5, u))
    n += 3

    # ── M2: Victim signal trace (wide + taper + narrow) ───────────
    cell.shapes(lm2).insert(box(x0, yw6, x1, yw7, u))
    cell.shapes(lm2).insert(trapezoid(x1, yw6, yw7, x2, yn6, yn7, u))
    cell.shapes(lm2).insert(box(x2, yn6, x3, yn7, u))
    n += 3

    # ── M2: Top outer ground fill (wide + taper + narrow) ─────────
    cell.shapes(lm2).insert(box(x0, yw8, x1, yw9, u))
    cell.shapes(lm2).insert(trapezoid(x1, yw8, yw9, x2, yn8, yn9, u))
    cell.shapes(lm2).insert(box(x2, yn8, x3, yn9, u))
    n += 3

    # ── VIA1: Bottom via plane (solid fill, outer edge) ───────────
    cell.shapes(lvia).insert(box(x0, via_bot_y0, x3, via_bot_y1, u))
    n += 1

    # ── VIA1: Top via plane (solid fill, outer edge) ──────────────
    cell.shapes(lvia).insert(box(x0, via_top_y0, x1, via_top_y1, u))
    cell.shapes(lvia).insert(trapezoid(x1, via_top_y0, via_top_y1,
                                        x2, yn9 - VIA_PLANE_WIDTH, yn9, u))
    cell.shapes(lvia).insert(box(x2, yn9 - VIA_PLANE_WIDTH, x3, yn9, u))
    n += 3

    # ── Port labels (layer 10/0) ───────────────────────────────────
    label("p1", x0, cy_attk_w, u, cell.shapes, llbl)   # attacker left
    label("p2", x3, cy_attk_n, u, cell.shapes, llbl)   # attacker right
    label("p3", x0, cy_vict_w, u, cell.shapes, llbl)   # victim left
    label("p4", x3, cy_vict_n, u, cell.shapes, llbl)   # victim right
    n += 4

    print(f"Port labels: p1,p2 (attacker), p3,p4 (victim)")

    mw.current_view().zoom_fit()

    print("\n" + "=" * 55)
    print("  SUCCESS")
    print(f"  Layout      : {TOTAL_LENGTH:.1f} x {TOTAL_HEIGHT:.4f} mm")
    print(f"  Wide  sec   : W={W_WIDE} mm  G={G_WIDE} mm  L={L_WIDE} mm")
    print(f"  Taper       : {L_TAPER} mm long")
    print(f"  Narrow sec  : W={W_NARROW} mm  G={G_NARROW} mm  L={L_NARROW} mm")
    print(f"  GND trace   : same width as signal traces")
    print(f"  Via plane   : {VIA_PLANE_WIDTH} mm solid fill outer edges")
    print(f"  Total shapes: {n}")
    print("=" * 55)
    print("  Port labels on layer 10/0:")
    print("  p1 = attacker left,  p2 = attacker right")
    print("  p3 = victim left,    p4 = victim right")
    print("=" * 55)

run()
