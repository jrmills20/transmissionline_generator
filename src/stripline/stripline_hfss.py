# -*- coding: utf-8 -*-
# Dual Stripline (Attacker + Victim) — Symmetric HFSS Builder
#
# Structure:
#  [left pad 0..3] [left taper 3..5] [TL 5..8] [right taper 8..10] [right pad 10..13]
#
# 3 traces: attacker | GND | victim — taper on BOTH sides keeps trace spacing consistent
#   Left via  at x=3: pad (surface) → stripline (embedded)
#   Right via at x=10: stripline → pad (surface)
#   Signal pads: isolated from GND_TOP by anti-pads (do NOT connect to ground)
#   GND trace : connects directly to GND_TOP through vias (no anti-pad)
#
# Ports: GND_BOT (z=0) → top of surface pad (z=1.7)  — "bottom plate to top pads"
#   Port1: attacker left  x=0   Y=[yp_attk_bot, yp_attk_top]
#   Port2: attacker right x=13  Y=[yp_attk_bot, yp_attk_top]
#   Port3: victim   left  x=0   Y=[yp_vict_bot, yp_vict_top]
#   Port4: victim   right x=13  Y=[yp_vict_bot, yp_vict_top]
#   Integration line: pad top (z=1.7) → GND_BOT bottom (z=0.0)

# ===========================================================================
# STACKUP
# ===========================================================================
GND_BOT_Z  = 0.0;   GND_THK  = 0.1
DIEL_Z     = 0.1;   DIEL_THK = 1.5
SL_Z       = 0.8;   SL_THK   = 0.1
GND_TOP_Z  = 1.6
TOP_Z      = 1.7

# ===========================================================================
# DIMENSIONS
# ===========================================================================
W_PAD      = 0.293;  G_PAD = 0.204
W_SL       = 0.7;    G_SL  = 0.7
L_PAD      = 3.0;    L_TAPER = 2.0;  L_TL = 3.0
VIA_W      = 0.7
GND_MARGIN = VIA_W + 0.7     # 1.4mm
CLEARANCE  = 0.15
AIR_PADDING = 2.0
DIEL_ER    = 3.48
DIEL_TAND  = 0.002

# ===========================================================================
# DERIVED
# ===========================================================================
TOTAL_LENGTH = 2*L_PAD + 2*L_TAPER + L_TL   # 13.0 mm

x0 = 0.0
x1 = L_PAD                                   # 3.0
x2 = L_PAD + L_TAPER                         # 5.0
x3 = L_PAD + L_TAPER + L_TL                  # 8.0
x4 = L_PAD + L_TAPER + L_TL + L_TAPER        # 10.0
x5 = TOTAL_LENGTH                             # 13.0

VIA_HALF         = W_PAD / 2
via_height       = TOP_Z - GND_BOT_Z          # 1.7mm
trans_via_height = GND_TOP_Z - SL_Z           # 0.8mm

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

TOTAL_HEIGHT    = yt_total
via_top_pad_bot = yp_total - VIA_W
via_top_tl_bot  = yt_total - VIA_W

PORT_Z_BOT  = GND_BOT_Z   # 0.0
PORT_Z_TOP  = TOP_Z        # 1.7

# ===========================================================================
# INITIALIZE
# ===========================================================================
oDesktop.AddMessage("", "", 0, "=== Dual Stripline Symmetric Build Starting ===")
oDesktop.AddMessage("", "", 0, "Length=" + str(TOTAL_LENGTH) + "mm  x0-x5: " +
    str(x0)+","+str(x1)+","+str(x2)+","+str(x3)+","+str(x4)+","+str(x5))

oProject = oDesktop.GetActiveProject()
oDesign  = oProject.GetActiveDesign()
oEditor  = oDesign.SetActiveEditor("3D Modeler")
oBoundarySetup     = oDesign.GetModule("BoundarySetup")
oAnalysisSetup     = oDesign.GetModule("AnalysisSetup")
oDefinitionManager = oProject.GetDefinitionManager()

# ===========================================================================
# 1. CLEAN UP
# ===========================================================================
for pattern in ["gnd_bot*","gnd_top*","diel*","attk_*","vict_*",
                "gnd_trace*","gnd_via*","via_wall*","anti_pad*",
                "airbox","port_rect_*"]:
    try:
        objs = list(oEditor.GetMatchedObjectName(pattern))
        if objs:
            oEditor.Delete(["NAME:Selections","Selections:=",",".join(objs)])
    except: pass

try:
    existing_bnds = list(oBoundarySetup.GetBoundaries())
    to_del = [b for b in ["Port1","Port2","Port3","Port4","Rad1"] if b in existing_bnds]
    if to_del: oBoundarySetup.DeleteBoundaries(to_del)
except: pass

try:
    if "Setup1" in list(oAnalysisSetup.GetSetups()):
        oAnalysisSetup.DeleteSetups(["Setup1"])
except: pass

oDesktop.AddMessage("", "", 0, "Cleanup done")

# ===========================================================================
# 2. MATERIAL
# ===========================================================================
try:
    oDefinitionManager.AddMaterial(
        ["NAME:Stripline_Diel","CoordinateSystemType:=","Cartesian",
         ["NAME:AttachedData"],
         "permittivity:=",str(DIEL_ER),
         "dielectric_loss_tangent:=",str(DIEL_TAND)])
    oDesktop.AddMessage("", "", 0, "Material: er=" + str(DIEL_ER))
except: pass

# ===========================================================================
# 3. HELPERS
# ===========================================================================
def mm(v):
    return str(round(v, 6)) + "mm"

def make_box(name, x, y, z, xs, ys, zs, mat, si):
    try:
        oEditor.CreateBox(
            ["NAME:BoxParameters",
             "XPosition:=",mm(x),"YPosition:=",mm(y),"ZPosition:=",mm(z),
             "XSize:=",mm(xs),"YSize:=",mm(ys),"ZSize:=",mm(zs)],
            ["NAME:Attributes","Name:=",name,
             "MaterialValue:=",'"'+mat+'"',"SolveInside:=",si])
        oDesktop.AddMessage("", "", 0, "Box: " + name)
    except Exception as e:
        oDesktop.AddMessage("", "", 0, "Box error " + name + ": " + str(e))

def make_trap(name, xa, yb1, yt1, xb, yb2, yt2, z, zs, mat, si):
    try:
        oEditor.CreatePolyline(
            ["NAME:PolylineParameters","IsPolylineCovered:=",True,"IsPolylineClosed:=",True,
             ["NAME:PolylinePoints",
              ["NAME:PLPoint","X:=",mm(xa),"Y:=",mm(yb1),"Z:=",mm(z)],
              ["NAME:PLPoint","X:=",mm(xb),"Y:=",mm(yb2),"Z:=",mm(z)],
              ["NAME:PLPoint","X:=",mm(xb),"Y:=",mm(yt2),"Z:=",mm(z)],
              ["NAME:PLPoint","X:=",mm(xa),"Y:=",mm(yt1),"Z:=",mm(z)]],
             ["NAME:PolylineSegments",
              ["NAME:PLSegment","SegmentType:=","Line","StartIndex:=",0,"NoOfDef:=",0],
              ["NAME:PLSegment","SegmentType:=","Line","StartIndex:=",1,"NoOfDef:=",0],
              ["NAME:PLSegment","SegmentType:=","Line","StartIndex:=",2,"NoOfDef:=",0],
              ["NAME:PLSegment","SegmentType:=","Line","StartIndex:=",3,"NoOfDef:=",0]],
             ["NAME:PolylineXSection","XSectionType:=","None","XSectionOrient:=","Auto",
              "XSectionWidth:=","0mm","XSectionTopWidth:=","0mm","XSectionHeight:=","0mm",
              "XSectionNumSegments:=","0","XSectionBendType:=","Corner"]],
            ["NAME:Attributes","Name:=",name,"MaterialValue:=",'"'+mat+'"',"SolveInside:=",si])
        oEditor.SweepAlongVector(
            ["NAME:Selections","Selections:=",name,"NewPartsModelFlag:=","Model"],
            ["NAME:VectorSweepParameters","DraftAngle:=","0deg","DraftType:=","Round",
             "CheckFaceFaceIntersection:=",False,
             "SweepVectorX:=","0mm","SweepVectorY:=","0mm","SweepVectorZ:=",mm(zs)])
        oDesktop.AddMessage("", "", 0, "Trap: " + name)
    except Exception as e:
        oDesktop.AddMessage("", "", 0, "Trap error " + name + ": " + str(e))

def unite(names):
    try:
        oEditor.Unite(
            ["NAME:Selections","Selections:=",",".join(names)],
            ["NAME:UniteParameters","KeepOriginals:=",False])
        oDesktop.AddMessage("", "", 0, "United -> " + names[0])
    except Exception as e:
        oDesktop.AddMessage("", "", 0, "Unite error: " + str(e))

def subtract(blank, tools, keep=False):
    try:
        oEditor.Subtract(
            ["NAME:Selections","Blank Parts:=",blank,
             "Tool Parts:=",",".join(tools) if isinstance(tools,list) else tools],
            ["NAME:SubtractParameters","KeepOriginals:=",keep])
        oDesktop.AddMessage("", "", 0, "Subtracted from " + blank)
    except Exception as e:
        oDesktop.AddMessage("", "", 0, "Subtract error: " + str(e))

# ===========================================================================
# 4. GND_BOT — 5 sections, united
# ===========================================================================
make_box("gnd_bot_lpad",  x0, 0, GND_BOT_Z, L_PAD,  yp_total, GND_THK, "copper", False)
make_trap("gnd_bot_ltap", x1, 0, yp_total, x2, 0, yt_total, GND_BOT_Z, GND_THK, "copper", False)
make_box("gnd_bot_tl",    x2, 0, GND_BOT_Z, L_TL,   yt_total, GND_THK, "copper", False)
make_trap("gnd_bot_rtap", x3, 0, yt_total, x4, 0, yp_total, GND_BOT_Z, GND_THK, "copper", False)
make_box("gnd_bot_rpad",  x4, 0, GND_BOT_Z, L_PAD,  yp_total, GND_THK, "copper", False)
unite(["gnd_bot_lpad","gnd_bot_ltap","gnd_bot_tl","gnd_bot_rtap","gnd_bot_rpad"])

# ===========================================================================
# 5. DIELECTRIC — 5 sections, united (conductors subtracted later)
# ===========================================================================
make_box("diel_lpad",  x0, 0, DIEL_Z, L_PAD, yp_total, DIEL_THK, "Stripline_Diel", True)
make_trap("diel_ltap", x1, 0, yp_total, x2, 0, yt_total, DIEL_Z, DIEL_THK, "Stripline_Diel", True)
make_box("diel_tl",    x2, 0, DIEL_Z, L_TL,  yt_total, DIEL_THK, "Stripline_Diel", True)
make_trap("diel_rtap", x3, 0, yt_total, x4, 0, yp_total, DIEL_Z, DIEL_THK, "Stripline_Diel", True)
make_box("diel_rpad",  x4, 0, DIEL_Z, L_PAD, yp_total, DIEL_THK, "Stripline_Diel", True)
unite(["diel_lpad","diel_ltap","diel_tl","diel_rtap","diel_rpad"])

# ===========================================================================
# 6. GND_TOP — 5 sections, united (anti-pads subtracted later)
# ===========================================================================
make_box("gnd_top_lpad",  x0, 0, GND_TOP_Z, L_PAD, yp_total, GND_THK, "copper", False)
make_trap("gnd_top_ltap", x1, 0, yp_total, x2, 0, yt_total, GND_TOP_Z, GND_THK, "copper", False)
make_box("gnd_top_tl",    x2, 0, GND_TOP_Z, L_TL,  yt_total, GND_THK, "copper", False)
make_trap("gnd_top_rtap", x3, 0, yt_total, x4, 0, yp_total, GND_TOP_Z, GND_THK, "copper", False)
make_box("gnd_top_rpad",  x4, 0, GND_TOP_Z, L_PAD, yp_total, GND_THK, "copper", False)
unite(["gnd_top_lpad","gnd_top_ltap","gnd_top_tl","gnd_top_rtap","gnd_top_rpad"])

oDesktop.AddMessage("", "", 0, "Ground planes + dielectric placed")

# ===========================================================================
# 7. ATTACKER — left pad + left via + left taper + TL + right taper + right via + right pad
# ===========================================================================
# Surface pads (on GND_TOP layer, isolated by anti-pads)
make_box("attk_pad_l", x0, yp_attk_bot, GND_TOP_Z, L_PAD, W_PAD, GND_THK, "copper", False)
make_box("attk_pad_r", x4, yp_attk_bot, GND_TOP_Z, L_PAD, W_PAD, GND_THK, "copper", False)
# Transition vias (surface → stripline)
make_box("attk_via_l", x1-VIA_HALF, yp_attk_bot, SL_Z, W_PAD, W_PAD, trans_via_height, "copper", False)
make_box("attk_via_r", x4-VIA_HALF, yp_attk_bot, SL_Z, W_PAD, W_PAD, trans_via_height, "copper", False)
# Left taper (widens pad→TL)
make_trap("attk_ltap", x1, yp_attk_bot, yp_attk_top, x2, yt_attk_bot, yt_attk_top, SL_Z, SL_THK, "copper", False)
# Straight TL
make_box("attk_tl", x2, yt_attk_bot, SL_Z, L_TL, W_SL, SL_THK, "copper", False)
# Right taper (narrows TL→pad)
make_trap("attk_rtap", x3, yt_attk_bot, yt_attk_top, x4, yp_attk_bot, yp_attk_top, SL_Z, SL_THK, "copper", False)

oDesktop.AddMessage("", "", 0, "Attacker placed")

# ===========================================================================
# 8. VICTIM — same structure as attacker
# ===========================================================================
make_box("vict_pad_l", x0, yp_vict_bot, GND_TOP_Z, L_PAD, W_PAD, GND_THK, "copper", False)
make_box("vict_pad_r", x4, yp_vict_bot, GND_TOP_Z, L_PAD, W_PAD, GND_THK, "copper", False)
make_box("vict_via_l", x1-VIA_HALF, yp_vict_bot, SL_Z, W_PAD, W_PAD, trans_via_height, "copper", False)
make_box("vict_via_r", x4-VIA_HALF, yp_vict_bot, SL_Z, W_PAD, W_PAD, trans_via_height, "copper", False)
make_trap("vict_ltap", x1, yp_vict_bot, yp_vict_top, x2, yt_vict_bot, yt_vict_top, SL_Z, SL_THK, "copper", False)
make_box("vict_tl", x2, yt_vict_bot, SL_Z, L_TL, W_SL, SL_THK, "copper", False)
make_trap("vict_rtap", x3, yt_vict_bot, yt_vict_top, x4, yp_vict_bot, yp_vict_top, SL_Z, SL_THK, "copper", False)

oDesktop.AddMessage("", "", 0, "Victim placed")

# ===========================================================================
# 9. GND TRACE — vias on both ends + left taper + TL (full stackup) + right taper
#    GND trace vias connect directly to GND_TOP (same net — no anti-pad needed)
# ===========================================================================
make_box("gnd_via_l", x1-VIA_HALF, yp_gnd_bot, SL_Z, W_PAD, W_PAD, trans_via_height, "copper", False)
make_box("gnd_via_r", x4-VIA_HALF, yp_gnd_bot, SL_Z, W_PAD, W_PAD, trans_via_height, "copper", False)
make_trap("gnd_ltap", x1, yp_gnd_bot, yp_gnd_top, x2, yt_gnd_bot, yt_gnd_top, SL_Z, SL_THK, "copper", False)
make_box("gnd_tl", x2, yt_gnd_bot, GND_BOT_Z, L_TL, W_SL, via_height, "copper", False)  # full stackup
make_trap("gnd_rtap", x3, yt_gnd_bot, yt_gnd_top, x4, yp_gnd_bot, yp_gnd_top, SL_Z, SL_THK, "copper", False)

oDesktop.AddMessage("", "", 0, "GND trace placed (vias both ends, full-stackup TL)")

# ===========================================================================
# 10. OUTER VIA WALLS — 0.7mm, full stackup, symmetric
# ===========================================================================
make_box("via_wall_bot", x0, 0, GND_BOT_Z, TOTAL_LENGTH, VIA_W, via_height, "copper", False)

make_box("via_wall_top_lpad",   x0, via_top_pad_bot, GND_BOT_Z, L_PAD,  VIA_W, via_height, "copper", False)
make_trap("via_wall_top_ltap",  x1, via_top_pad_bot, yp_total, x2, via_top_tl_bot, yt_total, GND_BOT_Z, via_height, "copper", False)
make_box("via_wall_top_tl",     x2, via_top_tl_bot,  GND_BOT_Z, L_TL,   VIA_W, via_height, "copper", False)
make_trap("via_wall_top_rtap",  x3, via_top_tl_bot,  yt_total, x4, via_top_pad_bot, yp_total, GND_BOT_Z, via_height, "copper", False)
make_box("via_wall_top_rpad",   x4, via_top_pad_bot, GND_BOT_Z, L_PAD,  VIA_W, via_height, "copper", False)
unite(["via_wall_top_lpad","via_wall_top_ltap","via_wall_top_tl","via_wall_top_rtap","via_wall_top_rpad"])

oDesktop.AddMessage("", "", 0, "Via walls placed")

# ===========================================================================
# 11. SUBTRACT embedded conductors from dielectric
# ===========================================================================
subtract("diel",
         ["attk_via_l","attk_ltap","attk_tl","attk_rtap","attk_via_r",
          "vict_via_l","vict_ltap","vict_tl","vict_rtap","vict_via_r",
          "gnd_via_l","gnd_ltap","gnd_tl","gnd_rtap","gnd_via_r",
          "via_wall_bot","via_wall_top"],
         keep=True)
oDesktop.AddMessage("", "", 0, "Embedded conductors subtracted from dielectric")

# ===========================================================================
# 12. ANTI-PADS in GND_TOP — signal pads only (attacker + victim, BOTH ends)
#     GND trace connects to GND_TOP directly — no anti-pad for GND
# ===========================================================================
C = CLEARANCE
# Left anti-pads
make_box("anti_pad_attk_l", x0-C, yp_attk_bot-C, GND_TOP_Z,
         L_PAD+VIA_HALF+C, W_PAD+2*C, GND_THK, "vacuum", True)
make_box("anti_pad_vict_l", x0-C, yp_vict_bot-C, GND_TOP_Z,
         L_PAD+VIA_HALF+C, W_PAD+2*C, GND_THK, "vacuum", True)
# Right anti-pads (mirror of left)
make_box("anti_pad_attk_r", x4-VIA_HALF-C, yp_attk_bot-C, GND_TOP_Z,
         L_PAD+VIA_HALF+C, W_PAD+2*C, GND_THK, "vacuum", True)
make_box("anti_pad_vict_r", x4-VIA_HALF-C, yp_vict_bot-C, GND_TOP_Z,
         L_PAD+VIA_HALF+C, W_PAD+2*C, GND_THK, "vacuum", True)
subtract("gnd_top",
         ["anti_pad_attk_l","anti_pad_vict_l",
          "anti_pad_attk_r","anti_pad_vict_r"],
         keep=False)
oDesktop.AddMessage("", "", 0, "Anti-pads subtracted (signal pads isolated from GND_TOP)")

# ===========================================================================
# 13. AIRBOX
# ===========================================================================
P = AIR_PADDING
make_box("airbox", x0-P, 0-P, GND_BOT_Z-P,
         TOTAL_LENGTH+2*P, TOTAL_HEIGHT+2*P, TOP_Z-GND_BOT_Z+2*P,
         "vacuum", True)

# ===========================================================================
# 14. RADIATION BOUNDARY
# ===========================================================================
try:
    oBoundarySetup.AssignRadiation(
        ["NAME:Rad1","Objects:=",["airbox"],"IsFssReference:=",False,"IsForPML:=",False])
    oDesktop.AddMessage("", "", 0, "Radiation boundary assigned")
except Exception as e:
    oDesktop.AddMessage("", "", 0, "Radiation error: " + str(e))

# ===========================================================================
# 15. PORT RECTANGLES
#
# All 4 ports: Z = GND_BOT_Z (0.0) → TOP_Z (1.7mm)
# Y = W_PAD wide, centred on the signal pad trace
#
# At x=0 and x=13 (pad section):
#   z=0.0 - 0.1 : GND_BOT       ← reference
#   z=0.1 - 1.6 : dielectric only (no conductor at this Y)
#   z=1.6 - 1.7 : surface pad   ← signal  (GND_TOP cleared by anti-pad)
#   → exactly 2 conductors ✓
#
# Integration line: pad top (z=1.7) → GND_BOT bottom (z=0.0)
# ===========================================================================
ports = [
    ("port_rect_Port1", x0, yp_attk_bot, W_PAD),   # attacker left
    ("port_rect_Port2", x5, yp_attk_bot, W_PAD),   # attacker right
    ("port_rect_Port3", x0, yp_vict_bot, W_PAD),   # victim left
    ("port_rect_Port4", x5, yp_vict_bot, W_PAD),   # victim right
]
for rect_name, x, y_start, width in ports:
    try:
        oEditor.CreateRectangle(
            ["NAME:RectangleParameters","IsCovered:=",True,
             "XStart:=",mm(x),"YStart:=",mm(y_start),"ZStart:=",mm(PORT_Z_BOT),
             "Width:=",mm(width),"Height:=",mm(PORT_Z_TOP - PORT_Z_BOT),
             "WhichAxis:=","X"],
            ["NAME:Attributes","Name:=",rect_name,
             "MaterialValue:=",'"vacuum"',"SolveInside:=",True])
        oDesktop.AddMessage("", "", 0, "Port rect: " + rect_name)
    except Exception as e:
        oDesktop.AddMessage("", "", 0, "Rect error " + rect_name + ": " + str(e))

# ===========================================================================
# 16. SOLUTION SETUP
# ===========================================================================
try:
    oAnalysisSetup.InsertSetup("HfssDriven",
        ["NAME:Setup1","Frequency:=","10GHz","MaxDeltaS:=",0.02,
         "MaximumPasses:=",10,"MinimumPasses:=",2,"MinimumConvergedPasses:=",1,
         "PercentRefinement:=",30,"IsEnabled:=",True,
         ["NAME:MeshLink","ImportMesh:=",False],
         "BasisOrder:=",1,"DoLambdaRefine:=",True,"DoMaterialLambda:=",True,
         "SaveRadFieldsOnly:=",False,"SaveAnyFields:=",True])
    oDesktop.AddMessage("", "", 0, "Adaptive setup: 10GHz")
except Exception as e:
    oDesktop.AddMessage("", "", 0, "Setup error: " + str(e))

try:
    oAnalysisSetup.InsertFrequencySweep("Setup1",
        ["NAME:Sweep1","IsEnabled:=",True,"RangeType:=","LinearCount",
         "RangeStart:=","1GHz","RangeEnd:=","20GHz","RangeCount:=",191,
         "Type:=","Fast","SaveFields:=",False,"SaveRadFields:=",False])
    oDesktop.AddMessage("", "", 0, "Sweep: Fast 1-20GHz")
except Exception as e:
    oDesktop.AddMessage("", "", 0, "Sweep error: " + str(e))

# ===========================================================================
# 17. SAVE
# ===========================================================================
oProject.Save()
oDesktop.AddMessage("", "", 0, "=== BUILD COMPLETE ===")
oDesktop.AddMessage("", "", 0, "Length  : " + str(TOTAL_LENGTH) + "mm = pad(" + str(L_PAD) +
    ") + taper(" + str(L_TAPER) + ") + TL(" + str(L_TL) +
    ") + taper(" + str(L_TAPER) + ") + pad(" + str(L_PAD) + ")")
oDesktop.AddMessage("", "", 0, "Stackup : GND(0.1) / Diel(1.5,er=" + str(DIEL_ER) + ") / GND(0.1)")
oDesktop.AddMessage("", "", 0, "Pad     : W=" + str(W_PAD) + "  G=" + str(G_PAD))
oDesktop.AddMessage("", "", 0, "TL      : W=" + str(W_SL)  + "  G=" + str(G_SL))
oDesktop.AddMessage("", "", 0, "IMPORTANT: Update DIEL_TAND=" + str(DIEL_TAND))
oDesktop.AddMessage("", "", 0, "---")
oDesktop.AddMessage("", "", 0, "Next: Draw -> Port -> Create Terminal Ports")
oDesktop.AddMessage("", "", 0, "  Port1 x=0mm   attacker left : line pad top (z=1.7) -> GND_BOT (z=0)")
oDesktop.AddMessage("", "", 0, "  Port2 x=13mm  attacker right: line pad top (z=1.7) -> GND_BOT (z=0)")
oDesktop.AddMessage("", "", 0, "  Port3 x=0mm   victim   left : line pad top (z=1.7) -> GND_BOT (z=0)")
oDesktop.AddMessage("", "", 0, "  Port4 x=13mm  victim   right: line pad top (z=1.7) -> GND_BOT (z=0)")
oDesktop.AddMessage("", "", 0, "Then: Sweep1 -> Interpolating -> Validate -> F10")
oDesktop.AddMessage("", "", 0, "Key: dB(S(2,1))=loss  dB(S(3,1))=NEXT  dB(S(4,1))=FEXT")
