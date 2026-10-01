"""외부 사진을 붙이지 않고 명판과 HMI 모식도를 절차적으로 작성한다."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "isaac_sim/assets/cp_panel/textures"
FONT = "C:/Windows/Fonts/malgun.ttf"


def font(size):
    return ImageFont.truetype(FONT, size)


def label(name, text, size=(512, 128), bg=(203, 203, 187), fg=(40, 42, 40), border=True):
    image = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(image)
    if border:
        draw.rectangle((2, 2, size[0]-3, size[1]-3), outline=(150, 152, 141), width=2)
    point_size = int(size[1] * (0.68 / len(text.splitlines())))
    text_font = font(point_size)
    while point_size > 8:
        bounds = draw.multiline_textbbox((0,0), text, font=text_font, spacing=2)
        if bounds[2]-bounds[0] < size[0]*0.92 and bounds[3]-bounds[1] < size[1]*0.88:
            break
        point_size -= 1
        text_font = font(point_size)
    draw.multiline_text((size[0]/2, size[1]/2), text, fill=fg, font=text_font, anchor="mm", align="center", spacing=2)
    image.save(OUTPUT / f"{name}.png")


def generate():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for i in range(1, 8):
        label(f"number_{i}", str(i), (128, 128))
        if i < 7:
            label(f"hp_{i}", f"HP {i}")
    for module in ["temperature", "pressure", "vacuum"]:
        label(module, f"{module.upper()}\nCONTROLLER", (512, 160))
    label("operation", "OPERATION PANEL", (1024, 128))
    label("loader", "로더기", (256, 128))
    label("machine", "SM00055/108521\nHot Press Auto System\nVH2-2034\nKitagawa(Japan)", (512, 320))
    label("cover", "운전 상태 표시", (512, 100), (195, 167, 20))
    label("instrument", "PV                         SV\nRUN  AT  ALM       OUT", (512, 160), (24, 29, 27), (102, 109, 97), False)
    label("keys", "SET     ◀     ▼     ▲", (512, 96), (22, 26, 24), (111, 116, 105), False)

    image = Image.new("RGB", (384, 576), (197, 194, 176))
    d = ImageDraw.Draw(image)
    d.rectangle((0, 0, 383, 575), outline=(111, 25, 24), width=12)
    d.rectangle((15, 15, 368, 72), fill=(132, 38, 37))
    d.text((192, 43), "설비점검 안전절차", font=font(26), fill=(231, 218, 199), anchor="mm")
    rows = ["작업 전 설비 상태 확인", "전원 및 운전 상태 확인", "안전장치 이상 유무 확인", "주변 정리 및 점검", "작업 중 안전수칙 준수", "이상 발생 시 운전 정지", "점검 완료 후 상태 확인", "작업 종료 후 정리"]
    for i, text in enumerate(rows):
        y = 84+i*56
        d.rectangle((20,y,363,y+44), fill=(186,154,52) if i in [2,5] else (207,201,180), outline=(152,90,75), width=2)
        d.text((30,y+12), f"{i+1}. {text}", font=font(18), fill=(77,43,33))
    image.save(OUTPUT / "safety.png")
    image = Image.new("RGB", (384,256), (206,205,188)); d=ImageDraw.Draw(image)
    d.text((192,25), "기계설비 일상점검표", font=font(21), fill=(70,74,70), anchor="mm")
    for y in range(54,240,28): d.line((16,y,368,y),fill=(128,130,119),width=2)
    for x in [16,110,236,368]: d.line((x,54,x,240),fill=(128,130,119),width=2)
    image.save(OUTPUT / "inspection.png")

    image=Image.new("RGB",(1024,768),(25,32,42)); d=ImageDraw.Draw(image)
    d.rounded_rectangle((8,8,1015,759),radius=14,outline=(141,146,160),width=5)
    for x,t,c in [(40,"STOP",(182,145,62)),(620,"MONITOR",(52,162,170)),(758,"ALARM",(193,66,62)),(874,"RESET",(184,108,68))]:
        d.rounded_rectangle((x,30,x+100,67),radius=10,outline=c,width=3)
        d.text((x+50,48),t,font=font(19),fill=c,anchor="mm")
    for x,y,w,h,c in [(65,122,122,160,(89,119,228)),(275,134,194,534,(126,132,226)),(525,123,174,537,(160,76,84)),(745,118,220,539,(98,145,100))]:
        d.rectangle((x,y,x+w,y+h),outline=c,width=4)
    for x,y,t,c in [(65,180,"READY",(78,123,170)),(65,252,"HEAT ON",(64,224,36)),(65,324,"PC OFF",(79,102,132)),(304,121,"HEATER",(228,76,25)),(554,185,"PRESS",(40,122,224)),(554,289,"HOLD",(96,154,212))]:
        d.rectangle((x,y,x+115,y+46),fill=c,outline=(191,200,210),width=2)
        d.text((x+58,y+23),t,font=font(20),fill=(217,223,230),anchor="mm")
    for y in [236,334,440,552,614]:
        d.rectangle((314,y,432,y+43),outline=(198,199,215),width=2)
        d.line((373,y-36,373,y),fill=(182,148,203),width=3)
    for i,t in enumerate(["MACHINE READY","AUTO MODE","HEATING","PRESSURE","VACUUM","LOADER READY","CYCLE END"]):
        y=175+i*57; d.rectangle((766,y,783,y+17),fill=(190,102,204)); d.text((798,y),t,font=font(16),fill=(174,197,202))
    d.ellipse((77,424,150,497),fill=(64,224,36),outline=(192,201,218),width=4)
    d.text((512,727),"OPERATION / MONITOR",font=font(20),fill=(151,167,176),anchor="mm")
    image.save(OUTPUT / "hmi.png")
    return sorted(OUTPUT.glob("*.png"))


if __name__ == "__main__":
    generate()
