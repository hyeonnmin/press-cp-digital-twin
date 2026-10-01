"""기존 세그먼트 외형과 같은 오른쪽 정렬·자릿수별 크기 계산."""
def glyph_layout(text, width, height):
    if not text or any(c not in "0123456789." for c in text) or text.count(".") != 1 or len(text.replace(".", "")) > 4:
        raise ValueError("최대 네 숫자와 소수점 한 자리만 지원합니다")
    integer,fraction=text.split(".")
    if not integer or len(fraction)!=1 or width<=0 or height<=0:
        raise ValueError("표시 문자열 또는 크기가 잘못되었습니다")
    units=sum(.24 if c=="." else .68 for c in text)
    unit=min(height,width/units)
    x=width/2-units*unit
    digit_position=4-len(text.replace(".",""))
    result=[]
    for char in text:
        if char==".":
            key="decimal";center=x+.12*unit;x+=.24*unit
        else:
            key=f"digit_{digit_position}_{char}"
            digit_position+=1;center=x+.34*unit;x+=.68*unit
        result.append((key,center,unit))
    return result
