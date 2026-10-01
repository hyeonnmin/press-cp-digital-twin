"""CP 영상 기반 7개 그룹의 편집 가능한 3D Base Scene 생성."""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, UsdShade
import cp_label_textures

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/press_cp_scene.json"
ASSET = ROOT / "isaac_sim/assets/cp_panel/press_cp_cabinet.usda"
ENVIRONMENT = ROOT / "isaac_sim/assets/environment/workcell.usda"
SCENE = ROOT / "isaac_sim/stages/press_cp_main.usda"
GENERATOR = "press-cp/full-environment/v1"
MODULES = ["temperature", "pressure", "vacuum"]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_config():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    if [p["id"] for p in cfg["panels"]] != [f"panel_{i}" for i in range(1,8)]:
        raise ValueError("Panel ID 1~7이 필요합니다.")
    for p in cfg["panels"]:
        if [m["id"] for m in p["modules"]] != MODULES:
            raise ValueError("Module 구성 오류")
        for m in p["modules"]:
            if len(m["text"]) != 2 or any(not isinstance(t,str) or not t or any(c not in "0123456789.-" for c in t) for t in m["text"]):
                raise ValueError("두 Slot의 숫자 문자열을 확인하세요.")
    return cfg


def stage(root):
    s = Usd.Stage.CreateInMemory()
    UsdGeom.SetStageUpAxis(s, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(s, 1)
    s.SetDefaultPrim(UsdGeom.Xform.Define(s,root).GetPrim())
    s.GetRootLayer().customLayerData={"generator":GENERATOR,"config_sha256":sha256(CONFIG),"code_sha256":sha256(__file__),"dimension_status":"provisional_not_measured","reference":"IMG_2631.MOV @ 4 s","dataset_status":"not_training_data"}
    return s


def save(s,path):
    if path.exists():
        layer=Sdf.Layer.FindOrOpen(str(path))
        if layer.customLayerData.get("generator") != GENERATOR:
            raise FileExistsError(f"생성기 소유 파일이 아님: {path}")
    path.parent.mkdir(parents=True,exist_ok=True)
    if not s.GetRootLayer().Export(str(path)):
        raise RuntimeError(f"저장 실패: {path}")
    layer=Sdf.Layer.Find(str(path))
    if layer: layer.Reload()


def camera_basis(settings):
    c=np.array(settings["position"],dtype=float)
    f=np.array(settings["target"],dtype=float)-c; f/=np.linalg.norm(f)
    r=np.cross(f,[0,0,1]); r/=np.linalg.norm(r)
    u=np.cross(r,f)
    return c,f,r,u


def image_point(cfg,x,y,depth=0):
    c,f,r,u=camera_basis(cfg["camera"]["reference"])
    w,h=cfg["camera"]["resolution"]; focal=cfg["camera"]["focal_px"]
    ray=f+r*(x-w/2)/focal-u*(y-h/2)/focal
    return c+ray*(depth-c[1])/ray[1]


def image_box(cfg,bbox,depth=0):
    l,t,r,b=bbox
    center=image_point(cfg,(l+r)/2,(t+b)/2,depth)
    width=image_point(cfg,r,(t+b)/2,depth)[0]-image_point(cfg,l,(t+b)/2,depth)[0]
    height=image_point(cfg,(l+r)/2,t,depth)[2]-image_point(cfg,(l+r)/2,b,depth)[2]
    return center,float(width),float(height)


def pose(prim,position):
    UsdGeom.Xformable(prim).AddTranslateOp().Set(Gf.Vec3d(*[float(v) for v in position]))


def bind(prim,mat):
    UsdShade.MaterialBindingAPI.Apply(prim).Bind(mat)
    return prim


def cube(s,path,position,size,mat):
    c=UsdGeom.Cube.Define(s,path); c.CreateSizeAttr(1)
    pose(c.GetPrim(),position)
    c.AddScaleOp().Set(Gf.Vec3f(*[float(v) for v in size]))
    return bind(c.GetPrim(),mat)


def mesh(s,path,points,counts,indices,mat):
    m=UsdGeom.Mesh.Define(s,path)
    m.CreatePointsAttr([Gf.Vec3f(*[float(v) for v in p]) for p in points])
    m.CreateFaceVertexCountsAttr(counts); m.CreateFaceVertexIndicesAttr(indices)
    m.CreateSubdivisionSchemeAttr("none"); m.CreateDoubleSidedAttr(True)
    bind(m.GetPrim(),mat)
    return m


def bevel_box(s,path,position,size,mat,bevel=0.002):
    w,d,h=size; b=min(bevel,w/8,h/8,d/3)
    pts=[]
    for y,inset in [(-d/2,b),(-d/2+b,0),(d/2,0)]:
        x=w/2-inset; z=h/2-inset
        pts.extend([[-x,y,-z],[x,y,-z],[x,y,z],[-x,y,z]])
    faces=[[0,1,2,3],[11,10,9,8]]
    for ring in [0,4]:
        faces.extend([[ring+i,ring+(i+1)%4,ring+4+(i+1)%4,ring+4+i] for i in range(4)])
    m=mesh(s,path,pts,[4]*len(faces),[i for face in faces for i in face],mat)
    pose(m.GetPrim(),position)
    return m.GetPrim()


def cylinder(s,path,pos,radius,height,mat,axis="Y"):
    # 원형 버튼·배관에 거친 기본 프리미티브 테셀레이션 대신 48분할 Mesh 사용.
    n=48;points=[];normals=[];counts=[];indices=[]
    def oriented(x,y,z):
        return [x,y,z] if axis=="Y" else [x,z,y] if axis=="Z" else [y,x,z]
    for y in [-height/2,height/2]:
        for i in range(n):
            a=2*math.pi*i/n;points.append(oriented(radius*math.cos(a),y,radius*math.sin(a)))
    for i in range(n):
        j=(i+1)%n;indices.extend([i,n+i,n+j,j]);counts.append(4)
        for k in [i,i,j,j]:
            a=2*math.pi*k/n;normals.append(oriented(math.cos(a),0,math.sin(a)))
    indices.extend(range(n));counts.append(n);normals.extend([oriented(0,-1,0)]*n)
    indices.extend(reversed(range(n,2*n)));counts.append(n);normals.extend([oriented(0,1,0)]*n)
    if axis!="Y":
        offset=0
        for count in counts:
            indices[offset:offset+count]=reversed(indices[offset:offset+count])
            normals[offset:offset+count]=reversed(normals[offset:offset+count])
            offset+=count
    c=mesh(s,path,points,counts,indices,mat)
    c.CreateNormalsAttr(normals);c.SetNormalsInterpolation(UsdGeom.Tokens.faceVarying)
    pose(c.GetPrim(),pos)
    return c.GetPrim()


def materials(s,root,cfg):
    mats={}
    for name,entry in cfg["materials"].items():
        mat=UsdShade.Material.Define(s,f"{root}/Looks/{name}")
        sh=UsdShade.Shader.Define(s,f"{mat.GetPath()}/Surface"); sh.CreateIdAttr("UsdPreviewSurface")
        sh.CreateInput("diffuseColor",Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*entry["color"]))
        sh.CreateInput("roughness",Sdf.ValueTypeNames.Float).Set(entry.get("roughness",0.5))
        sh.CreateInput("metallic",Sdf.ValueTypeNames.Float).Set(entry.get("metallic",0))
        if "opacity" in entry: sh.CreateInput("opacity",Sdf.ValueTypeNames.Float).Set(entry["opacity"])
        if "emission" in entry: sh.CreateInput("emissiveColor",Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*entry["emission"]))
        if "emission_color" in entry:
            intensity = entry["emission_intensity"]
            if intensity < 0 or not math.isfinite(intensity):
                raise ValueError(f"발광 세기 오류: {name}")
            emission = [float(v) * intensity for v in entry["emission_color"]]
            sh.CreateInput("emissiveColor",Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*emission))
        mat.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(),"surface"); mats[name]=mat
    return mats


def texture_material(s,name,emissive=False):
    path=f"/Cabinet/Looks/Texture_{name}"
    existing=UsdShade.Material.Get(s,path)
    if existing: return existing
    mat=UsdShade.Material.Define(s,path)
    sh=UsdShade.Shader.Define(s,path+"/Surface"); sh.CreateIdAttr("UsdPreviewSurface")
    sh.CreateInput("roughness",Sdf.ValueTypeNames.Float).Set(0.65)
    tex=UsdShade.Shader.Define(s,path+"/Image"); tex.CreateIdAttr("UsdUVTexture")
    tex.CreateInput("file",Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath(f"textures/{name}.png"))
    tex.CreateInput("sourceColorSpace",Sdf.ValueTypeNames.Token).Set("sRGB")
    tex.CreateOutput("rgb",Sdf.ValueTypeNames.Float3)
    st=UsdShade.Shader.Define(s,path+"/UV"); st.CreateIdAttr("UsdPrimvarReader_float2")
    st.CreateInput("varname",Sdf.ValueTypeNames.String).Set("st"); st.CreateOutput("result",Sdf.ValueTypeNames.Float2)
    tex.CreateInput("st",Sdf.ValueTypeNames.Float2).ConnectToSource(st.ConnectableAPI(),"result")
    sh.CreateInput("diffuseColor",Sdf.ValueTypeNames.Color3f).ConnectToSource(tex.ConnectableAPI(),"rgb")
    if emissive: sh.CreateInput("emissiveColor",Sdf.ValueTypeNames.Color3f).ConnectToSource(tex.ConnectableAPI(),"rgb")
    mat.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(),"surface")
    return mat


def label(s,path,center,w,h,name,emissive=False):
    m=mesh(s,path,[[-w/2,0,-h/2],[w/2,0,-h/2],[w/2,0,h/2],[-w/2,0,h/2]],[4],[0,1,2,3],texture_material(s,name,emissive))
    UsdGeom.PrimvarsAPI(m).CreatePrimvar("st",Sdf.ValueTypeNames.TexCoord2fArray,UsdGeom.Tokens.vertex).Set([(0,0),(1,0),(1,1),(0,1)])
    pose(m.GetPrim(),center)


def image_label(s,path,cfg,bbox,name,depth=-0.002,emissive=False):
    c,w,h=image_box(cfg,bbox,depth); label(s,path,c,w,h,name,emissive)


SEGMENTS={"0":"abcdef","1":"bc","2":"abged","3":"abgcd","4":"fgbc","5":"afgcd","6":"afgecd","7":"abc","8":"abcdefg","9":"abfgcd","-":"g"," ":""}


def digits(s,path,text,center,width,height,on_mat,off_mat):
    """각 숫자·소수점을 Mesh로 만든다. 텍스처에 숫자를 굽지 않는다."""
    root=UsdGeom.Xform.Define(s,path).GetPrim(); pose(root,center)
    root.SetCustomDataByKey("display_text",text)
    root.SetCustomDataByKey("text_status","provisional_visual_example")
    step=0.68; units=sum(0.24 if c=="." else step for c in text)
    unit=min(height,width/max(units,0.1)); x=width/2-units*unit
    on_pts=[];on_counts=[];on_idx=[];off_pts=[];off_counts=[];off_idx=[]

    def polygon(poly,lit):
        # 모든 세그먼트 면의 정면을 -Y로 통일한다.
        if sum(poly[i][0]*poly[(i+1)%len(poly)][1]-poly[(i+1)%len(poly)][0]*poly[i][1] for i in range(len(poly))) < 0:
            poly=list(reversed(poly))
        pts,counts,indices=(on_pts,on_counts,on_idx) if lit else (off_pts,off_counts,off_idx)
        start=len(pts); pts.extend([[x+(px+0.06*pz)*unit,0,(pz-0.5)*unit] for px,pz in poly]); counts.append(len(poly)); indices.extend(range(start,start+len(poly)))

    def horizontal(z): return [(0.09,z),(0.16,z+0.05),(0.48,z+0.05),(0.54,z),(0.48,z-0.05),(0.16,z-0.05)]
    def vertical(xx,z): return [(xx,z-0.19),(xx+0.05,z-0.14),(xx+0.05,z+0.14),(xx,z+0.19),(xx-0.05,z+0.14),(xx-0.05,z-0.14)]
    polys={"a":horizontal(.94),"g":horizontal(.50),"d":horizontal(.06),"f":vertical(.09,.72),"b":vertical(.54,.72),"e":vertical(.09,.28),"c":vertical(.54,.28)}
    for char in text:
        if char==".":
            polygon([(0.025,0.02),(0.125,0.02),(0.125,0.12),(0.025,0.12)],True); x+=.24*unit
        else:
            for seg,poly in polys.items(): polygon(poly,seg in SEGMENTS[char])
            x+=step*unit
    if on_pts: mesh(s,path+"/Lit",on_pts,on_counts,on_idx,on_mat)
    if off_pts: mesh(s,path+"/Unlit",off_pts,off_counts,off_idx,off_mat)
    return root


def module(s,path,cfg,entry,mats,panel_id):
    root=UsdGeom.Xform.Define(s,path).GetPrim(); root.SetCustomDataByKey("module_id",entry["id"])
    c,w,h=image_box(cfg,entry["bbox"],-0.026)
    root.SetCustomDataByKey("reference_bbox",Gf.Vec4i(*entry["bbox"]))
    d=cfg["cabinet"]["module_depth"]
    bevel_box(s,path+"/Housing",[c[0],-d/2,c[2]],[w,d,h],mats["black"])
    bevel_box(s,path+"/Face",[c[0],-d-0.001,c[2]],[w*.94,.004,h*.94],mats["screen"],.001)
    vac=entry["id"]=="vacuum"; display=cfg["display"]
    for i,text in enumerate(entry["text"]):
        cx=c[0]+((display["vacuum_main_x"] if vac else display["main_x"])-.5)*w
        cz=c[2]+(.5-display["slot_y"][i])*h
        sw=w*(display["vacuum_main_width"] if vac else display["main_width"])
        dh=h*(display["vacuum_digit_height"] if vac else display["digit_height"])
        slot=digits(s,f"{path}/slot_{i+1}",text,[cx,-d-.004,cz],sw,dh,mats["green_led" if i==0 else "amber_led"],mats["off_segment"])
        slot.SetCustomDataByKey("slot_id",f"{panel_id}/{entry['id']}/slot_{i+1}")
    if not vac:
        digits(s,path+"/Auxiliary","1 6" if entry["id"]=="temperature" else "1 4",[c[0]-.22*w,-d-.004,c[2]+.34*h],w*.30,h*.071,mats["green_led"],mats["off_segment"])
        digits(s,path+"/AuxiliaryLower","--",[c[0]-.21*w,-d-.004,c[2]+.18*h],w*.22,h*.055,mats["amber_led"],mats["off_segment"])
        label(s,path+"/Legend",[c[0],-d-.004,c[2]-.05*h],w*.83,h*.16,"instrument")
        label(s,path+"/KeyLegend",[c[0],-d-.004,c[2]-.37*h],w*.87,h*.10,"keys")
        for k in range(4): bevel_box(s,f"{path}/Key_{k}",[c[0]+(k-1.5)*w*.2,-d-.007,c[2]-.24*h],[w*.12,.006,h*.06],mats["button_black"],.0007)
    else:
        cube(s,path+"/Controls",[c[0],-d-.003,c[2]-.28*h],[w*.91,.006,h*.36],mats["ivory"])
        for k,(xx,zz) in enumerate([(-.27,-.2),(.27,-.2),(-.27,-.36),(.27,-.36)]):
            cylinder(s,f"{path}/Key_{k}",[c[0]+xx*w,-d-.009,c[2]+zz*h],w*.085,.005,mats["button_black"])
        for k in range(2): cylinder(s,f"{path}/Indicator_{k}",[c[0]+(k-.5)*w*.12,-d-.005,c[2]-.015*h],w*.017,.001,mats["red_led"])
    l,t,r,b=entry["bbox"]
    image_label(s,path+"/Nameplate",cfg,[l+10,t-24,r-3,t-3],entry["id"])


def stop_button(s,path,cfg,p,mats):
    px,py=p["stop_center"]; rad=p["stop_radius_px"]
    c,w,h=image_box(cfg,[px-rad,py-rad,px+rad,py+rad],-.015)
    cylinder(s,path+"/Mount",c,w/2,.008,mats["silver"])
    cylinder(s,path+"/Ring",[c[0],-.024,c[2]],w*.44,.014,mats["ivory"])
    cylinder(s,path+"/Collar",[c[0],-.036,c[2]],w*.30,.017,mats["silver"])
    cylinder(s,path+"/Mushroom",[c[0],-.05,c[2]],w*.26,.026,mats["red"])
    # 흰색 회전 안내 표시: 두 개의 반원 호.
    pts=[]; counts=[];idx=[]
    for start in [0.25,math.pi+.25]:
        for j in range(15):
            a=start+j*.10;b=a+.1; radius=w*.19; thick=w*.015
            poly=[[c[0]+rr*math.cos(t),-.064,c[2]+rr*math.sin(t)] for rr,t in [(radius-thick,a),(radius+thick,a),(radius+thick,b),(radius-thick,b)]]
            n=len(pts);pts.extend(poly);counts.append(4);idx.extend(range(n,n+4))
    mesh(s,path+"/TurnMark",pts,counts,idx,mats["ivory"])
    plug=image_point(cfg,px,py-rad*1.8,-.006)
    cylinder(s,path+"/BlankPlug",plug,w*.21,.006,mats["button_black"])


def cabinet(cfg):
    s=stage("/Cabinet"); mats=materials(s,"/Cabinet",cfg); cc=cfg["cabinet"]
    w=cc["width"]; h=cc["top"]-cc["bottom"]; z=(cc["top"]+cc["bottom"])/2
    bevel_box(s,"/Cabinet/Body",[0,cc["depth"]/2+.013,z],[w+.018,cc["depth"],h+.02],mats["cabinet_side"],.009)
    for name,left,right in [("LeftDoor",-w/2,cc["seam_x"]-cc["door_gap"]/2),("RightDoor",cc["seam_x"]+cc["door_gap"]/2,w/2)]:
        bevel_box(s,f"/Cabinet/{name}",[(left+right)/2,.012,z],[right-left,.024,h],mats["enamel"],.004)
    for p in cfg["panels"]:
        path=f"/Cabinet/Panels/{p['id']}"
        root=UsdGeom.Xform.Define(s,path).GetPrim();root.SetCustomDataByKey("panel_id",p["id"]);root.SetCustomDataByKey("door",p["door"])
        for entry in p["modules"]: module(s,f"{path}/{entry['id']}",cfg,entry,mats,p["id"])
        if p["label_bbox"]: image_label(s,path+"/HPLabel",cfg,p["label_bbox"],f"hp_{p['number']}")
        image_label(s,path+"/Number",cfg,p["number_bbox"],f"number_{p['number']}")
        stop_button(s,path+"/Stop",cfg,p,mats)
    f=cfg["fittings"]
    c,hw,hh=image_box(cfg,f["hmi_bbox"],-.03)
    bevel_box(s,"/Cabinet/HMI/Bezel",c,[hw,.047,hh],mats["silver"],.007)
    c2,sw,sh=image_box(cfg,f["hmi_screen_bbox"],-.056)
    cube(s,"/Cabinet/HMI/InnerBezel",c2,[sw+.012,.004,sh+.012],mats["black"])
    image_label(s,"/Cabinet/HMI/Screen",cfg,f["hmi_screen_bbox"],"hmi",-.06,True)
    image_label(s,"/Cabinet/OperationLabel",cfg,f["operation_label_bbox"],"operation")
    image_label(s,"/Cabinet/SafetyNotice",cfg,f["safety_bbox"],"safety")
    image_label(s,"/Cabinet/MachinePlate",cfg,f["machine_label_bbox"],"machine")
    image_label(s,"/Cabinet/InspectionSheet",cfg,f["inspection_bbox"],"inspection")
    c,cw,ch=image_box(cfg,f["green_cover_bbox"],-.055)
    bevel_box(s,"/Cabinet/GreenCover",[c[0],-.04,c[2]],[cw,.03,ch],mats["green"],.005)
    label(s,"/Cabinet/CoverLabel",[c[0],-.056,c[2]],cw*.64,ch*.22,"cover")
    for i,bbox in enumerate(f["handles"]):
        c,hw,hh=image_box(cfg,bbox,-.02)
        bevel_box(s,f"/Cabinet/Handle_{i}/Mount",c,[hw,.025,hh],mats["black"],.005)
        bevel_box(s,f"/Cabinet/Handle_{i}/Grip",[c[0],-.044,c[2]],[hw*.48,.034,hh*.72],mats["silver"],.006)
    image_label(s,"/Cabinet/LoaderLabel",cfg,f["loader_label_bbox"],"loader")
    for i,(px,py) in enumerate(f["loader_buttons"]):
        c=image_point(cfg,px,py,-.016); radius=.022 if i!=9 else .040
        cylinder(s,f"/Cabinet/Loader/Button_{i}/Mount",c,radius,.012,mats["silver"])
        mat="amber_led" if i==5 else "red" if i>=6 else "button_black"
        cylinder(s,f"/Cabinet/Loader/Button_{i}/Cap",[c[0],-.032,c[2]],radius*.7,.024,mats[mat])
    for i in range(3):
        for side in [-1,1]:
            bevel_box(s,f"/Cabinet/Hinge_{side+1}_{i}",[side*(w/2-.009),.005,.28+i*.47],[.026,.039,.08],mats["silver"],.003)
    save(s,ASSET)


def workcell(cfg):
    s=stage("/Workcell");m=materials(s,"/Workcell",cfg);e=cfg["environment"]
    cube(s,"/Workcell/Floor",[0,0,e["floor_z"]-.06],[6,6,.12],m["floor"])
    cube(s,"/Workcell/Wall",[0,e["wall_y"],1.3],[6,.12,2.8],m["wall"])
    cube(s,"/Workcell/CabinetPlinth",[0,.16,-.04],[1.8,.42,.12],m["machine"])
    for i,x in enumerate(e["pipe_x"]):
        y=e["pipe_y"]+i*.08
        cylinder(s,f"/Workcell/Pipe_{i}/Riser",[x,y,.66],.075,1.4,m["machine"],"Z")
        for j,z in enumerate([.15,.48,.95]):
            cylinder(s,f"/Workcell/Pipe_{i}/Flange_{j}",[x,y,z],.115,.045,m["silver"],"Z")
            for k in range(8):
                a=k*math.pi/4
                cylinder(s,f"/Workcell/Pipe_{i}/Bolt_{j}_{k}",[x+.093*math.cos(a),y+.093*math.sin(a),z+.028],.010,.018,m["black"],"Z")
        cylinder(s,f"/Workcell/Pipe_{i}/Valve",[x,y,e["valve_z"][i]],.095,.20,m["pipe_green"],"X")
        cylinder(s,f"/Workcell/Pipe_{i}/Stem",[x,y,e["valve_z"][i]+.13],.015,.16,m["silver"],"Z")
        z=e["valve_z"][i]+.215
        # 수평 밸브 휠: 튜브 대신 원주를 Mesh로 작성한다.
        pts=[];faces=[]
        for j in range(48):
            a=2*math.pi*j/48
            for rr in [.105,.119]: pts.append([x+rr*math.cos(a),y+rr*math.sin(a),z])
        for j in range(48): faces.append([2*j,2*j+1,(2*(j+1)+1)%96,2*(j+1)%96])
        mesh(s,f"/Workcell/Pipe_{i}/Wheel",pts,[4]*48,[v for f in faces for v in f],m["valve_blue"])
        cube(s,f"/Workcell/Pipe_{i}/SpokeX",[x,y,z],[.22,.012,.012],m["valve_blue"])
        cube(s,f"/Workcell/Pipe_{i}/SpokeY",[x,y,z],[.012,.22,.012],m["valve_blue"])
    cube(s,"/Workcell/LeftMachine/Base",[-1.22,.04,.22],[.49,.65,.58],m["machine"])
    cube(s,"/Workcell/LeftMachine/Top",[-1.19,.03,.57],[.6,.69,.065],m["silver"])
    for i in range(3):
        cylinder(s,f"/Workcell/LeftMachine/Riser_{i}",[-1.37+i*.14,.17,.94],.027,.65,m["silver"],"Z")
        cylinder(s,f"/Workcell/LeftMachine/Cross_{i}",[-1.37+i*.14,0,1.24],.027,.35,m["black"],"Y")
    save(s,ENVIRONMENT)


def aim(prim,settings):
    c=Gf.Vec3d(*settings["position"]); t=Gf.Vec3d(*settings["target"])
    matrix=Gf.Matrix4d().SetLookAt(c,t,Gf.Vec3d(0,0,1)).GetInverse()
    UsdGeom.Xformable(prim).AddTransformOp().Set(matrix)


def author_render_settings(s,cfg):
    """Kit 저장 시 생략되는 기본값까지 명시해 다른 앱 세션에서 재현한다."""
    layer=s.GetRootLayer()
    data=dict(layer.customLayerData)
    settings=dict(data.get("renderSettings",{}))
    settings.update({key.lstrip("/").replace("/", ":"): Gf.Vec3d(*value) if isinstance(value,list) else value for key,value in cfg["rendering"]["settings"].items()})
    data["renderSettings"]=settings
    layer.customLayerData=data


def build():
    cfg=read_config(); cp_label_textures.generate(); cabinet(cfg); workcell(cfg)
    s=stage("/World");save(s,SCENE);s=Usd.Stage.Open(str(SCENE))
    playback=UsdGeom.Scope.Define(s,"/World/DisplayPlayback").GetPrim()
    playback.SetMetadata("apiSchemas",Sdf.TokenListOp.Create(prependedItems=["OmniScriptingAPI"]))
    playback.CreateAttribute("omni:scripting:scripts",Sdf.ValueTypeNames.AssetArray).Set([Sdf.AssetPath("../scripts/press_cp_play_behavior.py")])
    s.SetStartTimeCode(0);s.SetEndTimeCode(60000);s.SetTimeCodesPerSecond(60)
    for name,path in [("Cabinet","../assets/cp_panel/press_cp_cabinet.usda"),("Workcell","../assets/environment/workcell.usda")]:
        UsdGeom.Xform.Define(s,f"/World/{name}").GetPrim().GetReferences().AddReference(path)
    for name in ["reference","overview","detail"]:
        cam=UsdGeom.Camera.Define(s,f"/World/Cameras/{name}"); cam.CreateProjectionAttr("perspective")
        cam.CreateHorizontalApertureAttr(36);cam.CreateVerticalApertureAttr(20.25)
        focal=cfg["camera"]["focal_px"]*36/cfg["camera"]["resolution"][0] if name=="reference" else cfg["camera"][name]["focal_mm"]
        cam.CreateFocalLengthAttr(focal);cam.CreateClippingRangeAttr(Gf.Vec2f(.01,100));aim(cam.GetPrim(),cfg["camera"][name])
    light=UsdLux.DomeLight.Define(s,"/World/Lights/Ambient");light.CreateIntensityAttr(cfg["lighting"]["dome_intensity"])
    for name in ["key","fill"]:
        e=cfg["lighting"][name];l=UsdLux.RectLight.Define(s,f"/World/Lights/{name}")
        l.CreateIntensityAttr(e["intensity"]);l.CreateWidthAttr(e["width"]);l.CreateHeightAttr(e["height"]);aim(l.GetPrim(),e)
    # Kit이 USD 파일을 직접 열 때도 동일한 Bloom 설정을 복원한다.
    from training_camera import configure as configure_training_camera
    configure_training_camera(s,json.loads((ROOT/"config/training_capture.json").read_text(encoding="utf-8"))["camera"])
    s.GetRootLayer().customLayerData={**s.GetRootLayer().customLayerData,"cameraSettings":{"boundCamera":"/World/Cameras/training"}}
    author_render_settings(s,cfg)
    save(s,SCENE)
    return cfg


def validate(s,cfg):
    if UsdGeom.GetStageUpAxis(s)!="Z" or UsdGeom.GetStageMetersPerUnit(s)!=1:
        raise AssertionError("축·단위 오류")
    panels=[p for p in s.Traverse() if p.GetCustomDataByKey("panel_id")]
    modules=[p for p in s.Traverse() if p.GetCustomDataByKey("module_id")]
    slots=[p for p in s.Traverse() if p.GetCustomDataByKey("slot_id")]
    if (len(panels),len(modules),len(slots))!=(7,21,42): raise AssertionError("7 Panel / 21 Module / 42 Slot 구성 오류")
    ids=[p.GetCustomDataByKey("slot_id") for p in slots]
    if len(set(ids))!=42: raise AssertionError("Slot ID 중복")
    for slot in slots:
        lit=s.GetPrimAtPath(str(slot.GetPath())+"/Lit")
        material,_=UsdShade.MaterialBindingAPI(lit).ComputeBoundMaterial()
        shader=UsdShade.Shader(s.GetPrimAtPath(str(material.GetPath())+"/Surface"))
        value=shader.GetInput("emissiveColor").Get()
        name="green_led" if slot.GetName()=="slot_1" else "amber_led"
        entry=cfg["materials"][name]
        expected=[v*entry["emission_intensity"] for v in entry["emission_color"]]
        if value is None or any(abs(a-b)>1e-5 for a,b in zip(value,expected)):
            raise AssertionError(f"LED 발광 재질 오류: {slot.GetPath()}")
    saved_settings=s.GetRootLayer().customLayerData.get("renderSettings",{})
    for key,value in cfg["rendering"]["settings"].items():
        stored=saved_settings.get(key.lstrip("/").replace("/",":"))
        if isinstance(value,list):
            if stored is None or any(abs(a-b)>1e-5 for a,b in zip(stored,value)): raise AssertionError(f"렌더 설정 저장 오류: {key}")
        elif stored!=value: raise AssertionError(f"렌더 설정 저장 오류: {key}")
    xf=UsdGeom.XformCache(); centers=[]; projection_errors=[]
    camera=UsdGeom.Camera(s.GetPrimAtPath("/World/Cameras/reference")).GetCamera(Usd.TimeCode.Default())
    viewproj=camera.frustum.ComputeViewMatrix()*camera.frustum.ComputeProjectionMatrix()
    for panel in cfg["panels"]:
        row=[]
        for mod in panel["modules"]:
            path=f"/World/Cabinet/Panels/{panel['id']}/{mod['id']}"
            b=s.GetPrimAtPath(path+"/Housing"); world=xf.GetLocalToWorldTransform(b).ExtractTranslation();row.append(world)
            slot_z=[]
            for i,text in enumerate(mod["text"]):
                p=s.GetPrimAtPath(f"{path}/slot_{i+1}")
                if p.GetCustomDataByKey("display_text")!=text: raise AssertionError("표시 문자열 불일치")
                slot_z.append(xf.GetLocalToWorldTransform(p).ExtractTranslation()[2])
            if slot_z[0]<=slot_z[1]: raise AssertionError("위·아래 Slot 역전")
            # 배치에 사용한 기준점과 실제 USD 카메라의 투영 규약 일치 검사.
            c,_,_=image_box(cfg,mod["bbox"],-.026)
            ndc=viewproj.Transform(Gf.Vec3d(*c)); px=(ndc[0]+1)*960;py=(1-ndc[1])*540
            bbox=mod["bbox"];expected=[(bbox[0]+bbox[2])/2,(bbox[1]+bbox[3])/2]
            projection_errors.append(math.dist([px,py],expected))
        if not row[0][0]<row[1][0]<row[2][0]: raise AssertionError("모듈 좌우 순서 오류")
        centers.append([panel["id"],float(row[0][0]),float(row[0][2])])
    if not all(centers[i][2]>centers[i+1][2] for i in range(4)): raise AssertionError("왼쪽 5단 순서 오류")
    if not centers[5][2]>centers[6][2]: raise AssertionError("오른쪽 2단 순서 오류")
    if not all(c[1]<cfg["cabinet"]["seam_x"] for c in centers[:5]) or not all(c[1]>0 for c in centers[5:]): raise AssertionError("좌우 문 분배 오류")
    if max(projection_errors)>1: raise AssertionError(f"카메라 투영 규약 불일치: {max(projection_errors)}")
    for path in ["/World/Cabinet/HMI/Screen","/World/Cabinet/GreenCover","/World/Cabinet/Handle_0/Grip","/World/Workcell/Floor"]:
        if not s.GetPrimAtPath(path): raise AssertionError(f"구조 누락: {path}")
    for prim in s.Traverse():
        if prim.GetTypeName()=="Shader":
            attr=prim.GetAttribute("inputs:file")
            if attr and not attr.Get().resolvedPath: raise AssertionError(f"텍스처 참조 누락: {prim.GetPath()}")
    return {"panel_count":7,"module_count":21,"slot_count":42,"unique_slot_ids":42,"up_axis":"Z","meters_per_unit":1,"module_anchor_projection_max_error_px":max(projection_errors),"projection_note":"수동 배치점의 투영 일관성 검사이며 독립 영상 유사도 지표가 아님","panel_positions":centers}
