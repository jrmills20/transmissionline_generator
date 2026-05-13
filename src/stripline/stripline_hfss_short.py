# -*- coding: utf-8 -*-
# Dual Stripline (Attacker + Victim) — One-Sided HFSS Builder
#
# Changes from original symmetric script:
#   1. One-sided: pins on LEFT (x=0) only; structure ends at x=8mm
#   2. Lengths matched to microstrip: L_PAD=3, L_TAPER=2, L_TL=3 (unchanged)
#   3. GND_TOP: full-width plane over taper+TL, X-inset to clear pin/via area
#   4. Ports: Port1/3 at pins (x=0), Port2/4 at TL right end (x=8mm)
#   5. All ground conductors (GND_BOT + GND_TOP + via walls) united into one
#      object so all ports share a single unambiguous ground reference
#
# TL trace dimensions UNCHANGED: W_SL=0.7, G_SL=0.7

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
W_PAD      = 0.293;  G_PAD = 0.204   # pin section — unchanged
W_SL       = 0.7;    G_SL  = 0.7     # TL section  — unchanged
L_PAD      = 0.5;    L_TAPER = 1.0;  L_TL = 3.0
VIA_W      = 0.7
GND_MARGIN = VIA_W + 0.7             # 1.4 mm
AIR_PADDING = 2.0
DIEL_ER    = 3.48
DIEL_TAND  = 0.002

# Pull GND_TOP left edge away from pin/via area (mm past x1 into taper)
GND_TOP_X_INSET = 0.3

# ===========================================================================
# DERIVED
# ===========================================================================
TOTAL_LENGTH = L_PAD + L_TAPER + L_TL   # 8.0 mm (one-sided)

x0 = 0.0
x1 = L_PAD                              # 3.0
x2 = L_PAD + L_TAPER                   # 5.0
x3 = L_PAD + L_TAPER + L_TL            # 8.0

VIA_HALF         = W_PAD / 2
via_height       = TOP_Z - GND_BOT_Z
trans_via_height = GND_TOP_Z - SL_Z

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

# GND_TOP start X and interpolated total Y-width at that X
gt_x              = x1 + GND_TOP_X_INSET
t                 = GND_TOP_X_INSET / L_TAPER        # 0-1 fraction into taper
gt_ytotal_at_start = yp_total + t * (yt_total - yp_total)

# Port Z ranges
PIN_PORT_Z_BOT = GND_BOT_Z;  PIN_PORT_Z_TOP = TOP_Z   # full stackup for pin ports
TL_PORT_Z_BOT  = SL_Z;       TL_PORT_Z_TOP  = TOP_Z   # stripline→GND_TOP for TL ports

# ===========================================================================
# INITIALIZE
# ===========================================================================
oDesktop.AddMessage("", "", 0, "=== Dual Stripline One-Sided Build Starting ===")

oProject = oDesktop.GetActiveProject()
oDesign  = oProject.GetActiveDesign()
oEditor  = oDesign.SetActiveEditor("3D Modeler")
oBoundarySetup     = oDesign.GetModule("BoundarySetup")
oAnalysisSetup     = oDesign.GetModule("AnalysisSetup")
oDefinitionManager = oProject.GetDefinitionManager()

# ===========================================================================
# 1. CLEAN UP
# ===========================================================================
for pattern in ["gnd_bot*","gnd_top*","diel*","attk*","vict*",
                "gnd_pad*","gnd_via*","gnd_ltap*","gnd_tl*",
                "via_wall*","airbox","port_rect_*"]:
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
            ["NAME:PolylineParameters","IsPolylineCovered:=",True,
             "IsPolylineClosed:=",True,
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
            ["NAME:Attributes","Name:=",name,
             "MaterialValue:=",'"'+mat+'"',"SolveInside:=",si])
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
# 4. GND_BOT — left pad + taper + TL
# ===========================================================================
make_box("gnd_bot_lpad",  x0,0,GND_BOT_Z, L_PAD, yp_total, GND_THK, "copper", False)
make_trap("gnd_bot_ltap", x1,0,yp_total,  x2,0,yt_total, GND_BOT_Z, GND_THK, "copper", False)
make_box("gnd_bot_tl",    x2,0,GND_BOT_Z, L_TL,  yt_total, GND_THK, "copper", False)
unite(["gnd_bot_lpad","gnd_bot_ltap","gnd_bot_tl"])

# ===========================================================================
# 5. DIELECTRIC — left pad + taper + TL
# ===========================================================================
make_box("diel_lpad",  x0,0,DIEL_Z, L_PAD, yp_total, DIEL_THK, "Stripline_Diel", True)
make_trap("diel_ltap", x1,0,yp_total, x2,0,yt_total, DIEL_Z, DIEL_THK, "Stripline_Diel", True)
make_box("diel_tl",    x2,0,DIEL_Z, L_TL,  yt_total, DIEL_THK, "Stripline_Diel", True)
unite(["diel_lpad","diel_ltap","diel_tl"])

# ===========================================================================
# 6. GND_TOP — FULL WIDTH, starts at gt_x (inset from pin/via area), ends at x3
#
#   gnd_top_ltap : gt_x → x2   tapered, full width (0 → interpolated Y at gt_x)
#   gnd_top_tl   : x2   → x3   straight box, full width (0 → yt_total)
#   United into gnd_top_ltap
#
#   Pin sections (x=0 → x1) have NO top copper, matching original design intent
# ===========================================================================
make_trap("gnd_top_ltap", gt_x, 0, gt_ytotal_at_start,
                          x2,   0, yt_total,
                          GND_TOP_Z, GND_THK, "copper", False)
make_box("gnd_top_tl",    x2, 0, GND_TOP_Z, L_TL, yt_total, GND_THK, "copper", False)
unite(["gnd_top_ltap","gnd_top_tl"])

oDesktop.AddMessage("", "", 0, "GND_TOP full-width taper+TL: x=[" + str(round(gt_x,3))
                              + "," + str(x3) + "]  y=[0," + str(round(yt_total,3)) + "]")

# ===========================================================================
# 7. ATTACKER — pin_l → via_l → ltap → tl  (no right side)
# ===========================================================================
make_box("attk_pad_l",  x0,  yp_attk_bot, GND_TOP_Z, L_PAD, W_PAD, GND_THK, "copper", False)
make_box("attk_via_l",  x1-VIA_HALF, yp_attk_bot, SL_Z, W_PAD, W_PAD, trans_via_height, "copper", False)
make_trap("attk_ltap",  x1, yp_attk_bot, yp_attk_top, x2, yt_attk_bot, yt_attk_top, SL_Z, SL_THK, "copper", False)
make_box("attk_tl",     x2, yt_attk_bot, SL_Z, L_TL, W_SL, SL_THK, "copper", False)
unite(["attk_pad_l","attk_via_l","attk_ltap","attk_tl"])
oDesktop.AddMessage("", "", 0, "Attacker united -> attk_pad_l")

# ===========================================================================
# 8. GND TRACE — pin_l → via_l → ltap → tl full stackup (no right side)
# ===========================================================================
make_box("gnd_pad_l",  x0,  yp_gnd_bot, GND_TOP_Z, L_PAD, W_PAD, GND_THK, "copper", False)
make_box("gnd_via_l",  x1-VIA_HALF, yp_gnd_bot, SL_Z, W_PAD, W_PAD, trans_via_height, "copper", False)
make_trap("gnd_ltap",  x1, yp_gnd_bot, yp_gnd_top, x2, yt_gnd_bot, yt_gnd_top, SL_Z, SL_THK, "copper", False)
make_box("gnd_tl",     x2, yt_gnd_bot, GND_BOT_Z, L_TL, W_SL, via_height, "copper", False)
unite(["gnd_pad_l","gnd_via_l","gnd_ltap","gnd_tl"])
oDesktop.AddMessage("", "", 0, "GND trace united -> gnd_pad_l")

# ===========================================================================
# 9. VICTIM — pin_l → via_l → ltap → tl  (no right side)
# ===========================================================================
make_box("vict_pad_l",  x0,  yp_vict_bot, GND_TOP_Z, L_PAD, W_PAD, GND_THK, "copper", False)
make_box("vict_via_l",  x1-VIA_HALF, yp_vict_bot, SL_Z, W_PAD, W_PAD, trans_via_height, "copper", False)
make_trap("vict_ltap",  x1, yp_vict_bot, yp_vict_top, x2, yt_vict_bot, yt_vict_top, SL_Z, SL_THK, "copper", False)
make_box("vict_tl",     x2, yt_vict_bot, SL_Z, L_TL, W_SL, SL_THK, "copper", False)
unite(["vict_pad_l","vict_via_l","vict_ltap","vict_tl"])
oDesktop.AddMessage("", "", 0, "Victim united -> vict_pad_l")

# ===========================================================================
# 10. OUTER VIA WALLS — left pad + taper + TL only
# ===========================================================================
make_box("via_wall_bot",      x0,0,GND_BOT_Z, TOTAL_LENGTH, VIA_W, via_height, "copper", False)
make_box("via_wall_top_lpad", x0,via_top_pad_bot,GND_BOT_Z, L_PAD, VIA_W, via_height, "copper", False)
make_trap("via_wall_top_ltap",x1,via_top_pad_bot,yp_total,x2,via_top_tl_bot,yt_total,GND_BOT_Z,via_height,"copper",False)
make_box("via_wall_top_tl",   x2,via_top_tl_bot, GND_BOT_Z, L_TL, VIA_W, via_height, "copper", False)
unite(["via_wall_top_lpad","via_wall_top_ltap","via_wall_top_tl"])
oDesktop.AddMessage("", "", 0, "Via walls placed")

# ===========================================================================
# 10b. UNITE ALL GROUND CONDUCTORS into one object
#
#   GND_BOT (gnd_bot_lpad) + GND_TOP (gnd_top_ltap) + via walls (both)
#   → single copper shell, all at the same potential
#   → both pin ports and TL ports now reference the same ground node
#   → eliminates the split-reference problem that corrupts S-parameters
#
#   Surviving object name: gnd_bot_lpad
# ===========================================================================
unite(["gnd_bot_lpad", "gnd_top_ltap", "via_wall_bot", "via_wall_top_lpad"])
oDesktop.AddMessage("", "", 0, "All ground conductors united into gnd_bot_lpad (single ground shell)")

# ===========================================================================
# 11. SUBTRACT embedded conductors from dielectric
#     Ground is now one object — use gnd_bot_lpad for the shell
# ===========================================================================
subtract("diel",
         ["attk_pad_l",
          "gnd_pad_l",
          "vict_pad_l",
          "gnd_bot_lpad"],    # unified ground shell
         keep=True)
oDesktop.AddMessage("", "", 0, "Conductors subtracted from dielectric")

# ===========================================================================
# 12. AIRBOX
# ===========================================================================
P = AIR_PADDING
make_box("airbox", x0-P,0-P,GND_BOT_Z-P,
         TOTAL_LENGTH+2*P, TOTAL_HEIGHT+2*P, TOP_Z-GND_BOT_Z+2*P,
         "vacuum", True)

# ===========================================================================
# 13. RADIATION BOUNDARY
# ===========================================================================
try:
    oBoundarySetup.AssignRadiation(
        ["NAME:Rad1","Objects:=",["airbox"],
         "IsFssReference:=",False,"IsForPML:=",False])
    oDesktop.AddMessage("", "", 0, "Radiation boundary assigned")
except Exception as e:
    oDesktop.AddMessage("", "", 0, "Radiation error: " + str(e))

# ===========================================================================
# 14. PORT RECTANGLES
#
# All ports reference GND_BOT (the unified ground shell bottom face).
#
# Port1/3 — pin face (x=0):
#   z = GND_BOT_Z(0.0) → TOP_Z(1.7)
#   Touches: GND_BOT (ref) at z=0-0.1, pin (signal) at z=1.6-1.7  → 2 conductors ✓
#
# Port2/4 — TL end (x=x3):
#   z = GND_BOT_Z(0.0) → SL_Z+SL_THK(0.9)
#   Touches: GND_BOT (ref) at z=0-0.1, stripline (signal) at z=0.8-0.9 → 2 conductors ✓
#   GND_TOP is at z=1.6-1.7 — NOT touched by this rectangle
# ===========================================================================
TL_PORT_Z_TOP = SL_Z + SL_THK   # 0.9mm — top of stripline trace

ports = [
    ("port_rect_Port1", x0, yp_attk_bot, W_PAD, GND_BOT_Z, TOP_Z        - GND_BOT_Z),
    ("port_rect_Port3", x0, yp_vict_bot, W_PAD, GND_BOT_Z, TOP_Z        - GND_BOT_Z),
    ("port_rect_Port2", x3, yt_attk_bot, W_SL,  GND_BOT_Z, TL_PORT_Z_TOP - GND_BOT_Z),
    ("port_rect_Port4", x3, yt_vict_bot, W_SL,  GND_BOT_Z, TL_PORT_Z_TOP - GND_BOT_Z),
]
for rect_name, x, y_start, width, z_bot, z_height in ports:
    try:
        oEditor.CreateRectangle(
            ["NAME:RectangleParameters","IsCovered:=",True,
             "XStart:=",mm(x),"YStart:=",mm(y_start),"ZStart:=",mm(z_bot),
             "Width:=",mm(width),"Height:=",mm(z_height),
             "WhichAxis:=","X"],
            ["NAME:Attributes","Name:=",rect_name,
             "MaterialValue:=",'"vacuum"',"SolveInside:=",True])
        oDesktop.AddMessage("", "", 0, "Port rect: " + rect_name)
    except Exception as e:
        oDesktop.AddMessage("", "", 0, "Rect error " + rect_name + ": " + str(e))

# ===========================================================================
# 15. SOLUTION SETUP
# ===========================================================================
try:
    oAnalysisSetup.InsertSetup("HfssDriven",
        ["NAME:Setup1","Frequency:=","10GHz","MaxDeltaS:=",0.01,
         "MaximumPasses:=",20,"MinimumPasses:=",3,"MinimumConvergedPasses:=",2,
         "PercentRefinement:=",30,"IsEnabled:=",True,
         ["NAME:MeshLink","ImportMesh:=",False],
         "BasisOrder:=",1,"DoLambdaRefine:=",True,"DoMaterialLambda:=",True,
         "SaveRadFieldsOnly:=",False,"SaveAnyFields:=",True])
    oDesktop.AddMessage("", "", 0, "Adaptive: 10GHz, 20 passes, dS=0.01")
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
# 16. SAVE
# ===========================================================================
oProject.Save()
oDesktop.AddMessage("", "", 0, "=== BUILD COMPLETE ===")
oDesktop.AddMessage("", "", 0, "Structure   : pins(x=0) -> taper -> TL -> open end(x=8mm)")
oDesktop.AddMessage("", "", 0, "Pin  dims   : W_PAD=" + str(W_PAD) + "  G_PAD=" + str(G_PAD))
oDesktop.AddMessage("", "", 0, "TL   dims   : W_SL="  + str(W_SL)  + "  G_SL="  + str(G_SL))
oDesktop.AddMessage("", "", 0, "GND_TOP     : full-width x=[" + str(round(gt_x,3)) + "," + str(x3)
                              + "]  y=[0," + str(round(yt_total,3)) + "]")
oDesktop.AddMessage("", "", 0, "Ground shell : GND_BOT + GND_TOP + via walls → single object (gnd_bot_lpad)")
oDesktop.AddMessage("", "", 0, "Ports (all reference GND_BOT):")
oDesktop.AddMessage("", "", 0, "  Port1 x=0   attacker PIN  z=[0.0, 1.7]  W=" + str(W_PAD) + "  (GND_BOT -> pin top)")
oDesktop.AddMessage("", "", 0, "  Port3 x=0   victim   PIN  z=[0.0, 1.7]  W=" + str(W_PAD) + "  (GND_BOT -> pin top)")
oDesktop.AddMessage("", "", 0, "  Port2 x=8   attacker TL   z=[0.0, 0.9]  W=" + str(W_SL)  + "  (GND_BOT -> stripline top)")
oDesktop.AddMessage("", "", 0, "  Port4 x=8   victim   TL   z=[0.0, 0.9]  W=" + str(W_SL)  + "  (GND_BOT -> stripline top)")
oDesktop.AddMessage("", "", 0, "Key: dB(S(2,1))=insertion  dB(S(3,1))=NEXT  dB(S(4,1))=FEXT")
