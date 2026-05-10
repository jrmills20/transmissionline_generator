# -*- coding: utf-8 -*-
# Dual Tapered CPW (Attacker + Victim) Builder for HFSS Terminal Network
# 3 equal-width traces: attacker signal | GND trace | victim signal
# GND trace spans full stackup (M1_Z -> TOP_Z) like a via plane
# Matches dual_tapered_cpw.py KLayout script exactly
# Run via Tools -> Run Script in a blank HFSSDesign (Terminal Network)

# ===========================================================================
# STACKUP (mm, bottom to top)
# ===========================================================================
M1_Z     = 0.0;    M1_THK   = 0.035
PRE1_Z   = 0.035;  PRE1_THK = 0.2104
INT1_Z   = 0.2454; INT1_THK = 0.0152
CORE_Z   = 0.2606; CORE_THK = 1.065
INT2_Z   = 1.3256; INT2_THK = 0.0152
PRE2_Z   = 1.3408; PRE2_THK = 0.2104
M2_Z     = 1.5512; M2_THK   = 0.035
TOP_Z    = 1.5862

# ===========================================================================
# CPW DIMENSIONS (mm) — must match dual_tapered_cpw.py exactly
# All three traces (attacker, GND, victim) share the same width
# ===========================================================================
W_WIDE      = 0.293   # wide-section trace width — signal AND gnd trace
W_NARROW    = 0.206   # narrow-section trace width — signal AND gnd trace
G_WIDE      = 0.204   # gap between every adjacent trace pair — wide section
G_NARROW    = 0.140   # gap between every adjacent trace pair — narrow section
L_WIDE      = 3.0
L_TAPER     = 2.0
L_NARROW    = 3.0
GND_MARGIN  = 1.0
VIA_PLANE_W = 0.3

AIR_PADDING = 2.0

# ===========================================================================
# DERIVED — mirror of KLayout DERIVED section
# ===========================================================================
TOTAL_LENGTH = L_WIDE + L_TAPER + L_NARROW   # 8.0 mm

# Wide section Y layout
yw0 = 0.0
yw1 = GND_MARGIN                             # 1.000
yw2 = yw1 + G_WIDE                           # 1.204 — attacker bottom
yw3 = yw2 + W_WIDE                           # 1.497 — attacker top
yw4 = yw3 + G_WIDE                           # 1.701 — GND trace bottom
yw5 = yw4 + W_WIDE                           # 1.994 — GND trace top
yw6 = yw5 + G_WIDE                           # 2.198 — victim bottom
yw7 = yw6 + W_WIDE                           # 2.491 — victim top
yw8 = yw7 + G_WIDE                           # 2.695 — top outer fill bottom
yw9 = yw8 + GND_MARGIN                       # 3.695 — top outer fill top

# Narrow section Y layout
yn0 = 0.0
yn1 = GND_MARGIN                             # 1.000
yn2 = yn1 + G_NARROW                         # 1.140 — attacker bottom
yn3 = yn2 + W_NARROW                         # 1.346 — attacker top
yn4 = yn3 + G_NARROW                         # 1.486 — GND trace bottom
yn5 = yn4 + W_NARROW                         # 1.692 — GND trace top
yn6 = yn5 + G_NARROW                         # 1.832 — victim bottom
yn7 = yn6 + W_NARROW                         # 2.038 — victim top
yn8 = yn7 + G_NARROW                         # 2.178 — top outer fill bottom
yn9 = yn8 + GND_MARGIN                       # 3.178 — top outer fill top

TOTAL_HEIGHT = yw9   # 3.695 mm

x0 = 0.0
x1 = L_WIDE                                  # 3.0
x2 = L_WIDE + L_TAPER                        # 5.0
x3 = TOTAL_LENGTH                            # 8.0

via_height  = TOP_Z - M1_Z                   # 1.5862 mm — full stackup

# Via planes — outer edges only
via_bot_y0 = yw0
via_bot_y1 = yw0 + VIA_PLANE_W              # 0.300
via_top_y0 = yn9 - VIA_PLANE_W              # 2.878
via_top_y1 = yn9                             # 3.178

# Port Z range: INT2 → TOP_Z (2 conductors per port: Int2 + M2 signal)
PORT_Z_BOT  = INT2_Z
PORT_Z_TOP  = TOP_Z
PORT_HEIGHT = PORT_Z_TOP - PORT_Z_BOT        # 0.2606

# ===========================================================================
# INITIALIZE
# ===========================================================================
oDesktop.AddMessage("", "", 0, "=== Dual Tapered CPW Build Script Starting ===")

oProject = oDesktop.GetActiveProject()
oDesign  = oProject.GetActiveDesign()
oEditor  = oDesign.SetActiveEditor("3D Modeler")
oBoundarySetup     = oDesign.GetModule("BoundarySetup")
oAnalysisSetup     = oDesign.GetModule("AnalysisSetup")
oDefinitionManager = oProject.GetDefinitionManager()

# ===========================================================================
# 1. CLEAN UP
# ===========================================================================
for pattern in ["m1", "attk_*", "vict_*", "gnd_trace*", "gnd_bot",
                "gnd_top*", "via_plane*", "prepreg*", "Int*", "core",
                "airbox", "port_rect_*"]:
    try:
        objs = list(oEditor.GetMatchedObjectName(pattern))
        if objs:
            oEditor.Delete(["NAME:Selections", "Selections:=", ",".join(objs)])
    except:
        pass

try:
    existing_bnds = list(oBoundarySetup.GetBoundaries())
    to_del = [b for b in ["Port1","Port2","Port3","Port4","Rad1"] if b in existing_bnds]
    if to_del:
        oBoundarySetup.DeleteBoundaries(to_del)
except:
    pass

try:
    if "Setup1" in list(oAnalysisSetup.GetSetups()):
        oAnalysisSetup.DeleteSetups(["Setup1"])
except:
    pass

oDesktop.AddMessage("", "", 0, "Cleanup done")

# ===========================================================================
# 2. MATERIALS
# ===========================================================================
for mat_name, er, tand in [("PP017", "4.4", "0.02"), ("Core039", "4.6", "0.02")]:
    try:
        oDefinitionManager.AddMaterial(
            ["NAME:" + mat_name,
             "CoordinateSystemType:=", "Cartesian",
             ["NAME:AttachedData"],
             "permittivity:=", er,
             "dielectric_loss_tangent:=", tand,
            ]
        )
    except:
        pass

# ===========================================================================
# 3. HELPERS
# ===========================================================================
def mm(v):
    return str(round(v, 6)) + "mm"

def make_box(name, x, y, z, xs, ys, zs, mat, solve_inside):
    try:
        oEditor.CreateBox(
            ["NAME:BoxParameters",
             "XPosition:=", mm(x),  "YPosition:=", mm(y),  "ZPosition:=", mm(z),
             "XSize:=",     mm(xs), "YSize:=",     mm(ys), "ZSize:=",     mm(zs)],
            ["NAME:Attributes",
             "Name:=",          name,
             "MaterialValue:=", '"' + mat + '"',
             "SolveInside:=",   solve_inside]
        )
        oDesktop.AddMessage("", "", 0, "Box: " + name)
    except Exception as e:
        oDesktop.AddMessage("", "", 0, "Box error " + name + ": " + str(e))

def make_trapezoid_prism(name, x1, y_bot1, y_top1, x2, y_bot2, y_top2, z, zs, mat, solve_inside):
    try:
        oEditor.CreatePolyline(
            [
                "NAME:PolylineParameters",
                "IsPolylineCovered:=", True,
                "IsPolylineClosed:=",  True,
                [
                    "NAME:PolylinePoints",
                    ["NAME:PLPoint", "X:=", mm(x1), "Y:=", mm(y_bot1), "Z:=", mm(z)],
                    ["NAME:PLPoint", "X:=", mm(x2), "Y:=", mm(y_bot2), "Z:=", mm(z)],
                    ["NAME:PLPoint", "X:=", mm(x2), "Y:=", mm(y_top2), "Z:=", mm(z)],
                    ["NAME:PLPoint", "X:=", mm(x1), "Y:=", mm(y_top1), "Z:=", mm(z)],
                ],
                [
                    "NAME:PolylineSegments",
                    ["NAME:PLSegment", "SegmentType:=", "Line", "StartIndex:=", 0, "NoOfDef:=", 0],
                    ["NAME:PLSegment", "SegmentType:=", "Line", "StartIndex:=", 1, "NoOfDef:=", 0],
                    ["NAME:PLSegment", "SegmentType:=", "Line", "StartIndex:=", 2, "NoOfDef:=", 0],
                    ["NAME:PLSegment", "SegmentType:=", "Line", "StartIndex:=", 3, "NoOfDef:=", 0],
                ],
                [
                    "NAME:PolylineXSection",
                    "XSectionType:=",        "None",
                    "XSectionOrient:=",      "Auto",
                    "XSectionWidth:=",       "0mm",
                    "XSectionTopWidth:=",    "0mm",
                    "XSectionHeight:=",      "0mm",
                    "XSectionNumSegments:=", "0",
                    "XSectionBendType:=",    "Corner",
                ],
            ],
            [
                "NAME:Attributes",
                "Name:=",          name,
                "MaterialValue:=", '"' + mat + '"',
                "SolveInside:=",   solve_inside,
            ]
        )
        oEditor.SweepAlongVector(
            ["NAME:Selections", "Selections:=", name, "NewPartsModelFlag:=", "Model"],
            [
                "NAME:VectorSweepParameters",
                "DraftAngle:=",                "0deg",
                "DraftType:=",                 "Round",
                "CheckFaceFaceIntersection:=", False,
                "SweepVectorX:=",              "0mm",
                "SweepVectorY:=",              "0mm",
                "SweepVectorZ:=",              mm(zs),
            ]
        )
        oDesktop.AddMessage("", "", 0, "Trapezoid prism: " + name)
    except Exception as e:
        oDesktop.AddMessage("", "", 0, "Trapezoid error " + name + ": " + str(e))

def unite(names):
    try:
        oEditor.Unite(
            ["NAME:Selections",      "Selections:=",   ",".join(names)],
            ["NAME:UniteParameters", "KeepOriginals:=", False]
        )
        oDesktop.AddMessage("", "", 0, "United -> " + names[0])
    except Exception as e:
        oDesktop.AddMessage("", "", 0, "Unite error: " + str(e))

# ===========================================================================
# 4. M1 — bottom ground plane
# ===========================================================================
make_box("m1", x0, yw0, M1_Z,
         TOTAL_LENGTH, TOTAL_HEIGHT, M1_THK, "copper", False)

# ===========================================================================
# 5. DIELECTRIC STACKUP
# ===========================================================================
make_box("prepreg1", x0, yw0, PRE1_Z, TOTAL_LENGTH, TOTAL_HEIGHT, PRE1_THK, "PP017",   True)
make_box("Int1_GND", x0, yw0, INT1_Z, TOTAL_LENGTH, TOTAL_HEIGHT, INT1_THK, "copper",  False)
make_box("core",     x0, yw0, CORE_Z, TOTAL_LENGTH, TOTAL_HEIGHT, CORE_THK, "Core039", True)
make_box("Int2",     x0, yw0, INT2_Z, TOTAL_LENGTH, TOTAL_HEIGHT, INT2_THK, "copper",  False)
make_box("prepreg2", x0, yw0, PRE2_Z, TOTAL_LENGTH, TOTAL_HEIGHT, PRE2_THK, "PP017",   True)

oDesktop.AddMessage("", "", 0, "Stackup complete, M2 at Z=" + str(M2_Z))

# ===========================================================================
# 6. M2 — ATTACKER SIGNAL TRACE  (wide + taper + narrow → united)
# ===========================================================================
make_box("attk_sig_wide",
         x0, yw2, M2_Z, L_WIDE,   W_WIDE,   M2_THK, "copper", False)
make_trapezoid_prism("attk_sig_taper",
         x1, yw2, yw3, x2, yn2, yn3,
         M2_Z, M2_THK, "copper", False)
make_box("attk_sig_narrow",
         x2, yn2, M2_Z, L_NARROW, W_NARROW, M2_THK, "copper", False)
unite(["attk_sig_wide", "attk_sig_taper", "attk_sig_narrow"])

# ===========================================================================
# 7. M2 — VICTIM SIGNAL TRACE  (wide + taper + narrow → united)
# ===========================================================================
make_box("vict_sig_wide",
         x0, yw6, M2_Z, L_WIDE,   W_WIDE,   M2_THK, "copper", False)
make_trapezoid_prism("vict_sig_taper",
         x1, yw6, yw7, x2, yn6, yn7,
         M2_Z, M2_THK, "copper", False)
make_box("vict_sig_narrow",
         x2, yn6, M2_Z, L_NARROW, W_NARROW, M2_THK, "copper", False)
unite(["vict_sig_wide", "vict_sig_taper", "vict_sig_narrow"])

# ===========================================================================
# 8. GND TRACE — same width as signal, spans full stackup (M1_Z → TOP_Z)
#    Wide:   Y = [yw4, yw5] = [1.701, 1.994] mm  width = W_WIDE  = 0.293 mm
#    Narrow: Y = [yn4, yn5] = [1.486, 1.692] mm  width = W_NARROW = 0.206 mm
#    Z range: M1_Z → TOP_Z (same as via planes) for low-impedance ground path
# ===========================================================================
make_box("gnd_trace_wide",
         x0, yw4, M1_Z, L_WIDE,   W_WIDE,   via_height, "copper", False)
make_trapezoid_prism("gnd_trace_taper",
         x1, yw4, yw5, x2, yn4, yn5,
         M1_Z, via_height, "copper", False)
make_box("gnd_trace_narrow",
         x2, yn4, M1_Z, L_NARROW, W_NARROW, via_height, "copper", False)
unite(["gnd_trace_wide", "gnd_trace_taper", "gnd_trace_narrow"])

oDesktop.AddMessage("", "", 0, "GND trace: W_WIDE/W_NARROW, full stackup M1->TOP")

# ===========================================================================
# 9. M2 — BOTTOM OUTER GROUND FILL (constant, no taper)
# ===========================================================================
make_box("gnd_bot",
         x0, yw0, M2_Z, TOTAL_LENGTH, GND_MARGIN, M2_THK, "copper", False)

# ===========================================================================
# 10. M2 — TOP OUTER GROUND FILL  (wide + taper + narrow → united)
# ===========================================================================
make_box("gnd_top_wide",
         x0, yw8, M2_Z, L_WIDE,   GND_MARGIN, M2_THK, "copper", False)
make_trapezoid_prism("gnd_top_taper",
         x1, yw8, yw9, x2, yn8, yn9,
         M2_Z, M2_THK, "copper", False)
make_box("gnd_top_narrow",
         x2, yn8, M2_Z, L_NARROW, GND_MARGIN, M2_THK, "copper", False)
unite(["gnd_top_wide", "gnd_top_taper", "gnd_top_narrow"])

# ===========================================================================
# 11. VIA PLANES — solid copper outer edges, full stackup
# ===========================================================================
make_box("via_plane_bot",
         x0, via_bot_y0, M1_Z,
         TOTAL_LENGTH, VIA_PLANE_W, via_height, "copper", False)

make_box("via_plane_top",
         x0, via_top_y0, M1_Z,
         TOTAL_LENGTH, VIA_PLANE_W, via_height, "copper", False)

oDesktop.AddMessage("", "", 0, "Via planes placed (" + str(VIA_PLANE_W) + " mm outer edges)")

# ===========================================================================
# 12. AIRBOX
# ===========================================================================
P = AIR_PADDING
make_box("airbox",
         x0 - P,             yw0 - P,           M1_Z - P,
         TOTAL_LENGTH + 2*P, TOTAL_HEIGHT + 2*P, TOP_Z - M1_Z + 2*P,
         "vacuum", True)

# ===========================================================================
# 13. RADIATION BOUNDARY
# ===========================================================================
try:
    oBoundarySetup.AssignRadiation(
        ["NAME:Rad1",
         "Objects:=",        ["airbox"],
         "IsFssReference:=", False,
         "IsForPML:=",       False,
        ]
    )
    oDesktop.AddMessage("", "", 0, "Radiation boundary assigned")
except Exception as e:
    oDesktop.AddMessage("", "", 0, "Radiation error: " + str(e))

# ===========================================================================
# 14. PORT RECTANGLES  (INT2_Z → TOP_Z, signal-trace Y width only)
#
# Port1 : attacker left  (x=0,   Y=[yw2, yw3], W=W_WIDE)
# Port2 : attacker right (x=8mm, Y=[yn2, yn3], W=W_NARROW)
# Port3 : victim   left  (x=0,   Y=[yw6, yw7], W=W_WIDE)
# Port4 : victim   right (x=8mm, Y=[yn6, yn7], W=W_NARROW)
#
# GND trace and outer fills are OUTSIDE these Y bands so each port
# touches exactly 2 conductors: Int2 (reference) + M2 signal (terminal).
#
# After running: Draw → Port → Create Terminal Ports
# Integration line: M2 signal face (top of rect) → Int2 face (bottom of rect)
# ===========================================================================
ports = [
    ("port_rect_Port1", x0, yw2, W_WIDE),    # attacker — wide end
    ("port_rect_Port2", x3, yn2, W_NARROW),  # attacker — narrow end
    ("port_rect_Port3", x0, yw6, W_WIDE),    # victim   — wide end
    ("port_rect_Port4", x3, yn6, W_NARROW),  # victim   — narrow end
]

for rect_name, x, y_start, width in ports:
    try:
        oEditor.CreateRectangle(
            ["NAME:RectangleParameters",
             "IsCovered:=", True,
             "XStart:=",    mm(x),
             "YStart:=",    mm(y_start),
             "ZStart:=",    mm(PORT_Z_BOT),
             "Width:=",     mm(width),
             "Height:=",    mm(PORT_HEIGHT),
             "WhichAxis:=", "X",
            ],
            ["NAME:Attributes",
             "Name:=",          rect_name,
             "MaterialValue:=", '"vacuum"',
             "SolveInside:=",   True,
            ]
        )
        oDesktop.AddMessage("", "", 0, "Port rect: " + rect_name)
    except Exception as e:
        oDesktop.AddMessage("", "", 0, "Rect error " + rect_name + ": " + str(e))

# ===========================================================================
# 15. SOLUTION SETUP
# ===========================================================================
try:
    oAnalysisSetup.InsertSetup("HfssDriven",
        ["NAME:Setup1",
         "Frequency:=",              "10GHz",
         "MaxDeltaS:=",              0.02,
         "MaximumPasses:=",          10,
         "MinimumPasses:=",          2,
         "MinimumConvergedPasses:=", 1,
         "PercentRefinement:=",      30,
         "IsEnabled:=",              True,
         ["NAME:MeshLink", "ImportMesh:=", False],
         "BasisOrder:=",             1,
         "DoLambdaRefine:=",         True,
         "DoMaterialLambda:=",       True,
         "SaveRadFieldsOnly:=",      False,
         "SaveAnyFields:=",          True,
        ]
    )
    oDesktop.AddMessage("", "", 0, "Adaptive setup: 10GHz")
except Exception as e:
    oDesktop.AddMessage("", "", 0, "Setup error: " + str(e))

try:
    oAnalysisSetup.InsertFrequencySweep("Setup1",
        ["NAME:Sweep1",
         "IsEnabled:=",     True,
         "RangeType:=",     "LinearCount",
         "RangeStart:=",    "1GHz",
         "RangeEnd:=",      "20GHz",
         "RangeCount:=",    191,
         "Type:=",          "Fast",
         "SaveFields:=",    False,
         "SaveRadFields:=", False,
        ]
    )
    oDesktop.AddMessage("", "", 0, "Sweep: Fast 1-20GHz (change to Interpolating after assigning ports)")
except Exception as e:
    oDesktop.AddMessage("", "", 0, "Sweep error: " + str(e))

# ===========================================================================
# 16. SAVE
# ===========================================================================
oProject.Save()
oDesktop.AddMessage("", "", 0, "=== BUILD COMPLETE ===")
oDesktop.AddMessage("", "", 0, "Layout      : " + str(TOTAL_LENGTH) + " x " + str(round(TOTAL_HEIGHT,4)) + " mm")
oDesktop.AddMessage("", "", 0, "Wide  sec   : W=" + str(W_WIDE)   + "  G=" + str(G_WIDE)   + "  L=" + str(L_WIDE)   + " mm")
oDesktop.AddMessage("", "", 0, "Narrow sec  : W=" + str(W_NARROW) + "  G=" + str(G_NARROW) + "  L=" + str(L_NARROW) + " mm")
oDesktop.AddMessage("", "", 0, "GND trace   : W_WIDE/W_NARROW (same as signal), full stackup via")
oDesktop.AddMessage("", "", 0, "---")
oDesktop.AddMessage("", "", 0, "Attacker Y  : wide=[" + str(round(yw2,3)) + "," + str(round(yw3,3)) + "]  narrow=[" + str(round(yn2,3)) + "," + str(round(yn3,3)) + "]")
oDesktop.AddMessage("", "", 0, "GND trace Y : wide=[" + str(round(yw4,3)) + "," + str(round(yw5,3)) + "]  narrow=[" + str(round(yn4,3)) + "," + str(round(yn5,3)) + "]")
oDesktop.AddMessage("", "", 0, "Victim Y    : wide=[" + str(round(yw6,3)) + "," + str(round(yw7,3)) + "]  narrow=[" + str(round(yn6,3)) + "," + str(round(yn7,3)) + "]")
oDesktop.AddMessage("", "", 0, "---")
oDesktop.AddMessage("", "", 0, "Next steps:")
oDesktop.AddMessage("", "", 0, "  1. Draw -> Port -> Create Terminal Ports")
oDesktop.AddMessage("", "", 0, "     Port1 x=0mm  attacker wide end")
oDesktop.AddMessage("", "", 0, "     Port2 x=8mm  attacker narrow end")
oDesktop.AddMessage("", "", 0, "     Port3 x=0mm  victim wide end")
oDesktop.AddMessage("", "", 0, "     Port4 x=8mm  victim narrow end")
oDesktop.AddMessage("", "", 0, "     Integration line: M2 signal top -> Int2 bottom")
oDesktop.AddMessage("", "", 0, "  2. Right-click Sweep1 -> Edit -> change Type to Interpolating")
oDesktop.AddMessage("", "", 0, "  3. Validate, then F10 to analyze")
oDesktop.AddMessage("", "", 0, "  Key results:")
oDesktop.AddMessage("", "", 0, "    dB(S(2,1)) = attacker insertion loss")
oDesktop.AddMessage("", "", 0, "    dB(S(3,1)) = NEXT (near-end crosstalk)")
oDesktop.AddMessage("", "", 0, "    dB(S(4,1)) = FEXT (far-end crosstalk)")