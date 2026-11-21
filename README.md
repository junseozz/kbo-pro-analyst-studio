# KBO Pro Analyst Studio — 자동 연동 데이터

KBO 분석 스튜디오 앱(**v21.1 이상**)이 열릴 때 스스로 읽어 반영하는 데이터입니다.
앱은 45MB HTML 을 다시 받지 않아도 이 저장소의 최신 값으로 자기 데이터를 갱신합니다.

## 1. 전체 데이터 청크 (`data/manifest.json`)

앱은 **맨 먼저 `manifest.json`(약 3KB)만** 읽고, sha256 이 바뀐 청크만 내려받습니다.
변동이 없으면 청크 다운로드는 0바이트입니다.

| 청크 | 담긴 데이터 | 크기 |
|---|---|---|
| `data/core.json` | `KBO_DATA` 에서 경기 두 묶음만 뺀 전부 — meta · 1군/퓨처스 순위표 · 팀 스탯 · 타자·투수 기록 · 파크팩터 · 2027 FA · 옵트아웃 · 리그 평균 · 포지션 평균 | 3.99MB |
| `data/extra.json` | `V193_ENTRY_DATA`(등·말소 엔트리) · `V164_NEWS_SNAPSHOT`(뉴스) · `V158_INTL_DATA`(국제대회) · `V177_PRACTICE_RESULT`(연습경기) | 0.84MB |
| `data/zone_pitch.json` | `V167_ZONE_DATA`(핫콜드존·3개년 ABS존) · `V168_ZONE_PCT`(존 비율) · `V162_PITCH_DATA`(구종) | 2.28MB |
| `data/season.json` | `V159_YEARS`(3개년) · `V151_SITUATION`(상황별) · `V151_FALL` · `V193_PITCH_PARK` · `V190_STADIUM` · `V190_EXHIBIT` · `V165_SAVANT` · `V165_TOURS` · `V166_DEF` · `V166_BALK` · `V176_HEIGHTS` · `V192_PROF` · `V192_NUMS` · `V167_INTL_NAMES` · `V176_PRACTICE_MEDIA` | 8.92MB |
| `data/kbo1_games.json` | `KBO_DATA.kbo1_games` — 1군 박스스코어 전 경기(869) | 6.55MB |
| `data/futures_games.json` | `KBO_DATA.futures_games` — 퓨처스 박스스코어 전 경기(756) | 4.54MB |

- 각 청크는 **`<id>.json`(정본)** 과 **`<id>.js`(같은 바이트를 `window.V211_RECEIVE(...)` 로 감싼 사본)** 두 형태로 올라갑니다.
  · `.json` — `raw.githubusercontent.com` (fetch, CORS `*`)
  · `.js` — `raw.githack.com` · `cdn.jsdelivr.net` (앱을 `file://` 로 열어 fetch 가 막힐 때 script 로더용)
- 앱은 받은 값을 **제자리(in-place)로 덮어씁니다**. `const KBO_DATA` 처럼 재할당이 안 되는 참조도 그대로 살아 있고,
  배열은 길이를 0으로 만든 뒤 채우고 객체는 키 단위로 덮습니다. 앱의 함수·계산식·UI는 건드리지 않습니다.
- 앱은 청크를 `IndexedDB('v211_kbo_cache')` 에 저장합니다. 다음에 열 때는 manifest 확인 전에 저장본으로 먼저 켜지므로
  오프라인·비행기모드에서도 마지막 최신 데이터로 동작합니다.

`manifest.json` 형식:

```json
{
  "schema_version": 2, "app_version": "v21.1",
  "updated_at": "2026-11-21T10:26:41+09:00", "data_through": "2026-11-21",
  "chunks": [
    { "id": "core", "path": "data/core.json", "js": "data/core.js",
      "sha256": "34f9752a…", "bytes": 3990220, "updated_at": "2026-11-21T10:26:41+09:00",
      "globals": ["KBO_DATA"], "about": "…" }
  ],
  "live_patch": { "id": "live_patch", "sha256": "…", "bytes": 4536 },
  "total_bytes": 27113853
}
```

## 2. 증분 패치 (`data/live_patch.json`)

전체 청크(27MB)를 다시 올리지 않고 소식만 빨리 반영할 때 씁니다. 청크 반영 **뒤에** 적용되므로
`player_patches` 의 소속·등번호가 전체 데이터 교체에 지워지지 않습니다.

- `data/live_patch.json` — 본문(JSON). 앱은 `raw.githubusercontent.com` 에서 직접 읽습니다.
- `data/live_patch.js` — 같은 내용을 `window.V210_RECEIVE(...)` 로 감싼 사본(file:// 대체 로더용).

```json
{
  "schema_version": 1,
  "app_version": "v21.1",
  "updated_at": "2026-11-21T09:45:00+09:00",
  "data_through": "2026-11-21",
  "player_patches": [
    { "pid": "68242", "name": "정철원", "league": "KBO1",
      "team": "키움", "status": "트레이드", "number": "",
      "prev_team": "롯데", "move_date": "2026-11-20", "move_note": "…" }
  ],
  "notices": [
    { "date": "2026-11-20", "team": "롯데↔키움", "type": "트레이드",
      "player": "[오피셜] 정철원 ↔ 임지열 1대1 트레이드", "detail": "…", "src": "…" }
  ],
  "games": [
    { "pool": "practice", "id": "practice_20261121_LOTDOO", "add": true,
      "data": { "date": "11.21(토)", "date_iso": "20261121", "time": "13:00",
                "away": "롯데", "home": "두산", "as": 4, "hs": 7, "status": "종료" } }
  ],
  "ai_facts": [
    { "id": "fa2027-yang", "date": "2026-11-17", "keywords": ["양의지"],
      "label": "2027 FA 계약", "text": "두산 잔류 · 2년 최대 55억", "src": "두산 보도자료" }
  ]
}
```

- `player_patches` 는 `pid` 단독 매칭입니다. 같은 `pid` 가 1군·퓨처스에 함께 있으면 `league`(`KBO1`/`FUTURES`)로 구분합니다.
  `career[]`(과거 시즌 소속)는 건드리지 않으므로 2026 시즌 소속 기준 팀 집계(v20.8)는 그대로 유지됩니다.
- `number` 규칙: 값이 있으면 그 번호로 배정 / `"-"` 는 **'미정'으로 비움** / `""` 또는 항목 없음은 **손대지 않음**
  (앱이 실행 중에 채우는 등번호를 빈 값으로 지우지 않기 위해서).
- `notices` 는 `date`+`player` 로 중복을 막습니다.
- `games` 의 `pool` 은 `kbo1` · `futures` · `practice` · `intl` 이고, `id` 가 있으면 그 경기를 갱신, 없으면 `add:true` 일 때 추가합니다.

## 3. 갱신 규칙

1. 확인된 공식 발표만 적습니다(추정·가상 값 금지).
2. `updated_at` 을 반드시 갱신합니다.
3. 전체 데이터를 바꿀 때는 해당 청크 파일과 `manifest.json` 의 `sha256`·`bytes`·`updated_at` 을 함께 바꿉니다.
   (`<id>.json` 과 `<id>.js` 는 **같은 내용**이어야 합니다.)
4. 앱 반영 시점: 앱을 열 때 · 앱으로 돌아올 때(25초 경과) · 60초마다(국제대회 진행 중 20초) · 알림판 `지금 갱신` 버튼(이때는 GitHub API 로 manifest 를 확인해 CDN 캐시를 건너뛴다).
5. **청크를 바꾼 뒤에는 반드시 `python3 tools/verify_manifest.py` 로 무결성을 확인한다.** 이 검사가 `manifest.json` 의 sha256·bytes 와 실제 파일, `.js` 래퍼, `manifest.js` 가 어긋난 것을 잡아낸다(`--fix` 로 실제 파일 기준 재작성).
   → 2026-11-21 사고: `tools/update_news.py` 가 청크를 `name` 으로 찾아(실제 키는 `id`) `extra` 의 sha256 을 갱신하지 못했고, manifest 는 옛 해시를 계속 선언해 앱이 "변동 없음"으로 판단, 새 뉴스가 하루 종일 전달되지 않았다.
6. **2026 KBO 기록이 없는 신규 영입 선수**는 `core.json` 의 해당 풀(`kbo1_hitters`/`kbo1_pitchers`)에 `g:0`·기록 `null`·`no_num:1`·`new2027:1` 로 넣고, `season.json` 의 `V192_PROF` 에 공식 프로필을 함께 넣습니다(`num` 은 미정이면 `""`).
   · `new2027` 은 앱(v21.4+)이 **팀 로스터에만** 표시하고 2026 성적·WAR 집계·세이버 표(0경기 제외)·순위에는 넣지 않는다는 표시입니다. 프로필은 세이버 백분위 대신 공식 정보+0경기 안내만 그립니다.
   · 첫 사례: 후쿠타니 코지(키움 아시아쿼터, 2026-11-19 영입) — `id` 는 KBO 공식 id 미공시라 앱 내부 식별자 `FK19911` 을 씁니다.
   · **청크를 다시 만들 때 이 항목을 지우지 마세요.** `core.json` 은 앱 HTML 의 `KBO_DATA` 사본이라, HTML 에서 재추출하면 수동 추가분이 사라집니다.

## 4. 반영 결과 표시

알림판(`🔔`) 카드의 상태 줄:

- `전체 데이터 연동 완료 · 11.21 10:26 · 청크 6/6 · +25.9MB · v21.1`
- `오프라인 — 저장본/내장으로 동작 · 저장본 6청크 · 11.21 10:26 · v21.1`
- `일부 청크 실패 — 저장본으로 동작 · 청크 5/6 · v21.1`
