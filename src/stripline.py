"""
Stripline Transmission Line Layout Generator for KLayout
=========================================================
HOW TO RUN:
  1. Open KLayout -> File -> New Layout (accept defaults)
  2. Macros -> Macro Editor (F5)
  3. Paste this script, press Run

WHAT IS STRIPLINE:
  Unlike microstrip (trace on top, one ground below), stripline buries
  the signal trace inside the dielectric, sandwiched between two ground
  planes above and below. This gives better shielding and no radiation.

  In your 4-layer stackup:
    m1  (layer 1/0) = bottom ground plane    <- you already have this
    m2  (layer 2/0) = top ground plane       <- you already have this
    sig (layer 3/0) = signal trace buried    <- NEW layer (Int1 or Int2)

  In KLayout 2D top-down view, all three layers are overlaid.
  The sig layer sits visually between m1 and m2 in the layer panel.

STRUCTURE:
  Both m1 and m2 are solid ground plane rectangles (same footprint).
  The sig layer is a narrow strip running down the center — this is
  the buried transmission line.

STRIPLINE WIDTH NOTE:
  Stripline characteristic impedance depends on trace width, dielectric
  thickness, and er. For 50 ohm stripline the trace is narrower than
  microstrip because it has ground on both sides.
  Use a stripline calculator with your stackup to get the exact width.
  For Core-039 (1.065mm, er=4.6) with ground planes on each side:
    Z0 ~ 50 ohm at roughly w ~ 0.8-1.2mm (run calculator to verify)
"""

import pya
import math

# ===========================================================================
# PARAMETERS
# ===========================================================================

LAYER_M1  = (1, 0)   # bottom ground plane
LAYER_M2  = (2, 0)   # top ground plane
LAYER_SIG = (3, 0)   # buried signal trace (Int1 or Int2 in your stackup)

# Signal trace
TRACE_WIDTH  = 1.0    # mm  adjust for 50 ohm — run stripline calculator
TRACE_LENGTH = 60.0   # mm  total length of the transmission line

# Ground plane margin around the trace on each side
GND_MARGIN = 5.0      # mm  how much wider the ground planes are vs trace

# Feed pads at each end (wider pad for port attachment)
ADD_PADS   = True
PAD_WIDTH  = 2.0      # mm  wider pad at port ends
PAD_LENGTH = 2.0      # mm  length of pad

# ===========================================================================
# DERIVED
# ===========================================================================
GND_WIDTH  = TRACE_WIDTH + 2 * GND_MARGIN   # total ground plane width
TOTAL_LENGTH = TRACE_LENGTH

Y_CENTER   = 0.0
GND_Y_BOT  = Y_CENTER - GND_WIDTH / 2.0
GND_Y_TOP  = Y_CENTER + GND_WIDTH / 2.0
SIG_Y_BOT  = Y_CENTER - TRACE_WIDTH / 2.0
SIG_Y_TOP  = Y_CENTER + TRACE_WIDTH / 2.0

# ===========================================================================
# HELPERS
# ===========================================================================
def to_dbu(mm, u):
    return int(round(mm / u))

def box(x1, y1, x2, y2, u):
    return pya.Box(to_dbu(x1,u), to_dbu(y1,u),
                   to_dbu(x2,u), to_dbu(y2,u))

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
        cell = layout.create_cell("STRIPLINE_TL")
        cv.cell_name = cell.name
        print(f"Created cell: {cell.name}")

    lm1  = layout.layer(LAYER_M1[0],  LAYER_M1[1])
    lm2  = layout.layer(LAYER_M2[0],  LAYER_M2[1])
    lsig = layout.layer(LAYER_SIG[0], LAYER_SIG[1])
    print(f"Layers — m1:{lm1}  m2:{lm2}  sig:{lsig}")

    n = 0

    # -----------------------------------------------------------------------
    # 1. M1 — bottom ground plane (solid rectangle)
    # -----------------------------------------------------------------------
    cell.shapes(lm1).insert(box(0, GND_Y_BOT, TOTAL_LENGTH, GND_Y_TOP, u))
    n += 1
    print(f"[m1] Bottom ground plane: {TOTAL_LENGTH:.2f} x {GND_WIDTH:.2f} mm")

    # -----------------------------------------------------------------------
    # 2. M2 — top ground plane (same footprint as m1)
    # -----------------------------------------------------------------------
    cell.shapes(lm2).insert(box(0, GND_Y_BOT, TOTAL_LENGTH, GND_Y_TOP, u))
    n += 1
    print(f"[m2] Top ground plane: {TOTAL_LENGTH:.2f} x {GND_WIDTH:.2f} mm")

    # -----------------------------------------------------------------------
    # 3. SIG — buried signal trace (centered between ground planes)
    # -----------------------------------------------------------------------
    cell.shapes(lsig).insert(box(0, SIG_Y_BOT, TOTAL_LENGTH, SIG_Y_TOP, u))
    n += 1
    print(f"[sig] Signal trace: {TOTAL_LENGTH:.2f} x {TRACE_WIDTH:.2f} mm")
    print(f"      y={SIG_Y_BOT:.3f} to {SIG_Y_TOP:.3f} (centered at y=0)")

    # -----------------------------------------------------------------------
    # 4. Optional port pads on SIG layer (wider rectangle at each end)
    #    Makes it easier to attach simulation ports
    # -----------------------------------------------------------------------
    if ADD_PADS:
        # Left pad
        cell.shapes(lsig).insert(box(
            0, Y_CENTER - PAD_WIDTH/2,
            PAD_LENGTH, Y_CENTER + PAD_WIDTH/2, u))
        # Right pad
        cell.shapes(lsig).insert(box(
            TOTAL_LENGTH - PAD_LENGTH, Y_CENTER - PAD_WIDTH/2,
            TOTAL_LENGTH, Y_CENTER + PAD_WIDTH/2, u))
        n += 2
        print(f"[sig] Port pads: {PAD_LENGTH:.2f} x {PAD_WIDTH:.2f} mm at each end")

    mw.current_view().zoom_fit()

    print("\n" + "=" * 55)
    print("  SUCCESS — Stripline Transmission Line")
    print("=" * 55)
    print(f"  Trace width   : {TRACE_WIDTH:.2f} mm")
    print(f"  Trace length  : {TRACE_LENGTH:.2f} mm")
    print(f"  GND width     : {GND_WIDTH:.2f} mm")
    print(f"  GND margin    : {GND_MARGIN:.2f} mm each side")
    print(f"  Total shapes  : {n}")
    print("=" * 55)
    print("  LAYER SUMMARY:")
    print(f"  m1  ({LAYER_M1[0]}/{LAYER_M1[1]}) = bottom ground plane")
    print(f"  m2  ({LAYER_M2[0]}/{LAYER_M2[1]}) = top ground plane")
    print(f"  sig ({LAYER_SIG[0]}/{LAYER_SIG[1]}) = buried signal trace")
    print("=" * 55)
    print("  NOTE: In KLayout all 3 layers render as overlapping 2D shapes.")
    print("  The stackup definition encodes the vertical order.")
    print("  sig layer should map to Int1 or Int2 in your layer setup.")
    print("=" * 55)

run()
