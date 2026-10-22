# 뉴스레이다 · 교육부판

CBS노컷뉴스 박종환 기자용 보고 준비 페이지.
원본 [tolibre/news-monitor](https://github.com/tolibre/news-monitor)(김광일 기자 출입처판)에서 설정만 바꿔 만든 판이다.
같은 방식(사회정책팀): 노동판 [newsradar-labor](https://github.com/tolibre/newsradar-labor) · 재경부판 [newsradar-moef](https://github.com/tolibre/newsradar-moef) · 국회판 [newsradar-assembly](https://github.com/tolibre/newsradar-assembly) · 산업부판 [newsradar-industry](https://github.com/tolibre/newsradar-industry) · 기후·문체판 [newsradar-climate-culture](https://github.com/tolibre/newsradar-climate-culture) · 복지·보건판 [newsradar-welfare](https://github.com/tolibre/newsradar-welfare) · 행정판 [newsradar-gov](https://github.com/tolibre/newsradar-gov).

- 페이지: https://tolibre.github.io/newsradar-education/ (→ `/live/`)
- 섹션: 교육부 · 교육청 (+ 맨 끝 박종환 기자 본인 기사, 보고 양식에서 `<기처리>`)
- 보고: 업무일 09:00 · 14:00 (원본과 같은 구간·화면 전환 시각)

## 코드를 직접 고치지 말 것

`news_monitor.py`·`render_page.py`·`merge_db.py`·`retitle.py`는 **`tools/make_variant.py`가 원본에서 생성**한다.

```
git clone --depth 1 https://github.com/tolibre/news-monitor /tmp/nm
python tools/make_variant.py /tmp/nm .
```

## 원본과 다른 점

| | 원본 | 이 판 |
|---|---|---|
| 검색어 | 공정위·방미통위·과기정통부·우주항공청·CBS 등 | 교육부 · 교육청(시도교육청 전부) |
| 그룹 | — | 교육부 · 교육청 |
| 오탐 예방 | — | '교육부터'("교육부터 창업까지")·'고등교육부'(외국 부처)·'교육부문'·'교육부서' — 사회정책팀 공용 `tools/social_team.py` |
| DB 보관 | 90일 | 45일(첫 실행 실측 뒤 조정) |
| 기관장 이름 씨앗 | — | 최교진(장관) |
| 당직(휴일 특근) | 경제정책팀 8곳 | **사회정책팀 묶음**(사회정책팀 다섯 명 — 양형욱·정다운·김동빈·박종환·김민재 — 출입처 합침, `tools/social_team.py`) 중 이 판 섹션이 아닌 것 — '휴일 특근' 스위치로 봄(0-67) |
| 본인 기사 섹션 | 김광일 기자 | 박종환 기자 |
| 브라우저 저장키 | `nm-live-*` | `nm-edu-*` |
| 기기 연동·텔레그램·digest 페이지·수확 | 있음 | 없음(다른 변형판과 같음) |

## 운영 (cron-job.org → workflow_dispatch)

URL `https://api.github.com/repos/tolibre/newsradar-education/actions/workflows/newsradar-education.yml/dispatches`, POST,
헤더는 원본 잡과 같음(PAT `news-monitor-cron`에 이 저장소 추가 필요), 시간대 Asia/Seoul.

| 잡 | 스케줄 | body |
|---|---|---|
| edu-check | `0 * * * *` | `{"ref":"main","inputs":{"mode":"check"}}` |
| edu-precut | `25 8,13 * * 1-5` | 위와 같음 |
| edu-digest | `0 6 * * *` | `{"ref":"main","inputs":{"mode":"digest"}}` |
| edu-retitle | `15 */2 * * *` | `{"ref":"main","inputs":{"mode":"retitle","apply":"1","limit":"100"}}` |

Secrets: `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`(원본과 같은 값). Pages: main / docs.
