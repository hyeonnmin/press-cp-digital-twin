"""기존 CP 원본을 보존하는 공장 실내·주변 설비 생성기. 치수는 시각 근사값."""
import json
import math

import numpy as np
from pxr import Gf, Usd, UsdGeom, UsdLux

import press_cp_environment as geo

CONFIG = geo.ROOT / "config/factory_environment.json"


def read_config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def tube(s, path, points, radius, mat, sides=16):
    """연속 중심선을 따라 굽은 호스·배관을 작성한다."""
    centers = np.asarray(points, dtype=float)
    vertices, faces = [], []
    for i, center in enumerate(centers):
        tangent = centers[min(i + 1, len(centers)-1)] - centers[max(i-1, 0)]
        tangent /= np.linalg.norm(tangent)
        axis = np.array([0, 0, 1]) if abs(tangent[2]) < .9 else np.array([0, 1, 0])
        normal = np.cross(tangent, axis); normal /= np.linalg.norm(normal)
        binormal = np.cross(tangent, normal)
        for j in range(sides):
            a = 2*math.pi*j/sides
            vertices.append(center + radius*(normal*math.cos(a)+binormal*math.sin(a)))
    for i in range(len(centers)-1):
        for j in range(sides):
            k = (j+1) % sides
            faces.append([i*sides+j, i*sides+k, (i+1)*sides+k, (i+1)*sides+j])
    faces += [list(reversed(range(sides))), list(range((len(centers)-1)*sides, len(centers)*sides))]
    return geo.mesh(s, path, vertices, [len(f) for f in faces], [v for f in faces for v in f], mat)


def wheel(s, path, center, radius, mat):
    x,y,z = center
    tube(s, path+"/Rim", [[x+radius*math.cos(a),y+radius*math.sin(a),z] for a in np.linspace(0,2*math.pi,49)], .010, mat)
    geo.cylinder(s,path+"/Hub",center,.022,.024,mat,"Z")
    for i in range(3):
        a=i*2*math.pi/3
        tube(s,path+f"/Spoke_{i}",[center,[x+radius*math.cos(a),y+radius*math.sin(a),z]],.008,mat)


def press(s, path, position, mats, scale=1.0):
    root=UsdGeom.Xform.Define(s,path)
    geo.pose(root.GetPrim(),position)
    root.AddScaleOp().Set(Gf.Vec3f(scale))
    def box(name,p,size,material="machine"):
        return geo.bevel_box(s,path+"/"+name,p,size,mats[material],.012)
    box("Base",[0,0,.11],[1.25,1.0,.42])
    box("Table",[0,-.04,.62],[1.35,1.03,.14],"steel")
    box("Crown",[0,.05,2.15],[1.35,.87,.40])
    for i,x in enumerate([-.50,.50]):
        box(f"Column_{i}",[x,.22,1.35],[.22,.57,1.5])
        geo.cylinder(s,path+f"/Guide_{i}",[x,-.23,1.33],.043,1.34,mats["steel"],"Z")
        for z in [.75,1.93]:
            geo.cylinder(s,path+f"/Collar_{i}_{int(z*100)}",[x,-.23,z],.074,.08,mats["dark"],"Z")
    box("MovingPlaten",[0,-.03,1.13],[1.03,.81,.20],"steel")
    box("Die",[0,-.13,.79],[.63,.59,.20],"dark")
    geo.cylinder(s,path+"/Cylinder",[0,.05,2.48],.19,.48,mats["machine"],"Z")
    geo.cylinder(s,path+"/Ram",[0,.05,1.62],.085,.85,mats["steel"],"Z")
    tube(s,path+"/HydraulicHose",[[.10,.3,2.5],[.37,.52,2.55],[.64,.54,2.3],[.69,.55,1.4],[.65,.5,.5]],.028,mats["dark"])


def build_workcell(scene_cfg, cfg=None):
    cfg=cfg or read_config()
    s=geo.stage("/Workcell")
    s.GetRootLayer().customLayerData={**s.GetRootLayer().customLayerData,"environment_config_sha256":geo.sha256(CONFIG),"environment_code_sha256":geo.sha256(__file__),"reference":"frame_000001.png; unseen architecture is provisional"}
    m=geo.materials(s,"/Workcell",cfg)
    room=cfg["room"]; floor=room["floor_z"]; height=room["height"]
    width=room["width"]; front=room["front_y"]; back=room["back_y"]; depth=back-front; middle=(front+back)/2
    def box(path,pos,size,mat):
        return geo.cube(s,"/Workcell/"+path,pos,size,m[mat])
    box("Floor",[0,middle,floor-.1],[width,depth,.2],"concrete")
    spacing=room["joint_spacing"]
    for i,x in enumerate(np.arange(-width/2+spacing,width/2,spacing)):
        box(f"FloorJoints/X_{i}",[x,middle,floor+.001],[.008,depth,.002],"joint")
    for i,y in enumerate(np.arange(front+spacing,back,spacing)):
        box(f"FloorJoints/Y_{i}",[0,y,floor+.001],[width,.008,.002],"joint")
    for name,y in [("Back",back),("Front",front)]:
        box(f"Building/{name}Wall",[0,y,floor+height/2],[width,.18,height],"plaster")
        box(f"Building/{name}Wainscot",[0,y+(.101 if name=="Front" else -.101),floor+.6],[width,.03,1.2],"wall_lower")
    for side,x in enumerate([-width/2,width/2]):
        box(f"Building/SideWall_{side}",[x,middle,floor+height/2],[.18,depth,height],"plaster")
        box(f"Building/SideBand_{side}",[x+(.1 if side==0 else -.1),middle,floor+.6],[.03,depth,1.2],"wall_lower")
        for i,y in enumerate([.8,3.6,6.4]):
            xx=x+(.11 if side==0 else -.11)
            box(f"Windows/Window_{side}_{i}/Frame",[xx,y,3.12],[.055,2.2,1.15],"structure")
            box(f"Windows/Window_{side}_{i}/Glass",[xx+(.033 if side==0 else -.033),y,3.12],[.018,2.07,1.02],"window")
            for j,dy in enumerate([-.7,0,.7]):
                box(f"Windows/Window_{side}_{i}/Mullion_{j}",[xx+(.05 if side==0 else -.05),y+dy,3.12],[.035,.04,1.06],"structure")
    for i,y in enumerate(room["column_y"]):
        for j,x in enumerate(room["column_x"]):
            for k,dx in enumerate([-.11,.11]):
                box(f"Structure/Column_{i}_{j}/Flange_{k}",[x+dx,y,floor+height/2],[.04,.29,height],"structure")
            box(f"Structure/Column_{i}_{j}/Web",[x,y,floor+height/2],[.22,.035,height],"structure")
            box(f"Structure/Column_{i}_{j}/Foot",[x,y,floor+.06],[.46,.46,.12],"steel")
            box(f"Structure/Column_{i}_{j}/Guard",[x,y,.35],[.27,.31,.75],"yellow")
        box(f"Structure/Beam_{i}/Web",[0,y,height-.37],[width,.06,.35],"structure")
        for k,z in enumerate([height-.54,height-.19]):
            box(f"Structure/Beam_{i}/Flange_{k}",[0,y,z],[width,.28,.04],"structure")
    box("Building/Roof",[0,middle,height+.01],[width,depth,.12],"roof")
    for i,x in enumerate(np.arange(-5.5,6,.75)):
        box(f"Structure/Purlin_{i}",[x,middle,height-.10],[.06,depth,.14],"structure")
    # 셔터문과 보행문은 사진 밖 구조를 나타내는 시각적 배경이다.
    box("Building/RollerDoor/Frame",[1.25,back-.13,1.6],[3.6,.08,3.4],"structure")
    box("Building/RollerDoor/Face",[1.25,back-.18,1.56],[3.32,.03,3.2],"roof")
    for i in range(20):
        box(f"Building/RollerDoor/Slat_{i}",[1.25,back-.205,.04+i*.16],[3.3,.014,.014],"steel")
    box("Building/PersonnelDoor",[-2,back-.15,1.0],[1.05,.08,2.2],"wall_lower")
    box("Building/PersonnelDoorHandle",[-1.65,back-.22,1.0],[.035,.07,.16],"steel")
    # 천장 케이블 트레이와 공급 배관.
    for i,x in enumerate([2.65,3.0]):
        box(f"Utilities/TraySide_{i}",[x,middle,3.55],[.035,depth-.8,.16],"steel")
    for i,y in enumerate(np.arange(front+.5,back-.3,.32)):
        box(f"Utilities/TrayRung_{i}",[2.825,y,3.49],[.35,.035,.025],"steel")
    for i,x in enumerate([-4.7,-4.4]):
        geo.cylinder(s,f"/Workcell/Utilities/Supply_{i}",[x,middle,3.8],.05,depth-.4,m["steel"],"Y")
    eq=cfg["equipment"]
    box("CabinetPlinth",[0,.16,-.04],[1.8,.42,.12],"machine")
    press(s,"/Workcell/LeftPress",eq["left_press_position"],m)
    for i,p in enumerate(eq["rear_press_positions"]):
        press(s,f"/Workcell/RearPress_{i}",p,m,1.18)
    sx,sy,_=eq["right_skid_position"]
    box("RightSkid/Base",[sx,sy,.005],[1.12,1.10,.21],"machine")
    box("RightSkid/Deck",[sx,sy,.13],[1.19,1.16,.045],"steel")
    for i,(x,y,z) in enumerate(zip(eq["pipe_x"],eq["pipe_y"],eq["valve_z"])):
        path=f"/Workcell/Pipe_{i}"
        geo.cylinder(s,path+"/Riser",[x,y,.73],eq["pipe_radius"],1.15,m["machine"],"Z")
        for j,zz in enumerate([.26,.59,1.04]):
            geo.cylinder(s,path+f"/Flange_{j}",[x,y,zz],eq["flange_radius"],.065,m["steel"],"Z")
            geo.cylinder(s,path+f"/Gasket_{j}",[x,y,zz],eq["flange_radius"]*1.015,.008,m["dark"],"Z")
            for k in range(8):
                a=math.pi*k/4
                geo.cylinder(s,path+f"/Bolt_{j}_{k}",[x+.087*math.cos(a),y+.087*math.sin(a),zz+.044],.010,.027,m["dark"],"Z")
        geo.cylinder(s,path+"/Valve",[x,y,z],.091,.21,m["green"],"X")
        geo.cylinder(s,path+"/Stem",[x,y,z+.11],.017,.16,m["steel"],"Z")
        wheel(s,path+"/Handwheel",[x,y,z+.20],.125,m["wheel"])
        # 완만한 하부 엘보, 전방 분기와 후방 공급 연결.
        pts=[[x,y,.40]]+[[x,y-.15+.15*math.cos(a),.28-.15*math.sin(a)] for a in np.linspace(0,math.pi/2,9)]+[[x,y-.42,.13]]
        tube(s,path+"/LowerElbow",pts,.047,m["steel"])
        tube(s,path+"/RearSupply",[[x,y,z],[x,y+.12,z],[x,y+.32,z-.08],[x,y+.48,z-.27],[x,y+.48,.22]],.038,m["machine"])
        geo.cylinder(s,path+"/SidePort",[x,y-.075,.83],.043,.15,m["dark"],"Y")
    lx,ly,_=eq["left_service_position"]
    box("LeftMachine/Base",[lx,ly,.19],[.58,.65,.56],"machine")
    box("LeftMachine/Top",[lx,ly,.50],[.65,.72,.07],"steel")
    for i in range(3):
        x=lx-.19+i*.18
        tube(s,f"/Workcell/LeftMachine/Pipe_{i}",[[x,ly+.1,.54],[x,ly+.1,.85],[x,ly+.09,1.05],[x,ly+.02,1.13],[x,ly-.12,1.16],[x,ly-.25,1.12],[x,ly-.29,1.03],[x,ly-.29,.76]],.025,m["steel"])
        geo.cylinder(s,f"/Workcell/LeftMachine/Coupling_{i}",[x,ly+.1,.72],.04,.065,m["dark"],"Z")
    wheel(s,"/Workcell/LeftMachine/Handwheel",[lx,ly+.1,1.23],.115,m["dark"])
    # 작업 통로: CP 전면을 가리지 않는 바닥 표시.
    walk=cfg["walkway"]
    for i,y in enumerate([walk["front_y"],walk["back_y"]]):
        box(f"Walkway/Line_{i}",[0,y,floor+.004],[2*walk["half_width"],walk["line_width"],.006],"yellow")
    for i,x in enumerate([-walk["half_width"],walk["half_width"]]):
        box(f"Walkway/End_{i}",[x,(walk["front_y"]+walk["back_y"])/2,floor+.004],[walk["line_width"],walk["front_y"]-walk["back_y"],.006],"yellow")
    light=cfg["lighting"]
    for i,x in enumerate(light["x"]):
        for j,y in enumerate(light["y"]):
            path=f"/Workcell/CeilingLights/Fixture_{i}_{j}"
            geo.cube(s,path+"/Housing",[x,y,light["z"]+.04],[light["width"]+.1,light["height"]+.1,.09],m["structure"])
            geo.cube(s,path+"/Diffuser",[x,y,light["z"]-.015],[light["width"],light["height"],.015],m["diffuser"])
            for k,dx in enumerate([-.45,.45]):
                geo.cylinder(s,path+f"/Suspension_{k}",[x+dx,y,(height+light["z"])/2],.007,height-light["z"],m["steel"],"Z")
            lamp=UsdLux.RectLight.Define(s,path+"/Light")
            geo.pose(lamp.GetPrim(),[x,y,light["z"]-.026])
            lamp.CreateWidthAttr(light["width"]); lamp.CreateHeightAttr(light["height"])
            lamp.CreateIntensityAttr(light["intensity"])
            lamp.CreateEnableColorTemperatureAttr(True); lamp.CreateColorTemperatureAttr(light["temperature"])
    fill=light["window_fill"]
    for i,x in enumerate(fill["x"]):
        for j,y in enumerate(fill["y"]):
            lamp=UsdLux.RectLight.Define(s,f"/Workcell/WindowLights/Fill_{i}_{j}")
            geo.aim(lamp.GetPrim(),{"position":[x,y,fill["z"]],"target":[0,y,1.0]})
            lamp.CreateWidthAttr(fill["width"]); lamp.CreateHeightAttr(fill["height"])
            lamp.CreateIntensityAttr(fill["intensity"])
            lamp.CreateEnableColorTemperatureAttr(True); lamp.CreateColorTemperatureAttr(fill["temperature"])
    geo.save(s,geo.ENVIRONMENT)
    return cfg


def configure_scene(s, cfg=None):
    cfg=cfg or read_config()
    for name,setting in cfg["cameras"].items():
        path=f"/World/Cameras/{name}"
        camera=UsdGeom.Camera.Define(s,path)
        camera.ClearXformOpOrder()
        # 재실행 때 기존 transform 속성을 재사용한다.
        matrix=Gf.Matrix4d().SetLookAt(Gf.Vec3d(*setting["position"]),Gf.Vec3d(*setting["target"]),Gf.Vec3d(0,0,1)).GetInverse()
        camera.AddTransformOp().Set(matrix)
        camera.CreateProjectionAttr("perspective")
        camera.CreateHorizontalApertureAttr(36); camera.CreateVerticalApertureAttr(20.25)
        camera.CreateFocalLengthAttr(setting["focal_mm"]); camera.CreateClippingRangeAttr(Gf.Vec2f(.01,100))
    data=dict(s.GetRootLayer().customLayerData)
    camera_settings=dict(data.get("cameraSettings",{}))
    camera_settings["boundCamera"]="/World/Cameras/"+cfg["default_camera"]
    data.update({"cameraSettings":camera_settings,"factory_environment_config_sha256":geo.sha256(CONFIG)})
    s.GetRootLayer().customLayerData=data


def update():
    """패널·텍스처를 재생성하지 않고 환경 Asset과 추가 카메라만 저장한다."""
    cfg=build_workcell(geo.read_config())
    s=Usd.Stage.Open(str(geo.SCENE))
    configure_scene(s,cfg)
    s.GetRootLayer().Save()
    geo.SCENE.write_text(geo.SCENE.read_text(encoding="utf-8").rstrip()+"\n",encoding="utf-8")
    return cfg
