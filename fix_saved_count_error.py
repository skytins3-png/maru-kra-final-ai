# fix_saved_count_error.py
# 사용법:
# 1) 이 파일을 app.py가 있는 폴더에 복사
# 2) 터미널/CMD에서: python fix_saved_count_error.py
# 3) 생성된 app_fixed.py 내용을 확인 후 app.py로 이름 변경/덮어쓰기
#
# 해결 오류:
# NameError: name 'saved_count' is not defined

from pathlib import Path
import re

APP = Path("app.py")
OUT = Path("app_fixed.py")

if not APP.exists():
    raise FileNotFoundError("현재 폴더에 app.py가 없습니다. app.py가 있는 폴더에서 실행하세요.")

text = APP.read_text(encoding="utf-8")

helper = """
# ===== MARU 안정 패치: saved_count 기본값 보강 =====
def _maru_safe_len(obj):
    try:
        return len(obj)
    except Exception:
        return 0

try:
    if "saved_count" not in st.session_state:
        st.session_state["saved_count"] = 0

    # 관찰 저장 데이터가 있으면 그 개수를 우선 사용
    if "observation_records" in st.session_state:
        saved_count = _maru_safe_len(st.session_state.observation_records)
        st.session_state["saved_count"] = saved_count
    else:
        saved_count = int(st.session_state.get("saved_count", 0) or 0)
except Exception:
    saved_count = 0
# ===== /MARU 안정 패치 =====
"""

# 이미 패치되어 있으면 중복 삽입하지 않음
if "MARU 안정 패치: saved_count 기본값 보강" not in text:
    # st.set_page_config(...) 바로 뒤에 삽입
    pattern = r"(st\.set_page_config\([^\n]*\)\s*)"
    if re.search(pattern, text):
        text = re.sub(pattern, r"\1\n" + helper + "\n", text, count=1)
    else:
        # 못 찾으면 파일 맨 위에 삽입
        text = helper + "\n" + text

# 화면 출력 부분에서 saved_count가 혹시 다시 미정의될 경우 방어
text = text.replace(
    '오늘 자동 관찰 저장: <b>{saved_count}건</b><br>',
    '오늘 자동 관찰 저장: <b>{int(st.session_state.get("saved_count", saved_count if "saved_count" in globals() else 0))}건</b><br>'
)

OUT.write_text(text, encoding="utf-8")
print("수정 완료: app_fixed.py 생성됨")
print("GitHub에는 app_fixed.py 내용을 app.py로 덮어쓰기 하세요.")
