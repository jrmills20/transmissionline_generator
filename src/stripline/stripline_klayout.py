"""
Dual Stripline (Attacker + Victim) Layout Generator for KLayout
Symmetric: pads on both ends, taper on both sides, vias at both ends.

Structure (x axis):
  [left pad 0..3] [left taper 3..5] [TL 5..8] [right taper 8..10] [right pad 10..13]

3 equal traces: attacker | GND | victim
Pads on both ends. GND_BOT / GND_TOP only drawn in taper+TL so pads show.

Layer map:
  1/0 = GND_BOT   bottom ground plane (taper + TL sections)
  2/0 = GND_TOP   top ground plane    (taper + TL sections)
  3/0 = SL        embedded traces (left taper + TL + right taper)
  4/0 = PAD       surface signal pads (both ends, all 3 traces)
  1/1 = VIA       outer via walls + via markers at x=3 and x=10
"""

import pya

# ===========================================================================
# PARAMETERS
# ===========================================================================
LAYER_GND_BOT = (1, 0)
LAYER_GND_TOP = (2, 0)
LAYER_SL      = (3, 0)
LAYER_PAD     = (4, 0)
LAYER_VIA     = (1, 1)
LAYER_LABEL   = (10, 0)

W_PAD      = 0.293
G_PAD      = 0.204
W_SL       = 0.7
G_SL       = 0.7
L_PAD      = 3.0
L_TAPER    = 2.0
L_TL       = 3.0
VIA_W      = 0.7
GND_MARGIN = VIA_W + 0.7   # 1.4mm — 0.7mm gap from via wall to first trace

# ===========================================================================
# DERIVED
# ===========================================================================
TOTAL_LENGTH = 2*L_PAD + 2*L_TAPER + L_TL   # 13.0 mm

x0 = 0.0
x1 = L_PAD                                   # 3.0  left via / left taper start
x2 = L_PAD + L_TAPER                         # 5.0  TL start
x3 = L_PAD + L_TAPER + L_TL                  # 8.0  TL end
x4 = L_PAD + L_TAPER + L_TL + L_TAPER        # 10.0 right via / right taper end
x5 = TOTAL_LENGTH                             # 13.0 right pad end

VIA_HALF = W_PAD / 2

# Y — pad end
yp_attk_bot = GND_MARGIN;               yp_attk_top = GND_MARGIN + W_PAD
yp_gnd_bot  = yp_attk_top + G_PAD;     yp_gnd_top  = yp_gnd_bot  + W_PAD
yp_vict_bot = yp_gnd_top  + G_PAD;     yp_vict_top = yp_vict_bot + W_PAD
yp_total    = yp_vict_top + GND_MARGIN

# Y — TL end
yt_attk_bot = GND_MARGIN;               yt_attk_top = GND_MARGIN + W_SL
yt_gnd_bot  = yt_attk_top + G_SL;      yt_gnd_top  = yt_gnd_bot  + W_SL
yt_vict_bot = yt_gnd_top  + G_SL;      yt_vict_top = yt_vict_bot + W_SL
yt_total    = yt_vict_top + GND_MARGIN

TOTAL_HEIGHT = yt_total

via_top_pad_bot = yp_total - VIA_W
via_top_tl_bot  = yt_total - VIA_W

cy_attk = (yp_attk_bot + yp_attk_top) / 2
cy_vict = (yp_vict_bot + yp_vict_top) / 2

# ===========================================================================
# HELPERS
# ===========================================================================
def to_dbu(mm, u):
    return int(round(mm / u))

def box(x1, y1, x2, y2, u):
    return pya.Box(to_dbu(x1,u), to_dbu(y1,u), to_dbu(x2,u), to_dbu(y2,u))

def trapezoid(x1, y_bot1, y_top1, x2, y_bot2, y_top2, u):
    pts = [pya.Point(to_dbu(x1,u), to_dbu(y_bot1,u)),
           pya.Point(to_dbu(x2,u), to_dbu(y_bot2,u)),
           pya.Point(to_dbu(x2,u), to_dbu(y_top2,u)),
           pya.Point(to_dbu(x1,u), to_dbu(y_top1,u))]
    return pya.Polygon(pts)

def label(text, x, y, u, shapes, layer):
    shapes(layer).insert(pya.Text(text, to_dbu(x,u), to_dbu(y,u)))

# ===========================================================================
# MAIN
# ===========================================================================
def run():
    app = pya.Application.instance()
    mw  = app.main_window()
    cv  = mw.current_view().active_cellview()
    if cv is None or not cv.is_valid():
        raise RuntimeError("No layout open.")

    layout = cv.layout()
    u = layout.dbu
    print(f"TOTAL_LENGTH = {TOTAL_LENGTH}mm  x0={x0} x1={x1} x2={x2} x3={x3} x4={x4} x5={x5}")
    print(f"Pad  Y: attk=[{yp_attk_bot:.3f},{yp_attk_top:.3f}] gnd=[{yp_gnd_bot:.3f},{yp_gnd_top:.3f}] vict=[{yp_vict_bot:.3f},{yp_vict_top:.3f}]")
    print(f"TL   Y: attk=[{yt_attk_bot:.3f},{yt_attk_top:.3f}] gnd=[{yt_gnd_bot:.3f},{yt_gnd_top:.3f}] vict=[{yt_vict_bot:.3f},{yt_vict_top:.3f}]")

    if layout.cells() > 0:
        cell = layout.cell(layout.top_cells()[0].cell_index())
        cell.clear()
    else:
        cell = layout.create_cell("DUAL_STRIPLINE")
        cv.cell_name = cell.name

    lgnd_bot = layout.layer(*LAYER_GND_BOT)
    lgnd_top = layout.layer(*LAYER_GND_TOP)
    lsl      = layout.layer(*LAYER_SL)
    lpad     = layout.layer(*LAYER_PAD)
    lvia     = layout.layer(*LAYER_VIA)
    llbl     = layout.layer(*LAYER_LABEL)

    # ── GND_BOT + GND_TOP: taper+TL sections only (pad sections left blank) ─
    for lyr in [lgnd_bot, lgnd_top]:
        cell.shapes(lyr).insert(trapezoid(x1, 0, yp_total, x2, 0, yt_total, u))  # left taper
        cell.shapes(lyr).insert(box(x2, 0, x3, yt_total, u))                       # TL
        cell.shapes(lyr).insert(trapezoid(x3, 0, yt_total, x4, 0, yp_total, u))  # right taper

    # ── LAYER_PAD: all 3 traces, both ends ───────────────────────────────
    for yb, yt in [(yp_attk_bot, yp_attk_top),
                   (yp_gnd_bot,  yp_gnd_top),
                   (yp_vict_bot, yp_vict_top)]:
        cell.shapes(lpad).insert(box(x0, yb, x1, yt, u))   # left pad
        cell.shapes(lpad).insert(box(x4, yb, x5, yt, u))   # right pad

    # ── LAYER_SL: left taper + TL + right taper (all 3 traces) ──────────
    for (yb_p, yt_p, yb_tl, yt_tl) in [
            (yp_attk_bot, yp_attk_top, yt_attk_bot, yt_attk_top),
            (yp_gnd_bot,  yp_gnd_top,  yt_gnd_bot,  yt_gnd_top),
            (yp_vict_bot, yp_vict_top, yt_vict_bot, yt_vict_top)]:
        cell.shapes(lsl).insert(trapezoid(x1, yb_p, yt_p, x2, yb_tl, yt_tl, u))  # left taper
        cell.shapes(lsl).insert(box(x2, yb_tl, x3, yt_tl, u))                      # TL
        cell.shapes(lsl).insert(trapezoid(x3, yb_tl, yt_tl, x4, yb_p, yt_p, u))  # right taper

    # ── LAYER_VIA: transition via markers — left (x≈x1) and right (x≈x4) ─
    for xv in [x1, x4]:
        for yb, yt in [(yp_attk_bot, yp_attk_top),
                       (yp_gnd_bot,  yp_gnd_top),
                       (yp_vict_bot, yp_vict_top)]:
            cell.shapes(lvia).insert(box(xv-VIA_HALF, yb, xv+VIA_HALF, yt, u))

    # ── LAYER_VIA: outer via wall — bottom (constant full length) ─────────
    cell.shapes(lvia).insert(box(x0, 0, x5, VIA_W, u))

    # ── LAYER_VIA: outer via wall — top (symmetric taper) ─────────────────
    cell.shapes(lvia).insert(box(x0, via_top_pad_bot, x1, yp_total, u))           # left pad
    cell.shapes(lvia).insert(trapezoid(x1, via_top_pad_bot, yp_total,
                                        x2, via_top_tl_bot,  yt_total, u))         # left taper
    cell.shapes(lvia).insert(box(x2, via_top_tl_bot, x3, yt_total, u))            # TL
    cell.shapes(lvia).insert(trapezoid(x3, via_top_tl_bot, yt_total,
                                        x4, via_top_pad_bot, yp_total, u))         # right taper
    cell.shapes(lvia).insert(box(x4, via_top_pad_bot, x5, yp_total, u))           # right pad

    # ── Port labels ───────────────────────────────────────────────────────
    label("p1", x0, cy_attk, u, cell.shapes, llbl)
    label("p2", x5, cy_attk, u, cell.shapes, llbl)
    label("p3", x0, cy_vict, u, cell.shapes, llbl)
    label("p4", x5, cy_vict, u, cell.shapes, llbl)

    mw.current_view().zoom_fit()
    print("\n" + "="*55)
    print(f"  SUCCESS  {TOTAL_LENGTH}mm x {yt_total:.3f}mm")
    print(f"  pad({L_PAD}) + taper({L_TAPER}) + TL({L_TL}) + taper({L_TAPER}) + pad({L_PAD})")
    print(f"  Pad: W={W_PAD} G={G_PAD}  |  TL: W={W_SL} G={G_SL}")
    print(f"  Via wall={VIA_W}mm  gap=0.7mm  GND_MARGIN={GND_MARGIN}mm")
    print("="*55)

run()
