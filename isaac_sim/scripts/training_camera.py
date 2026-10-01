"""실제 USD 경계에 맞춘 정면 중앙 카메라와 숫자 Mesh 투영 좌표."""
import math
from pxr import Gf, Usd, UsdGeom


def configure(stage, config):
    if config["projection"] != "orthographic":
        raise ValueError("정면 학습 카메라는 orthographic을 사용합니다")
    prim = stage.GetPrimAtPath(config["fit_prim"])
    if not prim: raise ValueError("카메라 대상 Prim 없음")
    box = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_]).ComputeWorldBound(prim).ComputeAlignedRange()
    lo, hi = box.GetMin(), box.GetMax()
    width, height = config["resolution"]
    aspect = width / height
    span_z = max(hi[2] - lo[2], (hi[0] - lo[0]) / aspect) * (1 + 2 * config["margin_fraction"])
    span_x = span_z * aspect
    center = Gf.Vec3d((lo[0]+hi[0])/2, lo[1], (lo[2]+hi[2])/2)
    position = center + Gf.Vec3d(0, -config["distance_m"], 0)
    cam = UsdGeom.Camera.Define(stage, config["path"])
    cam.CreateProjectionAttr(UsdGeom.Tokens.orthographic)
    cam.CreateHorizontalApertureAttr(span_x * 10)
    cam.CreateVerticalApertureAttr(span_z * 10)
    cam.CreateHorizontalApertureOffsetAttr(0)
    cam.CreateVerticalApertureOffsetAttr(0)
    cam.CreateFocalLengthAttr(50)
    cam.CreateFStopAttr(0)
    cam.CreateClippingRangeAttr(Gf.Vec2f(.01, 100))
    UsdGeom.Xformable(cam).MakeMatrixXform().Set(Gf.Matrix4d().SetLookAt(position, center, Gf.Vec3d(0,0,1)).GetInverse())
    return {"path":config["path"],"projection":"orthographic","position":list(position),"target":list(center),
            "span_x":span_x,"span_z":span_z,"resolution":[width,height],"fit_bounds":[list(lo),list(hi)],
            "pixels_per_meter":width/span_x,"horizontal_aperture":span_x*10,"vertical_aperture":span_z*10}


def project(points, camera):
    w,h = camera["resolution"]
    cx,_,cz = camera["target"]
    return [((p[0]-cx)/camera["span_x"]*w+w/2, h/2-(p[2]-cz)/camera["span_z"]*h) for p in points]


def box_from_points(points, camera, padding):
    xy = project(points,camera)
    box=[math.floor(min(p[0] for p in xy))-padding,math.floor(min(p[1] for p in xy))-padding,
         math.ceil(max(p[0] for p in xy))+padding,math.ceil(max(p[1] for p in xy))+padding]
    w,h = camera["resolution"]
    l,t,r,b = box
    if not (0<=l<r<=w and 0<=t<b<=h): raise ValueError(f"숫자 Crop 경계 이탈: {box}")
    return box


def regions(controller, camera, frame, padding):
    from src.generation.glyph_layout import glyph_layout
    xforms = UsdGeom.XformCache()
    values = {r["slot_id"]:r["text"] for r in frame["slots"]}
    result=[]
    for sid,path,width,height,attrs in controller.rows:
        transform=xforms.GetLocalToWorldTransform(controller.stage.GetPrimAtPath(path).GetParent())
        points=[]
        for key,center,unit in glyph_layout(values[sid],width,height):
            matrix=attrs[key].Get()
            if abs(matrix[3][0]-center)>1e-7 or abs(matrix[0][0]-unit)>1e-7:
                raise AssertionError(f"Fabric·정답 불일치: {sid}")
            for p in UsdGeom.Mesh.Get(controller.stage,f"{path}/{key}/Lit").GetPointsAttr().Get():
                points.append(transform.Transform(Gf.Vec3d(center+float(p[0])*unit,float(p[1])*unit,float(p[2])*unit)))
        digit_box=box_from_points(points,camera,0)
        roi=box_from_points([transform.Transform(Gf.Vec3d(x,0,z)) for x in (-width/2,width/2) for z in (-height/2,height/2)],camera,padding)
        result.append({"slot_id":sid,"text":values[sid],"bbox":box_from_points(points,camera,padding),
                       "digit_bbox":digit_box,"slot_roi":roi,"digit_height_px":digit_box[3]-digit_box[1]})
    return result


def panel_regions(stage, camera, scene):
    """버튼/HP 명판을 제외하고 표시기 3개의 실제 Housing 경계를 기록한다."""
    cache=UsdGeom.BBoxCache(Usd.TimeCode.Default(),[UsdGeom.Tokens.default_])
    result=[]
    for panel in scene["panels"]:
        points=[]
        for module in panel["modules"]:
            path=f"/World/Cabinet/Panels/{panel['id']}/{module['id']}/Housing"
            prim=stage.GetPrimAtPath(path)
            if not prim: raise ValueError(f"표시기 Housing 없음: {path}")
            bounds=cache.ComputeWorldBound(prim).ComputeAlignedRange()
            lo,hi=bounds.GetMin(),bounds.GetMax()
            points.extend(Gf.Vec3d(x,lo[1],z) for x in (lo[0],hi[0]) for z in (lo[2],hi[2]))
        result.append({"panel_id":panel["id"],"housing_bbox":box_from_points(points,camera,0)})
    return result
