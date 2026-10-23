#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""뉴스레이다 교육부판(박종환 기자용) 생성기.

원본(tolibre/news-monitor — 김광일 기자 출입처판)의 파일을 그대로 가져와
'출입처·바이라인·브라우저 저장키·보관 기간' 같은 설정만 바꿔 이 저장소에 쓴다.
(교육판 tolibre/newsradar-labor 생성기와 같은 구조 — 설정 블록만 다르다. 사회정책팀 휴일 특근 묶음은 tools/social_team.py.)

  python tools/make_variant.py <원본 저장소 경로> [<출력 경로, 기본=이 저장소>]

- 치환마다 '원본에서 정확히 몇 번 나와야 하는지'를 적어 두고, 다르면 아무 파일도
  쓰지 않고 멈춘다.
- 원본 쪽 파일은 읽기만 한다. 함수는 바꾸지 않는다(설정·문구만).
"""
import hashlib, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import social_team as ST   # 사회정책팀 휴일 특근 묶음(사회정책팀 저장소 공용 사본)

# ---------------------------------------------------------------- 설정값 ---
REPORTER = "박종환"                       # 노컷 원문 author 메타 'CBS노컷뉴스 박종환 기자'로 가정 — 첫 실행 로그로 확인할 것
BEATS_TITLE = "교육부·교육청"
STORE_PREFIX = "nm-edu-"                  # 브라우저 저장키 — 원본('nm-live-')·재경부('nm-moef-')·국회('nm-asm-')·산업부('nm-ind-')·
                                          # 기후문체('nm-cc-')·복지보건('nm-wel-')·노동('nm-lab-')과 같은 출처라 반드시 달라야 한다
GROUPS = ["교육부", "교육청"]            # 사용자 10/22 "키워드는 교육부, 교육청"
REPORT_ORDER_JS = "[" + ",".join(f"'{g}'" for g in GROUPS) + "]"

NEW_BASE_KEYWORDS = '''BASE_KEYWORDS = [
    # 뉴스레이다 교육부판(tools/make_variant.py가 생성 — 직접 고치지 말 것). 사용자 10/22 "키워드는 교육부, 교육청".
    # '교육청'은 시도교육청 전부(경기도교육청이 DB 제목 최다)를 한 섹션으로 받는다.
    "교육부",
    # 0-76: '교육장관'은 제목 판정 전용(social_team.py NO_SEARCH — 네이버 검색 안 함).
    "교육장관",
    "교육청",
]
'''
NEW_GROUPS_LINE = ("KEYWORD_GROUPS.update(DUTY_KEYWORD_GROUPS)\n"
                   "KEYWORD_GROUPS.update({'교육부': '교육부', '교육장관': '교육부', '교육청': '교육청'})   # 교육판(생성기)\n")

# 교육청 섹션 '다른 지역' 접기(원본 0-69 자리) — 사용자 10/22 "박종환 기자는 서울 경기 위주로 볼 거야. 다른 지역도 보긴 볼 테니 '접기' 기능을 이용해보자."
# 접는 것: ①제목에 다른 시도 이름이 있고 서울·경기가 없는 묶음 ②'교육·학교·학생' 같은 말이 제목에 전혀 없는 묶음(본문에만 '교육청'이 스친 기사).
# 지역 이름이 없는 전국 단위 기사(교육감협의회·전국 교권 조사 등)는 펼쳐 둔다. 처음엔 'keep이 없으면 접기'였는데 이런 기사까지 접혔다.
# '경기'는 '경기 침체'처럼 다른 뜻으로도 걸리지만 펼쳐 두는 쪽이라 놓치지 않는다. 다른 지역을 더 펼치려면 keep에 넣는다(예: r"인천").
_OTHER_REGIONS = ["부산", "대구", "인천", "광주", "대전", "울산", "세종", "강원", "충북", "충남", "충청", "전북", "전남", "전라",
                  "경북", "경남", "경상", "제주", "창원", "포항", "김해", "전주", "청주", "천안", "춘천", "원주", "강릉", "밀양",
                  "목포", "여수", "순천", "진주", "구미", "안동", "익산", "군산", "아산", "서산", "제천", "충주"]
_EDU_WORDS = ["교육", "학교", "학생", "교사", "교원", "교권", "학부모", "입시", "수능", "대학", "급식", "늘봄", "유치원",
              "학원", "교과", "학급", "초등", "중학", "고교", "고등학", "교직", "장학", "진학", "학습", "교실", "돌봄", "통학"]
FOLD_KEEP = {"교육청": {"keep": [r"서울", r"경기", r"정근식", r"임태희"], "fold": _OTHER_REGIONS, "need": _EDU_WORDS,
                        "label": "다른 지역",
                        "desc": "교육청 섹션에서 제목에 다른 시도 이름만 있고 서울·경기(교육감 정근식·임태희 포함)가 없는 묶음, 그리고 제목에 교육 관련 말이 전혀 없는 묶음을 섹션 끝에 접어 둡니다. 지역 이름이 없는 전국 단위 기사는 펼쳐 둡니다. [단독]은 접지 않고, 건수에는 포함합니다."}}

# 기관장 이름 씨앗 — 최교진 장관(2026 재산공개 기사로 확인). 차관은 DB 학습에 맡김. 인사가 바뀌면 고칠 것.
SEED = {"최교진": "교육부"}

# (파일, 찾을 문자열 또는 정규식, 바꿀 문자열, 원본에서 나와야 하는 횟수, 정규식 여부)
NM = "news_monitor.py"
RP = "render_page.py"

REPLACEMENTS = [
    # ---- news_monitor.py: 출입처 ----
    # 0-44·0-67: 휴일 특근 — 원본은 경제정책팀 8곳을 당직으로 모은다. 사회정책팀 판은 그 묶음을 팀 묶음(social_team.py)으로
    # 바꾸고 DUTY_COLLECT는 원본 값(True) 그대로 둔다(사용자 10/22 "세 명을 그룹화해서 휴일 당직 기능을 만들자").
    *ST.replacements(NM, RP, GROUPS, FOLD_KEEP),   # 0-69 교육청 다른 지역 + 0-72 당직 섹션 접기
    # 0-46: 원본의 EXCLUDE_TERMS(대한체육회·스포츠공정위·모의공정위)는 '공정위' 검색어 오탐용이다. 이 판은 '공정위'를
    # 검색하지 않으니 끈다(기후·문체판 0-46과 같음).
    (NM, r"EXCLUDE_TERMS = \[\n(?:.*\n)*?\]\n",
         "EXCLUDE_TERMS = []   # 이 판은 '공정위'를 검색하지 않아 공정위 오탐용 제외어가 필요 없다(생성기, 0-46)\n", 1, True),
    (NM, r"BASE_KEYWORDS = \[\n(?:.*\n)*?\]\n", NEW_BASE_KEYWORDS, 1, True),
    (NM, 'TEMP_KEYWORDS = {\n    "대미투자": "2026-09-23",\n}\n', "TEMP_KEYWORDS = {}\n", 1, False),
    (NM, "KEYWORD_GROUPS.update(DUTY_KEYWORD_GROUPS)\n", NEW_GROUPS_LINE, 1, False),
    # ---- news_monitor.py: 보관 기간 ----
    # 기사량은 첫 실행 전엔 모른다 — 다른 판과 같은 45일로 시작해 실측 뒤 조정.
    (NM, "RETENTION_DAYS = 90 ", "RETENTION_DAYS = 45 ", 1, False),
    # ---- news_monitor.py: 기관장 이름 씨앗(원본 0-38 자리) ----
    (NM, "ACTOR_PEOPLE_SEED = {}\n", f"ACTOR_PEOPLE_SEED = {SEED!r}   # 교육판(생성기)\n", 1, False),
    # ---- news_monitor.py: 바이라인(본인 기사 섹션) ----
    (NM, 'BYLINE_NAME = "김광일"', f'BYLINE_NAME = "{REPORTER}"', 1, False),
    (NM, 'BYLINE_SECTION = "김광일 기자"', f'BYLINE_SECTION = "{REPORTER} 기자"', 1, False),

    # ---- render_page.py: 보고 양식 순서 ----
    (RP, "var REPORT_ORDER = ['방미통위','공정위','과기정통부','우주항공청'];",
         f"var REPORT_ORDER = {REPORT_ORDER_JS};", 2, False),
    (RP, "출입처 순서(방미통위 → 공정위 → 과기정통부 → 우주청 → 2진)",
         "출입처 순서(" + " → ".join(GROUPS) + ")", 2, False),
    # ---- render_page.py: 브라우저 저장키(같은 출처의 다른 페이지와 섞이지 않게) ----
    (RP, "'nm-live-", f"'{STORE_PREFIX}", 6, False),
    # ---- render_page.py: 출입처 식별색(원본 앞 두 출입처 색) ----
    (RP, '[data-g="공정위"], [data-b="공정위"]', '[data-g="교육부"], [data-b="교육부"]', 1, False),
    (RP, '[data-g="과기정통부"], [data-b="과기정통부"]', '[data-g="교육청"], [data-b="교육청"]', 1, False),
    (RP, '[data-g="김광일 기자"], [data-b="김광일 기자"]',
         f'[data-g="{REPORTER} 기자"], [data-b="{REPORTER} 기자"]', 1, False),
    # ---- render_page.py: 기기 연동 숨김(GitHub 계정이 없는 기자는 못 쓴다 — 버튼만 숨김) ----
    (RP, '<button type="button" id="sync" class="sync off"',
         '<button type="button" id="sync" class="sync off" style="display:none"', 1, False),
    # ---- render_page.py: 화면 문구 ----
    (RP, "<title>뉴스레이다</title>", f"<title>뉴스레이다 · {BEATS_TITLE}</title>", 1, False),
    # 0-75: 머리줄 판 주인(사용자 10/23 "이 페이지가 누구의 판인지 각자의 이름을 써주면 좋겠어. 출입처명도 간략히")
    (RP, '<span class="who">김광일<span class="whob"> (과학·방송·경쟁 담당)</span></span>', '<span class="who">박종환<span class="whob"> (교육부·교육청)</span></span>', 1, False),
    (RP, "document.title = '뉴스레이다 · ' + r.title;",
         "document.title = '뉴스레이다(교육) · ' + r.title;", 1, False),
    (RP, "맨 끝 ‘김광일 기자’는", f"맨 끝 ‘{REPORTER} 기자’는", 1, False),
    (RP, "체크한 기사와 ‘여기까지 확인’은 이 기기에 저장되고, 머리줄 <b>기기 연동</b>을 켜면 다른 기기와 맞춰집니다(내 GitHub 비공개 gist). · <a href=\"../\">최신 다이제스트</a> · <a href=\"../archive/\">지난 다이제스트</a></p>",
         "체크한 기사와 ‘여기까지 확인’은 이 기기(브라우저)에만 저장됩니다 — PC와 폰은 따로 기억합니다.</p>", 1, False),
]

# 원본에서 그대로 가져오는 파일(치환 없음)
COPY_AS_IS = ["merge_db.py", "retitle.py"]

# 페이지에 남아 있으면 안 되는 문자열 — 주석(# / //)이 아닌 줄에서만 검사한다.
# (news_monitor.py는 문자열 대신 아래 EXPECT로 '실제로 import했을 때의 값'을 검사한다.
#  원본의 우주항공청·CBS 매핑·소관 어휘는 남아 있어도 검색어가 아니면 무해하다.)
FORBIDDEN = {
    RP: ["nm-live-", "김광일 기자\"", "기기 연동</b>", "방미통위 → 공정위"],
}
# 생성한 news_monitor.py를 별도 프로세스로 import해 확인할 값(당직·임시 키워드가 꺼진 날짜 기준).
EXPECT = {
    "DUTY_ONLY_GROUPS": ST.duty_only(GROUPS),   # 0-67 — 사회정책팀 묶음 중 이 판 섹션이 아닌 것
    "DUTY_COLLECT": True,
    "LIVE_FOLD_KEEP": ST.fold_keep(GROUPS, FOLD_KEEP),
    "LIVE_WEAK_FOLD_GROUPS": list(ST.WEAK_GROUPS),   # 0-68
    "EXCLUDE_TERMS": [],      # 0-46 — 공정위 오탐용 제외어 꺼짐
    "KEYWORDS": ["교육부", "교육장관", "교육청"],
    "GROUP_ORDER": GROUPS,
    "RETENTION_DAYS": 45,
    "BYLINE_NAME": REPORTER,
    "BYLINE_SECTION": f"{REPORTER} 기자",
    "ACTOR_ASSIGN": True,
    "LIVE_ACTOR_BONUS": 2.0,
    "ACTOR_PEOPLE_SEED": SEED,
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(src_dir):
    out = {}
    for fname in {r[0] for r in REPLACEMENTS}:
        with open(os.path.join(src_dir, fname), encoding="utf-8") as f:
            out[fname] = f.read()
    errors = []
    for fname, old, new, count, is_re in REPLACEMENTS:
        text = out[fname]
        found = len(re.findall(old, text)) if is_re else text.count(old)
        if found != count:
            errors.append(f"{fname}: {old[:60]!r} — {count}번이어야 하는데 {found}번")
            continue
        out[fname] = re.sub(old, lambda m: new, text) if is_re else text.replace(old, new)
    if errors:
        raise SystemExit("원본이 예상과 달라 생성을 멈춥니다(아무 파일도 쓰지 않음):\n  "
                         + "\n  ".join(errors))
    leftovers = []
    for fname, pats in FORBIDDEN.items():
        for i, line in enumerate(out[fname].splitlines(), 1):
            s = line.strip()
            if s.startswith("#") or s.startswith("//"):
                continue
            for p in pats:
                if p in line:
                    leftovers.append(f"{fname}:{i}: {p!r} — {s[:80]}")
    if leftovers:
        raise SystemExit("원본 고유 문자열이 남았습니다:\n  " + "\n  ".join(leftovers))
    return out


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    src = os.path.abspath(sys.argv[1])
    dst = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else
                          os.path.join(os.path.dirname(__file__), ".."))
    out = apply(src)
    # 먼저 임시 폴더에 써서 import 검사를 통과한 뒤에만 실제 위치로 옮긴다.
    import json, subprocess, tempfile
    with tempfile.TemporaryDirectory() as tmp:
        for fname, text in out.items():
            with open(os.path.join(tmp, fname), "w", encoding="utf-8") as f:
                f.write(text)
        probe = ("import json, news_monitor as m; print(json.dumps({k: getattr(m, k) for k in %r}, "
                 "ensure_ascii=False))" % list(EXPECT))
        env = dict(os.environ, DUTY_MODE="")
        r = subprocess.run([sys.executable, "-c", probe], cwd=tmp, env=env,
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("생성본 import 실패:\n" + r.stderr[-2000:])
        got = json.loads(r.stdout.strip().splitlines()[-1])
        bad = {k: (got.get(k), v) for k, v in EXPECT.items() if got.get(k) != v}
        if bad:
            raise SystemExit(f"생성본 설정값이 예상과 다릅니다: {bad}")
    for fname, text in sorted(out.items()):
        with open(os.path.join(dst, fname), "w", encoding="utf-8") as f:
            f.write(text)
    for fname in COPY_AS_IS:
        shutil.copyfile(os.path.join(src, fname), os.path.join(dst, fname))
    for fname in sorted(list(out) + COPY_AS_IS):
        with open(os.path.join(src, fname), "rb") as a, open(os.path.join(dst, fname), "rb") as b:
            print(f"{fname:18s} 원본 {md5(a.read())} → 생성 {md5(b.read())}")


if __name__ == "__main__":
    main()
