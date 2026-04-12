"""
SIW Leaky Wave Waveguide Layout Generator (No Slots) for KLayout
=================================================================
HOW TO RUN:
  1. Open KLayout -> File -> New Layout (accept defaults)
  2. Macros -> Macro Editor (F5)
  3. Paste this script, press Run

STRUCTURE (left to right):
  [microstrip feed] -> [taper] -> [SIW body, solid top] -> [taper] -> [microstrip feed]

LAYER STRUCTURE:
  m1   = solid ground plane (full rectangle, bottom copper)
  m2   = top conductor:
           - solid fill across full SIW width (no slots)
           - taper polygons at each end
           - narrow microstrip feed at each end
  via1 = two rows of circles forming the SIW sidewalls
"""

import pya
import math

# ===========================================================================
# PARAMETERS
# ===========================================================================

LAYER_M1   = (1, 0)
LAYER_M2   = (2, 0)
LAYER_VIA1 = (1, 1)

VIA_DIAMETER = 0.3    # mm
VIA_PITCH    = 0.6    # mm
VIA_SEGMENTS = 64

SIW_WIDTH   = 28.0    # mm  center-to-center between via rows
SIW_LENGTH  = 60.0    # mm  length of SIW body

TAPER_LENGTH = 10.0   # mm  length of each taper transition

FEED_WIDTH  = 1.5     # mm  microstrip feed line width (~50 ohm)
FEED_LENGTH = 10.0    # mm  feed stub length at each end

GND_MARGIN  = 3.0     # mm  m1 margin outside via rows

# ===========================================================================
# DERIVED
# ===========================================================================
VIA_RADIUS = VIA_DIAMETER / 2.0

Y_CENTER  = 0.0
Y_TOP_ROW = Y_CENTER + SIW_WIDTH / 2.0
Y_BOT_ROW = Y_CENTER - SIW_WIDTH / 2.0

X_FEED_END   = FEED_LENGTH
X_TAPER_END  = FEED_LENGTH + TAPER_LENGTH
X_SIW_END    = FEED_LENGTH + TAPER_LENGTH + SIW_LENGTH
X_RTAPER_END = FEED_LENGTH + TAPER_LENGTH + SIW_LENGTH + TAPER_LENGTH
X_TOTAL      = FEED_LENGTH + TAPER_LENGTH + SIW_LENGTH + TAPER_LENGTH + FEED_LENGTH

X_VIA_START = X_TAPER_END
X_VIA_END   = X_SIW_END

M1_Y_BOT = Y_BOT_ROW - GND_MARGIN
M1_Y_TOP = Y_TOP_ROW + GND_MARGIN

# ===========================================================================
# HELPERS
# ===========================================================================
def to_dbu(mm, u):
    return int(round(mm / u))

def box(x1, y1, x2, y2, u):
    return pya.Box(to_dbu(x1,u), to_dbu(y1,u),
                   to_dbu(x2,u), to_dbu(y2,u))

def poly(pts_mm, u):
    return pya.Polygon([pya.Point(to_dbu(x,u), to_dbu(y,u)) for x,y in pts_mm])

def circle(cx, cy, r, n, u):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        pts.append(pya.Point(to_dbu(cx + r*math.cos(a), u),
                             to_dbu(cy + r*math.sin(a), u)))
    return pya.Polygon(pts)

# ===========================================================================
# MAIN
# ===========================================================================
def run():
    app = pya.Application.instance()
    mw  = app.main_window()

    cv = mw.current_view().active_cellview()
    if cv is None or not cv.is_valid():
        raise RuntimeError("No layout open — go to File -> New Layout first.")

    layout = cv.layout()
    u = layout.dbu
    print(f"DBU = {u} mm")

    if layout.cells() > 0:
        cell = layout.cell(layout.top_cells()[0].cell_index())
        cell.clear()
        print(f"Cleared cell: {cell.name}")
    else:
        cell = layout.create_cell("SIW_SOLID")
        cv.cell_name = cell.name
        print(f"Created cell: {cell.name}")

    lm1  = layout.layer(LAYER_M1[0],   LAYER_M1[1])
    lm2  = layout.layer(LAYER_M2[0],   LAYER_M2[1])
    lvia = layout.layer(LAYER_VIA1[0], LAYER_VIA1[1])
    print(f"Layers — m1:{lm1}  m2:{lm2}  via1:{lvia}")

    n = 0

    # -----------------------------------------------------------------------
    # 1. M1 — solid ground plane
    # -----------------------------------------------------------------------
    cell.shapes(lm1).insert(box(0, M1_Y_BOT, X_TOTAL, M1_Y_TOP, u))
    n += 1
    print(f"[m1] Ground plane: {X_TOTAL:.2f} x {M1_Y_TOP - M1_Y_BOT:.2f} mm")

    # -----------------------------------------------------------------------
    # 2. M2 — left microstrip feed
    # -----------------------------------------------------------------------
    cell.shapes(lm2).insert(box(0, -FEED_WIDTH/2, X_FEED_END, FEED_WIDTH/2, u))
    n += 1
    print(f"[m2] Left feed: x=0 to {X_FEED_END:.2f}")

    # -----------------------------------------------------------------------
    # 3. M2 — left taper
    # -----------------------------------------------------------------------
    cell.shapes(lm2).insert(poly([
        (X_FEED_END,  -FEED_WIDTH/2),
        (X_FEED_END,   FEED_WIDTH/2),
        (X_TAPER_END,  Y_TOP_ROW),
        (X_TAPER_END,  Y_BOT_ROW),
    ], u))
    n += 1
    print(f"[m2] Left taper: x={X_FEED_END:.2f} to {X_TAPER_END:.2f}")

    # -----------------------------------------------------------------------
    # 4. M2 — SIW body solid fill (no slots)
    # -----------------------------------------------------------------------
    cell.shapes(lm2).insert(box(X_VIA_START, Y_BOT_ROW, X_VIA_END, Y_TOP_ROW, u))
    n += 1
    print(f"[m2] SIW body solid: x={X_VIA_START:.2f} to {X_VIA_END:.2f}, "
          f"y={Y_BOT_ROW:.2f} to {Y_TOP_ROW:.2f}")

    # -----------------------------------------------------------------------
    # 5. M2 — right taper
    # -----------------------------------------------------------------------
    cell.shapes(lm2).insert(poly([
        (X_SIW_END,    Y_BOT_ROW),
        (X_SIW_END,    Y_TOP_ROW),
        (X_RTAPER_END, FEED_WIDTH/2),
        (X_RTAPER_END, -FEED_WIDTH/2),
    ], u))
    n += 1
    print(f"[m2] Right taper: x={X_SIW_END:.2f} to {X_RTAPER_END:.2f}")

    # -----------------------------------------------------------------------
    # 6. M2 — right microstrip feed
    # -----------------------------------------------------------------------
    cell.shapes(lm2).insert(box(X_RTAPER_END, -FEED_WIDTH/2, X_TOTAL, FEED_WIDTH/2, u))
    n += 1
    print(f"[m2] Right feed: x={X_RTAPER_END:.2f} to {X_TOTAL:.2f}")

    # -----------------------------------------------------------------------
    # 7. VIA1 — two rows of circles
    # -----------------------------------------------------------------------
    via_count = 0
    x = X_VIA_START
    while x <= X_VIA_END + 1e-6:
        cell.shapes(lvia).insert(circle(x, Y_TOP_ROW, VIA_RADIUS, VIA_SEGMENTS, u))
        cell.shapes(lvia).insert(circle(x, Y_BOT_ROW, VIA_RADIUS, VIA_SEGMENTS, u))
        x += VIA_PITCH
        via_count += 2
    n += via_count
    print(f"[via1] {via_count} circles ({via_count//2} per row)")

    mw.current_view().zoom_fit()

    print("\n" + "=" * 55)
    print("  SUCCESS — SIW Solid (no slots)")
    print("=" * 55)
    print(f"  Total length  : {X_TOTAL:.1f} mm")
    print(f"  SIW width     : {SIW_WIDTH:.1f} mm")
    print(f"  Feed width    : {FEED_WIDTH:.1f} mm")
    print(f"  Taper length  : {TAPER_LENGTH:.1f} mm")
    print(f"  Via pitch/d   : {VIA_PITCH}/{VIA_DIAMETER} mm")
    print(f"  Total shapes  : {n}")
    print("=" * 55)

run()
